"""
Core Simulation Engine for SimICU
This is the shared backend logic that both the player and AI interact with.
"""

import numpy as np
from enum import Enum
from typing import List, Optional
import random


class PatientStatus(Enum):
    """Patient status states"""
    WAITING = "waiting"
    IN_BED = "in_bed"
    ON_VENTILATOR = "on_ventilator"
    CURED = "cured"
    LOST = "lost"


class Patient:
    """Represents a patient in the ICU simulation"""
    
    def __init__(self, patient_id: int, initial_severity: int = 50):
        self.id = patient_id
        # Interpret 'severity' as LIFE from 0..100 where:
        #   0  = death, 100 = full recovery.
        # Patients lose life while waiting and gain life when treated.
        self.severity = float(initial_severity)
        self.status = PatientStatus.WAITING
        self.time_waiting = 0
        self.assigned_nurse = None
        self.assigned_bed = None
        self.assigned_ventilator = None
        # Setup times: when (re)assigned, treatment is delayed during setup
        self.bed_setup_ticks = 0
        self.vent_setup_ticks = 0
        
    def update(self):
        """Update patient state each tick"""
        if self.status == PatientStatus.WAITING:
            self.time_waiting += 1
            # Lose life while waiting (slow deterioration)
            # Slight acceleration with longer wait
            extra = (self.time_waiting // 20) * 0.1
            self.severity = max(0.0, self.severity - (0.5 + extra))
            
        elif self.status == PatientStatus.IN_BED:
            # Gain life with bed + nurse care (slower, steady)
            if self.bed_setup_ticks > 0:
                self.bed_setup_ticks -= 1
            else:
                self.severity = min(100.0, self.severity + 1.5)
            
        elif self.status == PatientStatus.ON_VENTILATOR:
            # Gain life faster with ventilator
            if self.vent_setup_ticks > 0:
                self.vent_setup_ticks -= 1
            else:
                self.severity = min(100.0, self.severity + 3.0)
        
        # Check for state transitions
        if self.severity >= 100.0 and self.status != PatientStatus.CURED:
            self.status = PatientStatus.CURED
            self._release_resources()
        elif self.severity <= 0.0 and self.status != PatientStatus.LOST:
            self.status = PatientStatus.LOST
            self._release_resources()
    
    def _release_resources(self):
        """Release all assigned resources"""
        if self.assigned_nurse:
            self.assigned_nurse.available = True
            self.assigned_nurse = None
        if self.assigned_bed:
            self.assigned_bed.available = True
            self.assigned_bed = None
        if self.assigned_ventilator:
            self.assigned_ventilator.available = True
            self.assigned_ventilator = None


class Nurse:
    """Represents a nurse resource"""
    def __init__(self, nurse_id: int):
        self.id = nurse_id
        self.available = True


class Bed:
    """Represents a bed resource"""
    def __init__(self, bed_id: int):
        self.id = bed_id
        self.available = True


class Ventilator:
    """Represents a ventilator resource"""
    def __init__(self, ventilator_id: int):
        self.id = ventilator_id
        self.available = True


class SimICU:
    """Core ICU simulation engine"""
    
    def __init__(self, num_nurses: int = 6, num_beds: int = 10, num_ventilators: int = 4, max_patients_on_arrival=3, arrival_rate=0.10):
        self.num_nurses = num_nurses
        self.num_beds = num_beds
        self.num_ventilators = num_ventilators
        
        # Initialize resources
        self.nurses = [Nurse(i) for i in range(num_nurses)]
        self.beds = [Bed(i) for i in range(num_beds)]
        self.ventilators = [Ventilator(i) for i in range(num_ventilators)]
        
        # Patient management
        self.patients: List[Patient] = []
        self.next_patient_id = 0
        
        # Game state
        self.tick = 0
        self.patients_saved = 0
        self.patients_lost = 0
        self.total_wait_time = 0
        
        # Patient arrival parameters (Poisson distribution)
        self.max_patients_on_arrival = max_patients_on_arrival
        self.arrival_rate = arrival_rate
        self.next_arrival = self._generate_next_arrival()
        
        # Track state changes for reward calculation
        self.just_saved_a_patient = False
        self.just_lost_a_patient = False
        self.just_incurred_setup_delay = False
        
        # Initialize private resource counters
        self._free_beds = num_beds
        self._free_nurses = num_nurses
        self._free_vents = num_ventilators
        
        self.reset()
         
    def _generate_next_arrival(self) -> int:
        """Generate next patient arrival time using Poisson distribution"""
        return int(np.random.exponential(1.0 / self.arrival_rate))
    
    def reset(self):
        """Reset the simulation to initial state"""
        self.patients = []
        self.next_patient_id = 0
        self.tick = 0
        self.patients_saved = 0
        self.patients_lost = 0
        self.total_wait_time = 0
        self.next_arrival = self._generate_next_arrival()
        
        # Reset private resource counters
        self._free_beds = self.num_beds
        self._free_nurses = self.num_nurses
        self._free_vents = self.num_ventilators

        # Reset resources
        for nurse in self.nurses:
            nurse.available = True
        for bed in self.beds:
            bed.available = True
        for ventilator in self.ventilators:
            ventilator.available = True
    
    def add_patient(self, initial_severity: Optional[int] = None) -> Patient:
        """Add a new patient to the simulation"""
        if initial_severity is None:
            initial_severity = random.randint(40, 60)
        
        patient = Patient(self.next_patient_id, initial_severity)
        self.next_patient_id += 1
        self.patients.append(patient)
        return patient
    
    def get_available_nurse(self) -> Optional[Nurse]:
        """Get an available nurse"""
        for nurse in self.nurses:
            if nurse.available:
                return nurse
        return None
    
    def get_available_bed(self) -> Optional[Bed]:
        """Get an available bed"""
        for bed in self.beds:
            if bed.available:
                return bed
        return None
    
    def get_available_ventilator(self) -> Optional[Ventilator]:
        """Get an available ventilator"""
        for ventilator in self.ventilators:
            if ventilator.available:
                return ventilator
        return None
    
    def assign_patient_to_bed(self, patient: Patient) -> bool:
        """Assign a patient to a bed with a nurse"""
        if patient.status != PatientStatus.WAITING:
            return False
        
        # Check if resources are available using counters
        if self._free_beds <= 0 or self._free_nurses <= 0:
            return False
        
        bed = self.get_available_bed()
        nurse = self.get_available_nurse()
        
        if bed and nurse:
            patient.assigned_bed = bed
            patient.assigned_nurse = nurse
            bed.available = False
            nurse.available = False
            patient.status = PatientStatus.IN_BED
            # Setup delay before treatment starts
            patient.bed_setup_ticks = 3
            # Decrement counters
            self._free_beds -= 1
            self._free_nurses -= 1
            return True
        return False
    
    def assign_patient_to_specific_bed(self, patient: Patient, bed: Bed, nurse: Optional[Nurse] = None) -> bool:
        """
        Assign the given patient to a specific bed (and nurse).
        This is used by the UI when the player clicks a particular bed.
        """
        if patient.status != PatientStatus.WAITING:
            return False
        if bed is None or not bed.available:
            return False
        if self._free_beds <= 0 or self._free_nurses <= 0:
            return False

        # Choose a nurse if not explicitly provided
        chosen_nurse = nurse if nurse is not None else self.get_available_nurse()
        if chosen_nurse is None or not chosen_nurse.available:
            return False

        # Perform assignment
        patient.assigned_bed = bed
        patient.assigned_nurse = chosen_nurse
        bed.available = False
        chosen_nurse.available = False
        patient.status = PatientStatus.IN_BED
        patient.bed_setup_ticks = 3
        # Decrement counters
        self._free_beds -= 1
        self._free_nurses -= 1
        return True
    
    def assign_patient_to_ventilator(self, patient: Patient) -> bool:
        """Assign a patient to a ventilator (requires bed + nurse + ventilator)"""
        if patient.status != PatientStatus.WAITING and patient.status != PatientStatus.IN_BED:
            return False
        
        # Check if ventilator is available using counter
        if self._free_vents <= 0:
            return False
        
        ventilator = self.get_available_ventilator()
        
        if ventilator:
            # If not already in bed, assign bed and nurse first
            if patient.status == PatientStatus.WAITING:
                if not self.assign_patient_to_bed(patient):
                    return False
            
            patient.assigned_ventilator = ventilator
            ventilator.available = False
            patient.status = PatientStatus.ON_VENTILATOR
            # Setup delay before ventilator effect starts
            patient.vent_setup_ticks = 5
            # Decrement ventilator counter
            self._free_vents -= 1
            return True
        return False
    
    def perform_action(self, patient_id: int, action_type: int):
        """
        Perform an action on a patient
        action_type: 0 = assign to bed, 1 = assign to ventilator, 2 = do nothing
        """
        # Find patient by ID
        patient = None
        for p in self.patients:
            if p.id == patient_id:
                patient = p
                break
        
        if patient is None or patient.status in [PatientStatus.CURED, PatientStatus.LOST]:
            return False
        
        if action_type == 0:  # Assign to bed
            if self._free_beds > 0 and self._free_nurses > 0:
                return self.assign_patient_to_bed(patient)
            return False
        elif action_type == 1:  # Assign to ventilator
            if self._free_vents > 0:
                # If upgrading from bed to ventilator, this incurs a setup delay (tracked for reward shaping)
                if patient.status == PatientStatus.IN_BED:
                    self.just_incurred_setup_delay = True
                return self.assign_patient_to_ventilator(patient)
            return False
        elif action_type == 2:  # Do nothing
            return True
        
        return False
    
    def update_tick(self):
        """Update the simulation by one tick"""
        self.tick += 1
        self.just_saved_a_patient = False
        self.just_lost_a_patient = False
        self.just_incurred_setup_delay = False
        
        # Check for new patient arrivals
        if self.tick >= self.next_arrival:
            self.add_patient()
            self.next_arrival = self.tick + self._generate_next_arrival()
        
        # Update all patients
        for patient in self.patients:
            prev_status = patient.status
            # Track which resources were assigned before update (for counter updates)
            had_bed = patient.assigned_bed is not None
            had_nurse = patient.assigned_nurse is not None
            had_vent = patient.assigned_ventilator is not None
            
            patient.update()
            
            # Track state changes and release resources
            if prev_status != PatientStatus.CURED and patient.status == PatientStatus.CURED:
                self.just_saved_a_patient = True
                self.patients_saved += 1
                # Release resources when patient is cured (update counters)
                self._release_patient_resources_counters(had_bed, had_nurse, had_vent)
            elif prev_status != PatientStatus.LOST and patient.status == PatientStatus.LOST:
                self.just_lost_a_patient = True
                self.patients_lost += 1
                # Release resources when patient is lost (update counters)
                self._release_patient_resources_counters(had_bed, had_nurse, had_vent)
            
            # Track wait time
            if patient.status == PatientStatus.WAITING:
                self.total_wait_time += 1
        
        # Remove cured/lost patients after a delay (optional - for now keep them for stats)
        # In practice, you might want to remove them after a few ticks
    
    def _release_patient_resources_counters(self, had_bed: bool, had_nurse: bool, had_vent: bool):
        """Update resource counters when a patient is cured or lost"""
        # Note: Patient._release_resources() already handles setting resource objects to None
        # and setting their available flags. We just need to update the counters here.
        if had_bed:
            self._free_beds += 1
        if had_nurse:
            self._free_nurses += 1
        if had_vent:
            self._free_vents += 1
    
    def get_waiting_patients(self) -> List[Patient]:
        """Get list of patients currently waiting"""
        return [p for p in self.patients if p.status == PatientStatus.WAITING]
    
    @property
    def total_waiting_patients(self) -> int:
        """Get count of waiting patients"""
        return len(self.get_waiting_patients())
    
    @property
    def free_beds(self):
       return self._free_beds
    
    @property
    def free_nurses(self):
       return self._free_nurses
 
    @property
    def free_vents(self):
       return self._free_vents
    
    def is_game_over(self, max_ticks: int = 1000) -> bool:
        """Check if game is over (e.g., time limit reached)"""
        return self.tick >= max_ticks
    
    def get_score(self) -> dict:
        """Get current game score"""
        return {
            'patients_saved': self.patients_saved,
            'patients_lost': self.patients_lost,
            'total_wait_time': self.total_wait_time,
            'tick': self.tick,
            'active_patients': len([p for p in self.patients if p.status not in [PatientStatus.CURED, PatientStatus.LOST]])
        }

