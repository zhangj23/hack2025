"""
Gymnasium Environment for SimICU
This wraps the core simulation engine in a Gymnasium-compatible interface
for reinforcement learning.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from sim_icu_logic import SimICU, PatientStatus


class SimICUEnv(gym.Env):
    """
    Gymnasium environment for SimICU reinforcement learning.
    
    The AI agent learns to manage ICU resources by assigning patients to beds
    and ventilators to maximize patient survival.
    """
    
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 4}
    
    def __init__(self, max_patients: int = 10, max_ticks: int = 300, render_mode=None):
        super(SimICUEnv, self).__init__()
        
        self.max_patients = max_patients
        self.max_ticks = max_ticks
        self.render_mode = render_mode
        
        # Initialize the core simulation engine
        self.game = SimICU()
        
        # Define action space
        # Action: [patient_id, action_type]
        # patient_id: 0 to max_patients-1 (which patient to act on)
        # action_type: 0 = assign bed, 1 = assign ventilator, 2 = do nothing
        self.action_space = spaces.MultiDiscrete([max_patients, 3])
        
        # Define observation space (state space)
        # For each patient: [severity, time_waiting, status_encoded]
        # Plus: [free_beds, free_nurses, free_vents, tick]
        # Status encoding: 0=waiting, 1=in_bed, 2=on_ventilator, 3=cured, 4=lost
        state_size = (max_patients * 3) + 4
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
            PatientStatus.CURED: 3.0,
            PatientStatus.LOST: 4.0
        }
        return status_map.get(status, 0.0)
    
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
                state[i * 3] = float(patient.severity) / 100.0  # Max severity is 100
                state[i * 3 + 1] = float(patient.time_waiting) / self.max_ticks  # Max time is max_ticks
                state[i * 3 + 2] = self._encode_status(patient.status) / 4.0  # Max status code is 4
            else:
                # No patient in this slot - use default values
                state[i * 3] = 0.0  # severity
                state[i * 3 + 1] = 0.0  # time_waiting
                state[i * 3 + 2] = 1.0  # status = lost (invalid slot, normalized to 1.0)
        
        # Normalize resource counts and tick
        state[-4] = float(self.game.free_beds) / max_beds if max_beds > 0 else 0.0
        state[-3] = float(self.game.free_nurses) / max_nurses if max_nurses > 0 else 0.0
        state[-2] = float(self.game.free_vents) / max_vents if max_vents > 0 else 0.0
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
        patient_id, action_type = action
        
        # --- 1. VALIDATION & PENALTIES (DO NOT EARLY-RETURN) ---
        step_penalty = 0.0

        valid_patient = None
        if patient_id < len(self.game.patients):
            candidate = self.game.patients[patient_id]
            if candidate.status not in [PatientStatus.CURED, PatientStatus.LOST]:
                valid_patient = candidate
            else:
                step_penalty -= 5.0  # acting on finished patient
        else:
            step_penalty -= 5.0  # acting on non-existent patient

        # Resource availability checks
        resource_available = True
        if action_type == 0 and self.game.free_beds == 0:
            step_penalty -= 2.0
            resource_available = False
        elif action_type == 1 and self.game.free_vents == 0:
            step_penalty -= 2.0
            resource_available = False

        # --- 2. APPLY ACTION IF VALID ---
        action_applied = False
        if valid_patient and resource_available:
            actual_patient_id = valid_patient.id
            action_applied = bool(self.game.perform_action(actual_patient_id, action_type))

        # Track severity before update (for shaping reward)
        prev_total_severity = sum(p.severity for p in self.game.patients)

        # Always advance time so the sim progresses even after invalid actions
        self.game.update_tick()
        
        # Get new state (which is now normalized)
        new_state = self._get_state()
        
        # Calculate shaping reward
        reward = self._calculate_reward() + step_penalty

        # Reward reduction in total severity across all patients
        new_total_severity = sum(p.severity for p in self.game.patients)
        delta_severity = prev_total_severity - new_total_severity
        reward += 0.2 * delta_severity  # positive if severity decreased

        # Bonus for successful resource assignments (encourage acting)
        if action_applied:
            if action_type == 0:  # bed
                reward += 1.0
            elif action_type == 1:  # ventilator
                reward += 3.0

        # Penalty for idling when there is work to do (waiting patients and free resources)
        if action_type == 2:
            if self.game.total_waiting_patients > 0 and (self.game.free_beds > 0 or self.game.free_vents > 0):
                reward -= 0.5
        
        # Check if episode is done
        terminated = self.game.is_game_over(self.max_ticks)
        truncated = False
        
        # Info dict
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
            reward -= 150.0  # slightly stronger penalty to discourage losses

        # Dense shaping rewards per step
        waiting = self.game.total_waiting_patients
        in_bed = len([p for p in self.game.patients if p.status == PatientStatus.IN_BED])
        on_vent = len([p for p in self.game.patients if p.status == PatientStatus.ON_VENTILATOR])

        # Encourage active treatment
        reward += 1.0 * in_bed
        reward += 2.0 * on_vent

        # Mild penalty for waiting
        reward -= 0.05 * waiting

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
