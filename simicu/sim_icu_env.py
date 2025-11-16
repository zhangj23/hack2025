"""
Gymnasium Environment for SimICU
This wraps the core simulation engine in a Gymnasium-compatible interface
for reinforcement learning.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from sim_icu_logic import SimICU, PatientStatus, PatientType


class SimICUEnv(gym.Env):
    """
    Gymnasium environment for SimICU reinforcement learning.
    
    The AI agent learns to manage ICU resources by assigning patients to beds
    and ventilators to maximize patient survival.
    """
    
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}
    
    def __init__(self, max_patients: int = 10, max_ticks: int = 300, render_mode=None, arrival_rate: float | None = None, num_nurses: int | None = None, num_beds: int | None = None, num_ventilators: int | None = None):
        super(SimICUEnv, self).__init__()
        
        self.max_patients = max_patients
        self.max_ticks = max_ticks
        self.render_mode = render_mode
        
        # Initialize the core simulation engine
        self.game = SimICU(
            num_nurses=num_nurses if num_nurses is not None else 6,
            num_beds=num_beds if num_beds is not None else 10,
            num_ventilators=num_ventilators if num_ventilators is not None else 3,
            arrival_rate=arrival_rate if arrival_rate is not None else 0.10
        )

        # Pending assignment parity: simulate travel delay before setup starts
        self._pending_patient_id: int | None = None
        self._pending_action_type: int | None = None  # 0=bed,1=vent
        self._pending_travel_ticks: int = 0
        
        # Define action space
        # Action: [patient_id, action_type]
        # patient_id: 0 to max_patients-1 (which patient to act on)
        # action_type: 0 = assign bed, 1 = assign ventilator, 2 = do nothing
        self.action_space = spaces.MultiDiscrete([max_patients, 3])
        
        # Define observation space (state space)
        # For each patient: [severity, time_waiting, status_encoded, type_encoded]
        # Plus: [free_beds, free_nurses, free_vents, free_step_down, tick]
        # Status encoding: 0=waiting, 1=in_bed, 2=on_ventilator, 3=cured, 4=lost
        state_size = (max_patients * 4) + 5
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,  # <-- CRITICAL: Change from 1000.0 to 1.0
            shape=(state_size,),
            dtype=np.float32
        )
    
    def _encode_status(self, status: PatientStatus) -> float:
        """Encode patient status as a number"""
        status_map = {
            PatientStatus.WAITING: 0.0,
            PatientStatus.IN_BED: 1.0,
            PatientStatus.ON_VENTILATOR: 2.0,
            PatientStatus.PENDING_DISCHARGE: 3.0,
            PatientStatus.CURED: 3.0,
            PatientStatus.LOST: 4.0
        }
        return status_map.get(status, 0.0)
    
    def _encode_type(self, t: PatientType) -> float:
        type_map = {
            PatientType.RESPIRATORY: 0.0,
            PatientType.CARDIAC: 0.5,
            PatientType.TRAUMA: 1.0,
        }
        return type_map.get(t, 0.0)

    def _get_state(self) -> np.ndarray:
        """
        Build the state array from the current game state.
        This is what the AI "sees" about the environment.
        All values are normalized to [0, 1] range.
        """
        state = np.zeros(self.observation_space.shape, dtype=np.float32)
        
        # Get max values for normalization
        max_beds = self.game.num_beds
        max_nurses = self.game.num_nurses
        max_vents = self.game.num_ventilators
        
        # Get all patients (active and inactive)
        all_patients = self.game.patients[:self.max_patients]
        
        # Pad with zeros if we have fewer patients than max_patients
        for i in range(self.max_patients):
            if i < len(all_patients):
                patient = all_patients[i]
                # Normalize patient data to [0, 1]
                base = i * 4
                state[base] = float(patient.severity) / 100.0  # Max severity is 100
                state[base + 1] = float(patient.time_waiting) / self.max_ticks  # Max time is max_ticks
                state[base + 2] = self._encode_status(patient.status) / 4.0  # Max status code is 4
                state[base + 3] = self._encode_type(patient.patient_type)  # [0,1]
            else:
                # No patient in this slot - use default values
                base = i * 4
                state[base] = 0.0  # severity
                state[base + 1] = 0.0  # time_waiting
                state[base + 2] = 1.0  # status = lost (invalid slot, normalized to 1.0)
                state[base + 3] = 0.0  # type
        
        # Normalize resource counts and tick
        state[-5] = float(self.game.free_beds) / max_beds if max_beds > 0 else 0.0
        state[-4] = float(self.game.free_nurses) / max_nurses if max_nurses > 0 else 0.0
        state[-3] = float(self.game.free_vents) / max_vents if max_vents > 0 else 0.0
        # Step-down beds (normalized)
        max_step = getattr(self.game, "num_step_down_beds", 1) or 1
        free_step = getattr(self.game, "_free_step_down_beds", 0)
        state[-2] = float(free_step) / float(max_step)
        state[-1] = float(self.game.tick) / self.max_ticks
        
        return state
    
    def reset(self, seed=None, options=None):
        """Reset the environment to initial state"""
        super().reset(seed=seed)
        
        if seed is not None:
            np.random.seed(seed)
        
        self.game.reset()
        
        # Run a few ticks to get some initial patients
        for _ in range(5):
            self.game.update_tick()
        
        initial_state = self._get_state()
        info = {}
        
        return initial_state, info
    
    def step(self, action):
        patient_slot_id, action_type = action

        step_penalty = 0.0

        # 1) Validate action
        if patient_slot_id >= len(self.game.patients):
            step_penalty = -5.0
            patient = None
        else:
            patient = self.game.patients[patient_slot_id]

        if patient and patient.status in [PatientStatus.CURED, PatientStatus.LOST, PatientStatus.PENDING_DISCHARGE]:
            step_penalty = -5.0
            patient = None

        if patient and action_type == 0:
            if self.game.free_beds == 0 or self.game.free_nurses == 0:
                step_penalty = -2.0
                patient = None
        elif patient and action_type == 1:
            if self.game.free_vents == 0 or self.game.free_nurses < 2:
                step_penalty = -2.0
                patient = None

        # Severity before
        prev_total_severity = sum(p.severity for p in self.game.patients if p.status not in [PatientStatus.CURED, PatientStatus.LOST])

        # 2) Apply immediately
        if patient and action_type != 2:
            self.game.perform_action(patient.id, action_type)

        # 3) Advance game
        self.game.update_tick()

        # 4) New state and reward
        new_state = self._get_state()
        new_total_severity = sum(p.severity for p in self.game.patients if p.status not in [PatientStatus.CURED, PatientStatus.LOST])

        reward = self._calculate_reward() + step_penalty
        delta_severity = new_total_severity - prev_total_severity
        reward += 0.1 * delta_severity

        if self.game.just_incurred_setup_delay:
            reward -= 5.0

        if action_type == 2:
            if self.game.total_waiting_patients > 0 and self.game.free_nurses > 0:
                reward -= 0.5

        terminated = self.game.is_game_over(self.max_ticks)
        truncated = False
        info = {
            'patients_saved': self.game.patients_saved,
            'patients_lost': self.game.patients_lost,
            'score': self.game.get_score()
        }

        return new_state, reward, terminated, truncated, info
    
    def _calculate_reward(self) -> float:
        """
        Calculate reward for the current step.
        This is "reward engineering" - critical for RL success.
        """
        reward = 0.0

        # Large sparse rewards for terminal outcomes
        if self.game.just_saved_a_patient:
            reward += 100.0
        if self.game.just_lost_a_patient:
            reward -= 100.0

        # Dense shaping rewards per step (tuned)
        waiting = self.game.total_waiting_patients
        # Count treated patients only when setup is done and a nurse is attending
        treated = 0
        waiting_patients = []
        for p in self.game.patients:
            if p.status == PatientStatus.IN_BED and getattr(p, 'bed_setup_ticks', 0) <= 0 and getattr(p, 'assigned_nurse', None) is not None:
                treated += 1
            elif p.status == PatientStatus.ON_VENTILATOR and getattr(p, 'vent_setup_ticks', 0) <= 0 and getattr(p, 'assigned_nurse', None) is not None:
                treated += 1
            elif p.status == PatientStatus.WAITING:
                waiting_patients.append(p)
        pending = len([p for p in self.game.patients if p.status == PatientStatus.PENDING_DISCHARGE])

        # Encourage treatment
        reward += 0.8 * treated

        # Stronger penalty for patients waiting: count and aggregate severity
        reward -= 0.15 * waiting
        sum_waiting_severity = sum(p.severity for p in waiting_patients)
        reward -= 0.01 * sum_waiting_severity

        # ICU gridlock penalties (non-linear)
        reward -= 0.1 * pending
        reward -= 0.05 * (pending * pending)

        # Archetype-aware treatment shaping
        for p in self.game.patients:
            if p.status == PatientStatus.ON_VENTILATOR and getattr(p, 'vent_setup_ticks', 0) <= 0 and getattr(p, 'assigned_nurse', None) is not None:
                if getattr(p, 'patient_type', None) == PatientType.RESPIRATORY:
                    reward += 0.3
                else:
                    reward -= 0.3
            if p.status == PatientStatus.IN_BED and getattr(p, 'bed_setup_ticks', 0) <= 0 and getattr(p, 'assigned_nurse', None) is not None:
                if getattr(p, 'patient_type', None) == PatientType.CARDIAC:
                    reward += 0.2

        # Opportunity cost: nurses bound to ongoing treatments reduce flexibility
        nurses_in_use = self.game.num_nurses - self.game.free_nurses
        reward -= 0.2 * nurses_in_use

        return reward
    
    def render(self):
      """Render the environment (optional, for visualization)"""
      if self.render_mode == "human":
         # For now, just print state
         score = self.game.get_score()
         print(f"Tick: {self.game.tick} | Saved: {score['patients_saved']} | "
               f"Lost: {score['patients_lost']} | Waiting: {self.game.total_waiting_patients}")
      
      # You can add rgb_array support later if you want video
      elif self.render_mode == "rgb_array":
         # (This is where you would use pygame to return a pixel array)
         return np.zeros((100, 100, 3), dtype=np.uint8)
      
      return None
