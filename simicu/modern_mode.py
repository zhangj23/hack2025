"""
Modern AI Mode - Run the trained RL agent
This demonstrates the AI agent managing the ICU automatically.
"""

import pygame
import sys
import numpy as np
from stable_baselines3 import PPO
from sim_icu_env import SimICUEnv
from sim_icu_logic import PatientStatus, PatientType
import os


# Colors (same as retro mode for consistency)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
GREEN = (50, 205, 50)
BLUE = (30, 144, 255)
YELLOW = (255, 215, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
ORANGE = (255, 165, 0)
DARK_RED = (139, 0, 0)
DARK_GREEN = (0, 100, 0)


class ModernSimICU:
    """Pygame visualization for AI-controlled SimICU"""
    
    def __init__(self, model_path="models/sim_icu_ai_agent"):
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("SimICU - Modern AI Mode")
        self.clock = pygame.time.Clock()
        # Match Retro font sizing for visual parity
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.large_font = pygame.font.Font(None, 40)
        self.retro_antialias = False
        
        # Load trained model
        print(f"Loading AI model from {model_path}...")
        try:
            self.model = PPO.load(model_path)
            print("Model loaded successfully!")
        except FileNotFoundError:
            print(f"ERROR: Model not found at {model_path}")
            print("Please train the model first using: python train.py")
            sys.exit(1)
        
        # Create environment
        self.env = SimICUEnv(max_patients=10, max_ticks=1000)
        self.obs, self.info = self.env.reset()
        
        # Game state
        self.paused = False
        self.speed = 1  # Actions per frame
        self.episode = 1
        
        # UI layout (same as retro mode)
        self.waiting_room_y = 50
        self.waiting_room_height = 200
        self.bed_area_y = 300
        self.bed_area_height = 400
        self.ui_panel_x = 900
        self.ui_panel_width = 300

        # XAI log
        self.reco_log = []  # list of strings
        self.max_log_lines = 10
        self.show_emr = False
        self.show_intro = True

        # Nurse render size
        self.nurse_size = 64
        self.nurse_speed = 28.0

        # Nurse animation state
        self.nurse_positions = {}      # nurse -> (x,y)
        self.nurse_paths = {}          # nurse -> [(wx,wy), ...]
        self.nurse_stations = {}       # nurse -> (x,y)
        self.pending_assignments = []  # [{'nurse': n, 'patient': p, 'bed': bed} | {'vent': vent}]
        # Defer engine assignments until nurse arrival (to avoid immediate healing)
        self.deferred_action = None
        self.ready_to_apply_deferred = False

        # Resource tile registries for targeting
        self.bed_positions = {}        # bed -> (x,y,w,h)
        self.vent_positions = {}       # vent -> (x,y,w,h)

        # Movement simulation: patient_id -> {'x','y','tx','ty','speed'}
        self.patient_moves = {}

        # Patient sprite (standing/selected) -> raised hand variant
        base_dir = os.path.dirname(__file__)
        standing_path = os.path.join(base_dir, "sprites", "raised_hand.png")
        try:
            self.patient_sprite_raw = pygame.image.load(standing_path).convert_alpha()
        except Exception:
            self.patient_sprite_raw = None
        self._patient_sprite_cache = {}

        # Patient-in-bed sprite (occupied bed visual)
        bed_patient_path = os.path.join(base_dir, "sprites", "patient.png")
        try:
            self.patient_in_bed_sprite_raw = pygame.image.load(bed_patient_path).convert_alpha()
        except Exception:
            self.patient_in_bed_sprite_raw = None
        self._patient_in_bed_sprite_cache = {}
        self.patient_in_bed_scale = 1.2
        self.waiting_sprite_scale_w = 1.3
        self.waiting_sprite_scale_h = 1.6

        # Sitting sprite for waiting room (AI mode always shows sitting)
        sitting_path = os.path.join(base_dir, "sprites", "sitting.png")
        try:
            self.sitting_sprite_raw = pygame.image.load(sitting_path).convert_alpha()
        except Exception:
            self.sitting_sprite_raw = None
        self._sitting_sprite_cache = {}

        # Waiting room background
        wr_path = os.path.join(base_dir, "sprites", "waiting_room.png")
        try:
            self.waiting_bg_raw = pygame.image.load(wr_path).convert_alpha()
        except Exception:
            self.waiting_bg_raw = None
        self._waiting_bg_cache = {}

        # Global hospital floor background
        floor_path = os.path.join(base_dir, "sprites", "hospital_floor.png")
        try:
            self.floor_bg_raw = pygame.image.load(floor_path).convert()
        except Exception:
            self.floor_bg_raw = None
        self._floor_bg_cache = {}
        
        # Bed sprite (empty bed visual)
        bed_path = os.path.join(base_dir, "sprites", "bed.png")
        try:
            self.bed_sprite_raw = pygame.image.load(bed_path).convert_alpha()
        except Exception:
            self.bed_sprite_raw = None
        self._bed_sprite_cache = {}

        # Vent sprites (empty and occupied)
        vent_bed_path = os.path.join(base_dir, "sprites", "vent_bed.png")
        vent_patient_path = os.path.join(base_dir, "sprites", "vent_patient.png")
        try:
            self.vent_bed_raw = pygame.image.load(vent_bed_path).convert_alpha()
        except Exception:
            self.vent_bed_raw = None
        try:
            self.vent_patient_raw = pygame.image.load(vent_patient_path).convert_alpha()
        except Exception:
            self.vent_patient_raw = None
        self._vent_bed_cache = {}
        self._vent_patient_cache = {}

        # Nurse sprite
        nurse_path = os.path.join(base_dir, "sprites", "nurse.png")
        try:
            self.nurse_sprite_raw = pygame.image.load(nurse_path).convert_alpha()
        except Exception:
            self.nurse_sprite_raw = None
        self._nurse_sprite_cache = {}
        # Optional: divider sprite (not used by default)
        divider_path = os.path.join(base_dir, "sprites", "divider.png")
        try:
            self.divider_sprite_raw = pygame.image.load(divider_path).convert_alpha()
        except Exception:
            self.divider_sprite_raw = None
        self._divider_cache_by_height = {}
        self.divider_width_scale = 1.5
        self.divider_height_scale = 1.5
        self.divider_left_shift = -16
    
    def draw_patient(self, patient, x, y, width=100, height=80, minimal=False):
        """Draw a patient icon (sprite if available).
        minimal=True renders only the life bar (used for waiting room).
        """
        if minimal:
            # Waiting room: show standing sprite (if available) + life bar + number only.
            # AI mode: show sitting sprite in waiting room if available
            sprite = None
            if getattr(self, "sitting_sprite_raw", None):
                tw = max(1, int(width * self.waiting_sprite_scale_w))
                th = max(1, int(height * self.waiting_sprite_scale_h))
                key = (tw, th, "waiting_sit")
                if key not in self._sitting_sprite_cache:
                    self._sitting_sprite_cache[key] = pygame.transform.smoothscale(self.sitting_sprite_raw, (tw, th))
                sprite = self._sitting_sprite_cache[key]
            elif getattr(self, "patient_sprite_raw", None):
                tw = max(1, int(width * self.waiting_sprite_scale_w))
                th = max(1, int(height * self.waiting_sprite_scale_h))
                key = (tw, th, "waiting")
                if key not in self._patient_sprite_cache:
                    self._patient_sprite_cache[key] = pygame.transform.smoothscale(self.patient_sprite_raw, (tw, th))
                sprite = self._patient_sprite_cache[key]
            if sprite is not None:
                draw_x = x + (width - sprite.get_width()) // 2
                draw_y = y + (height - sprite.get_height()) // 2
                self.screen.blit(sprite, (draw_x, draw_y))
            bar_width = int((patient.severity / 100.0) * width)
            bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
            pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
            life_value = int(round(patient.severity))
            value_text = self.small_font.render(f"{life_value}", True, WHITE)
            self.screen.blit(value_text, (x + 5, y + 5))
            # Type badge in waiting room (top-right small badge)
            try:
                t_letter = "R" if patient.patient_type == PatientType.RESPIRATORY else "C" if patient.patient_type == PatientType.CARDIAC else "T"
                badge = self.small_font.render(t_letter, self.retro_antialias, BLACK)
                bw, bh = badge.get_size()
                pad = 4
                bx = x + width - bw - pad - 2
                by = y + 2
                pygame.draw.rect(self.screen, YELLOW, (bx - 2, by - 2, bw + 4, bh + 4))
                self.screen.blit(badge, (bx, by))
            except Exception:
                pass
            return
        drew_sprite = False
        if getattr(self, "patient_sprite_raw", None):
            key = (width, height)
            if key not in self._patient_sprite_cache:
                src_w, src_h = self.patient_sprite_raw.get_size()
                scale = min(width / src_w, height / src_h)
                scaled = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
                self._patient_sprite_cache[key] = pygame.transform.smoothscale(self.patient_sprite_raw, scaled)
            sprite = self._patient_sprite_cache[key]
            draw_x = x + (width - sprite.get_width()) // 2
            draw_y = y + (height - sprite.get_height()) // 2
            self.screen.blit(sprite, (draw_x, draw_y))
            pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
            drew_sprite = True
        if not drew_sprite:
            color = RED if patient.status == PatientStatus.WAITING else GREEN
            if patient.status == PatientStatus.ON_VENTILATOR:
                color = BLUE
            elif patient.status in [PatientStatus.CURED, PatientStatus.LOST]:
                color = GRAY
            pygame.draw.rect(self.screen, color, (x, y, width, height))
            pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        # Severity bar
        bar_width = int((patient.severity / 100.0) * width)
        # Life bar: green when high life, orange mid, red low
        bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
        pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
        
        # Patient ID
        id_text = self.small_font.render(f"#{patient.id}", True, WHITE)
        self.screen.blit(id_text, (x + 5, y + 5))
        
        # Status text
        status_text = self.small_font.render(patient.status.value, True, WHITE)
        self.screen.blit(status_text, (x + 5, y + 20))
        
        # Severity number (rounded to whole number)
        life_value = int(round(patient.severity))
        severity_text = self.small_font.render(f"{life_value}", True, WHITE)
        self.screen.blit(severity_text, (x + 5, y + 35))
    
    def draw_bed(self, bed, x, y, width=120, height=120):
        """Draw a bed icon with sprites; overlay patient info when occupied."""
        # Record tile for nurse targeting
        self.bed_positions[bed] = (x, y, width, height)
        # Empty bed sprite or fallback rect (only for available regular beds)
        if bed.available:
            if getattr(self, "bed_sprite_raw", None):
                key = (width, height)
                if key not in self._bed_sprite_cache:
                    self._bed_sprite_cache[key] = pygame.transform.smoothscale(self.bed_sprite_raw, (width, height))
                self.screen.blit(self._bed_sprite_cache[key], (x, y))
            else:
                pygame.draw.rect(self.screen, LIGHT_GRAY, (x, y, width, height))
            # Available bed outline
            pygame.draw.rect(self.screen, GREEN, (x, y, width, height), 2)
        else:
            # Occupied: show patient-in-bed sprite if available
            if getattr(self, "patient_in_bed_sprite_raw", None):
                sw = max(1, int(width * self.patient_in_bed_scale))
                sh = max(1, int(height * self.patient_in_bed_scale))
                key = (sw, sh)
                if key not in self._patient_in_bed_sprite_cache:
                    self._patient_in_bed_sprite_cache[key] = pygame.transform.smoothscale(self.patient_in_bed_sprite_raw, (sw, sh))
                draw_x = x + (width - sw) // 2
                draw_y = y + (height - sh) // 2
                self.screen.blit(self._patient_in_bed_sprite_cache[key], (draw_x, draw_y))
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))
            pygame.draw.rect(self.screen, RED, (x, y, width, height), 2)
            # Overlay bar, id, type badge
            try:
                patient = next(p for p in self.env.game.patients if p.assigned_bed == bed)
                bar_width = int((patient.severity / 100.0) * width)
                bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
                pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
                id_text = self.small_font.render(f"#{patient.id}", self.retro_antialias, WHITE)
                self.screen.blit(id_text, (x + 4, y + 4))
                t_letter = "R" if patient.patient_type == PatientType.RESPIRATORY else "C" if patient.patient_type == PatientType.CARDIAC else "T"
                badge = self.small_font.render(t_letter, self.retro_antialias, BLACK)
                bw, bh = badge.get_size()
                px, py = x + width - bw - 6, y + 2
                pygame.draw.rect(self.screen, YELLOW, (px - 2, py - 2, bw + 4, bh + 4))
                self.screen.blit(badge, (px, py))
            except StopIteration:
                pass
    
    def draw_nurse(self, nurse, x, y, size=40):
        """Draw a nurse sprite (fallback to circle)"""
        if getattr(self, "nurse_sprite_raw", None):
            key = (size, size)
            if key not in self._nurse_sprite_cache:
                self._nurse_sprite_cache[key] = pygame.transform.smoothscale(self.nurse_sprite_raw, (size, size))
            self.screen.blit(self._nurse_sprite_cache[key], (x, y))
        else:
            color = GREEN if nurse.available else RED
            pygame.draw.circle(self.screen, color, (x + size // 2, y + size // 2), size // 2)
            pygame.draw.circle(self.screen, BLACK, (x + size // 2, y + size // 2), size // 2, 2)
        
        label = "N" if nurse.available else "BUSY"
        label_text = self.small_font.render(label, True, WHITE)
        text_rect = label_text.get_rect(center=(x + size // 2, y + size // 2))
        self.screen.blit(label_text, text_rect)
    
    def draw_ventilator(self, vent, x, y, width=120, height=120):
        """Draw a ventilator bed with sprites and overlay patient health bar when occupied."""
        # Record tile for nurse targeting
        self.vent_positions[vent] = (x, y, width, height)
        occupied = not vent.available
        if not occupied:
            if getattr(self, "vent_bed_raw", None):
                key = (width, height)
                if key not in self._vent_bed_cache:
                    self._vent_bed_cache[key] = pygame.transform.smoothscale(self.vent_bed_raw, (width, height))
                self.screen.blit(self._vent_bed_cache[key], (x, y))
            else:
                pygame.draw.rect(self.screen, LIGHT_GRAY, (x, y, width, height))
            pygame.draw.rect(self.screen, GREEN, (x, y, width, height), 2)
        else:
            if getattr(self, "vent_patient_raw", None):
                key = (width, height)
                if key not in self._vent_patient_cache:
                    self._vent_patient_cache[key] = pygame.transform.smoothscale(self.vent_patient_raw, (width, height))
                self.screen.blit(self._vent_patient_cache[key], (x, y))
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))
            pygame.draw.rect(self.screen, RED, (x, y, width, height), 2)
            # Overlay health bar for the patient on this ventilator
            try:
                patient = next(p for p in self.env.game.patients if p.assigned_ventilator == vent and p.status == PatientStatus.ON_VENTILATOR)
                bar_width = int((patient.severity / 100.0) * width)
                bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
                pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
                # Type badge
                t_letter = "R" if patient.patient_type == PatientType.RESPIRATORY else "C" if patient.patient_type == PatientType.CARDIAC else "T"
                badge = self.small_font.render(t_letter, self.retro_antialias, BLACK)
                bw, bh = badge.get_size()
                px, py = x + width - bw - 6, y + 2
                pygame.draw.rect(self.screen, YELLOW, (px - 2, py - 2, bw + 4, bh + 4))
                self.screen.blit(badge, (px, py))
            except StopIteration:
                pass
        # Optional divider to the right (kept from other branch)
        if getattr(self, "divider_sprite_raw", None):
            key_h = (height, self.divider_width_scale, self.divider_height_scale)
            if key_h not in self._divider_cache_by_height:
                base_w = self.divider_sprite_raw.get_width()
                base_h = self.divider_sprite_raw.get_height()
                sh = int(height * self.divider_height_scale)
                sw = int(base_w * (sh / base_h) * self.divider_width_scale)
                self._divider_cache_by_height[key_h] = pygame.transform.smoothscale(
                    self.divider_sprite_raw, (max(1, sw), max(1, sh))
                )
            pad = 8
            surf = self._divider_cache_by_height[key_h]
            self.screen.blit(surf, (x + width + pad + self.divider_left_shift, y + (height - surf.get_height()) // 2))

    def draw_ui_panel(self):
        """Draw the UI information panel"""
        panel_x = self.ui_panel_x
        panel_y = 50
        
        # Background
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, self.ui_panel_width, self.height - 100))
        pygame.draw.rect(self.screen, BLACK, (panel_x, panel_y, self.ui_panel_width, self.height - 100), 2)
        
        y_offset = panel_y + 20
        
        # Title
        title = self.large_font.render("AI MODE", True, BLUE)
        self.screen.blit(title, (panel_x + 20, y_offset))
        y_offset += 50
        
        # Score
        score = self.env.game.get_score()
        score_text = self.font.render(f"Saved: {score['patients_saved']}", True, GREEN)
        self.screen.blit(score_text, (panel_x + 20, y_offset))
        y_offset += 30
        
        lost_text = self.font.render(f"Lost: {score['patients_lost']}", True, RED)
        self.screen.blit(lost_text, (panel_x + 20, y_offset))
        y_offset += 30
        
        # Success rate
        total = score['patients_saved'] + score['patients_lost']
        if total > 0:
            success_rate = (score['patients_saved'] / total) * 100
            rate_text = self.font.render(f"Success: {success_rate:.1f}%", True, YELLOW)
            self.screen.blit(rate_text, (panel_x + 20, y_offset))
        y_offset += 40
        
        # Tick
        tick_text = self.font.render(f"Tick: {self.env.game.tick}", True, WHITE)
        self.screen.blit(tick_text, (panel_x + 20, y_offset))
        y_offset += 30
        
        # Episode
        episode_text = self.font.render(f"Episode: {self.episode}", True, WHITE)
        self.screen.blit(episode_text, (panel_x + 20, y_offset))
        y_offset += 40
        
        # Resources
        resources_title = self.font.render("Resources:", True, WHITE)
        self.screen.blit(resources_title, (panel_x + 20, y_offset))
        y_offset += 30
        
        nurses_text = self.font.render(f"Nurses: {self.env.game.free_nurses}/{self.env.game.num_nurses}", True, WHITE)
        self.screen.blit(nurses_text, (panel_x + 20, y_offset))
        y_offset += 25
        
        beds_text = self.font.render(f"Beds: {self.env.game.free_beds}/{self.env.game.num_beds}", True, WHITE)
        self.screen.blit(beds_text, (panel_x + 20, y_offset))
        y_offset += 25
        
        vents_text = self.font.render(f"Vents: {self.env.game.free_vents}/{self.env.game.num_ventilators}", True, WHITE)
        self.screen.blit(vents_text, (panel_x + 20, y_offset))
        y_offset += 40
        
        # Controls
        controls = [
            "CONTROLS:",
            "SPACE: Pause/Resume",
            "R: Reset episode",
            "E: Toggle EMR mockup",
            "ESC: Quit"
        ]
        
        for control in controls:
            ctrl_text = self.small_font.render(control, True, YELLOW)
            self.screen.blit(ctrl_text, (panel_x + 20, y_offset))
            y_offset += 20

        # XAI log
        y_offset += 10
        xai_title = self.font.render("AI Recommendation Log", True, WHITE)
        self.screen.blit(xai_title, (panel_x + 20, y_offset))
        y_offset += 28
        for line in self.reco_log[-self.max_log_lines:]:
            line_text = self.small_font.render(line, True, LIGHT_GRAY)
            self.screen.blit(line_text, (panel_x + 20, y_offset))
            y_offset += 18
        
        # Pause indicator
        if self.paused:
            pause_text = self.large_font.render("PAUSED", True, YELLOW)
            text_rect = pause_text.get_rect(center=(panel_x + self.ui_panel_width // 2, self.height - 50))
            self.screen.blit(pause_text, text_rect)
    
    def draw(self):
        """Draw the entire game screen"""
        if self.floor_bg_raw:
            key_bg = (self.width, self.height)
            if key_bg not in self._floor_bg_cache:
                self._floor_bg_cache[key_bg] = pygame.transform.smoothscale(self.floor_bg_raw, (self.width, self.height))
            self.screen.blit(self._floor_bg_cache[key_bg], (0, 0))
        else:
            self.screen.fill(BLACK)
        
        # Intro overlay
        if getattr(self, "show_intro", False):
            return self.draw_intro_overlay()

        # Draw waiting room
        waiting_title = self.font.render("WAITING ROOM", True, WHITE)
        self.screen.blit(waiting_title, (50, 20))
        wr_x, wr_y, wr_w, wr_h = 50, self.waiting_room_y, 800, self.waiting_room_height
        if self.waiting_bg_raw:
            key = (wr_w, wr_h)
            if key not in self._waiting_bg_cache:
                self._waiting_bg_cache[key] = pygame.transform.smoothscale(self.waiting_bg_raw, (wr_w, wr_h))
            self.screen.blit(self._waiting_bg_cache[key], (wr_x, wr_y))
        else:
            pygame.draw.rect(self.screen, DARK_GRAY, (wr_x, wr_y, wr_w, wr_h))
        pygame.draw.rect(self.screen, WHITE, (wr_x, wr_y, wr_w, wr_h), 2)
        
        # Draw waiting patients (exclude any currently walking to a target)
        waiting_patients = [p for p in self.env.game.get_waiting_patients() if p.id not in self.patient_moves]
        for i, patient in enumerate(waiting_patients[:6]):
            self.draw_patient(patient, 50 + i * 120, self.waiting_room_y + 20, minimal=True)
        
        # Draw bed area (shifted right to match Retro layout)
        bed_title = self.font.render("ICU BEDS", self.retro_antialias, WHITE)
        self.screen.blit(bed_title, (200, self.bed_area_y - 30))
        for i, bed in enumerate(self.env.game.beds):
            bed_x = 200 + (i % 4) * 150
            bed_y = self.bed_area_y + 50 + (i // 4) * 120
            self.draw_bed(bed, bed_x, bed_y)
            
            # Draw patient in bed if occupied
            if not getattr(self, "patient_in_bed_sprite_raw", None):
                for patient in self.env.game.patients:
                    if patient.assigned_bed == bed:
                        # Suppress overlay while patient is still moving to this bed
                        if getattr(self, "patient_moves", None) and patient.id in self.patient_moves:
                            continue
                        self.draw_patient(patient, bed_x + 10, bed_y - 20, 100, 60)
        
        # Draw ventilators (on the left)
        vent_title = self.font.render("VENTILATORS", self.retro_antialias, WHITE)
        self.screen.blit(vent_title, (50, self.bed_area_y - 30))
        for i, vent in enumerate(self.env.game.ventilators):
            vent_x = 50
            vent_y = self.bed_area_y + 50 + i * 120
            self.draw_ventilator(vent, vent_x, vent_y)
            
            # Draw patient on ventilator if occupied
            if not getattr(self, "vent_patient_raw", None):
                for patient in self.env.game.patients:
                    if patient.assigned_ventilator == vent:
                        if getattr(self, "patient_moves", None) and patient.id in self.patient_moves:
                            continue
                        self.draw_patient(patient, vent_x + 10, vent_y - 20, 100, 60)

        # Draw moving patients (walking overlays)
        if self.patient_moves:
            remove_ids = []
            for pid, mv in self.patient_moves.items():
                # Advance towards target
                dx = mv['tx'] - mv['x']
                dy = mv['ty'] - mv['y']
                dist = max(1e-6, (dx*dx + dy*dy) ** 0.5)
                step = min(mv['speed'], dist)
                mv['x'] += (dx / dist) * step
                mv['y'] += (dy / dist) * step
                # Draw larger walking sprite + health bar
                patient = next((p for p in self.env.game.patients if p.id == pid), None)
                if patient is not None:
                    # sprite
                    if getattr(self, "patient_sprite_raw", None):
                        key = (140, 110, "walk")
                        if key not in self._patient_sprite_cache:
                            src_w, src_h = self.patient_sprite_raw.get_size()
                            scale = min(140 / src_w, 110 / src_h)
                            scaled = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
                            self._patient_sprite_cache[key] = pygame.transform.smoothscale(self.patient_sprite_raw, scaled)
                        sprite = self._patient_sprite_cache[key]
                        sx = int(mv['x']) + (140 - sprite.get_width()) // 2
                        sy = int(mv['y']) + (110 - sprite.get_height()) // 2
                        self.screen.blit(sprite, (sx, sy))
                    # bar
                    bar_w = int((patient.severity / 100.0) * 140)
                    bar_col = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
                    pygame.draw.rect(self.screen, bar_col, (int(mv['x']), int(mv['y']) + 100, bar_w, 10))
                # Arrival check
                if dist <= mv['speed'] + 0.1:
                    remove_ids.append(pid)
            for rid in remove_ids:
                self.patient_moves.pop(rid, None)
        
        # Draw nurses
        nurse_title = self.font.render("NURSES", True, WHITE)
        self.screen.blit(nurse_title, (850, self.bed_area_y - 30))
        # Define stations (fixed positions at right panel like Retro)
        for i, nurse in enumerate(self.env.game.nurses):
            self.nurse_stations[nurse] = (850, self.bed_area_y + 50 + i * 56)
        # Draw animated nurses at current positions (fallback to station)
        for nurse in self.env.game.nurses:
            nx, ny = self.nurse_positions.get(nurse, self.nurse_stations[nurse])
            self.draw_nurse(nurse, int(nx), int(ny), self.nurse_size)
        
        # Draw UI panel
        self.draw_ui_panel()
        
        pygame.display.flip()

    def draw_intro_overlay(self):
        self.screen.fill(BLACK)
        title = self.large_font.render("SIMICU - MODERN MODE", self.retro_antialias, YELLOW)
        subtitle = self.font.render("AI-CONTROLLED ICU MANAGEMENT", self.retro_antialias, WHITE)
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 120))
        self.screen.blit(subtitle, ((self.width - subtitle.get_width()) // 2, 165))

        lines = [
            "This mode runs the same simulation as Retro,",
            "but actions are chosen by a trained AI (PPO).",
            "The visuals, timing, and constraints are identical.",
            "",
            "Press PLAY to start."
        ]
        y = 220
        for line in lines:
            t = self.font.render(line, self.retro_antialias, LIGHT_GRAY)
            self.screen.blit(t, (100, y))
            y += 26

        btn_w, btn_h = 220, 56
        btn_x = (self.width - btn_w) // 2
        btn_y = y + 30
        pygame.draw.rect(self.screen, BLUE, (btn_x, btn_y, btn_w, btn_h), border_radius=6)
        pygame.draw.rect(self.screen, WHITE, (btn_x, btn_y, btn_w, btn_h), 2, border_radius=6)
        btn_text = self.large_font.render("PLAY", self.retro_antialias, WHITE)
        self.screen.blit(btn_text, (btn_x + (btn_w - btn_text.get_width()) // 2,
                                    btn_y + (btn_h - btn_text.get_height()) // 2))
        self._intro_button = (btn_x, btn_y, btn_w, btn_h)
        pygame.display.flip()

    def _push_reco(self, text: str):
        self.reco_log.append(text)
        if len(self.reco_log) > 200:
            self.reco_log = self.reco_log[-200:]

    def _heuristic_reason(self, patient, action_type):
        crisis_score = patient.severity * max(1, patient.time_waiting)
        typ = patient.patient_type.value if hasattr(patient, "patient_type") else "unknown"
        if action_type == 1:
            return f"RECOMMENDING: Patient {patient.id} -> Vent | REASON: Crisis={crisis_score:.0f}, type={typ}"
        elif action_type == 0:
            return f"RECOMMENDING: Patient {patient.id} -> Bed | REASON: Crisis={crisis_score:.0f}, vents busy"
        else:
            return f"RECOMMENDING: No-op | REASON: No valid resources or strategic wait"

    def _draw_emr_overlay(self):
        if not self.show_emr:
            return
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        # Mock EMR card
        card_w, card_h = 520, 300
        card_x, card_y = (self.width - card_w) // 2, (self.height - card_h) // 2
        pygame.draw.rect(self.screen, DARK_GRAY, (card_x, card_y, card_w, card_h))
        pygame.draw.rect(self.screen, WHITE, (card_x, card_y, card_w, card_h), 2)
        title = self.large_font.render("EMR Integration (Mock)", True, YELLOW)
        self.screen.blit(title, (card_x + 20, card_y + 16))
        # Example patient
        if self.env.game.patients:
            p = max(self.env.game.patients, key=lambda q: q.severity * max(1, q.time_waiting))
            lines = [
                f"Patient #{p.id} | Type: {getattr(p, 'patient_type', PatientType.RESPIRATORY).value}",
                f"Severity: {p.severity:.0f}   Waiting: {p.time_waiting}   Status: {p.status.value}",
                "AI Suggests: " + ("Ventilator" if self.env.game.free_vents > 0 else "Bed" if self.env.game.free_beds > 0 else "Observe"),
                "Reason: Max crisis score across cohort"
            ]
            y = card_y + 70
            for line in lines:
                t = self.font.render(line, True, WHITE)
                self.screen.blit(t, (card_x + 20, y))
                y += 28
    
    def run(self):
        """Main game loop"""
        running = True
        done = False
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.show_intro:
                            self.show_intro = False
                        else:
                            self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        if self.show_intro:
                            self.show_intro = False
                        else:
                            self.obs, self.info = self.env.reset()
                            self.episode += 1
                            done = False
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.speed = min(10, self.speed + 1)
                    elif event.key == pygame.K_MINUS:
                        self.speed = max(1, self.speed - 1)
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_e:
                        self.show_emr = not self.show_emr
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and getattr(self, "show_intro", False):
                        if hasattr(self, "_intro_button"):
                            bx, by, bw, bh = self._intro_button
                            mx, my = event.pos
                            if bx <= mx <= bx + bw and by <= my <= by + bh:
                                self.show_intro = False
            
            if not self.paused and not done:
                # Let AI make decisions
                for _ in range(self.speed):
                    # If a deferred assignment is ready (nurse arrived), apply it now
                    if self.ready_to_apply_deferred and self.deferred_action is not None:
                        self.obs, reward, terminated, truncated, self.info = self.env.step(self.deferred_action)
                        self.deferred_action = None
                        self.ready_to_apply_deferred = False
                        done = terminated or truncated
                        if done:
                            break

                    action, _ = self.model.predict(self.obs, deterministic=True)
                    # If any patient is walking or a nurse is already en route, block new assignments
                    try:
                        if (getattr(self, "patient_moves", None) and len(self.patient_moves) > 0) \
                           or (getattr(self, "pending_assignments", None) and len(self.pending_assignments) > 0):
                            pid, at = int(action[0]), int(action[1])
                            if at in (0, 1):
                                # convert to no-op while movement in progress
                                action = np.array([0, 2], dtype=np.int64)
                                self._push_reco("Blocked: movement in progress -> NO-OP")
                    except Exception:
                        pass
                    # Prepare movement start if assigning from waiting room
                    start_pos = None
                    try:
                        pid, at = int(action[0]), int(action[1])
                        if at in (0, 1) and pid < len(self.env.game.patients):
                            pre_p = self.env.game.patients[pid]
                            if pre_p.status == PatientStatus.WAITING:
                                wait_list = self.env.game.get_waiting_patients()
                                # index among first 6 slots visually shown
                                if pre_p in wait_list:
                                    idx = wait_list.index(pre_p)
                                    start_pos = (50 + idx * 120, self.waiting_room_y + 20)
                    except Exception:
                        pass
 
                    self.obs, reward, terminated, truncated, self.info = self.env.step(action)
                    # XAI log: try to reconstruct which patient was acted on
                    try:
                        pid, at = int(action[0]), int(action[1])
                        if pid < len(self.env.game.patients):
                            p = self.env.game.patients[pid]
                            self._push_reco(self._heuristic_reason(p, at))
                            # Create walking overlay towards new assignment target; defer engine assignment until nurse arrives
                            if start_pos and at in (0, 1) and (self.deferred_action is None):
                                # Determine target tile based on new assignment
                                tx, ty = None, None
                                target_bed = None
                                target_vent = None
                                if getattr(p, "assigned_bed", None) is not None:
                                    # compute bed tile position
                                    try:
                                        target_bed = p.assigned_bed
                                        bi = self.env.game.beds.index(target_bed)
                                        tx = 200 + (bi % 4) * 150 + 10
                                        ty = self.bed_area_y + 50 + (bi // 4) * 120 - 20
                                    except ValueError:
                                        pass
                                elif getattr(p, "assigned_ventilator", None) is not None:
                                    try:
                                        target_vent = p.assigned_ventilator
                                        vi = self.env.game.ventilators.index(target_vent)
                                        tx = 50 + 10
                                        ty = self.bed_area_y + 50 + vi * 120 - 20
                                    except ValueError:
                                        pass
                                if tx is not None and ty is not None:
                                    # Start movement for this patient if not already moving
                                    if (not getattr(self, "patient_moves", None)) or (p.id not in self.patient_moves):
                                        # Only allow if no other patient is currently moving (human parity)
                                        if (not self.patient_moves) or (len(self.patient_moves) == 0):
                                            self.patient_moves[p.id] = {'x': float(start_pos[0]), 'y': float(start_pos[1]), 'tx': float(tx), 'ty': float(ty), 'speed': 25.0}
                                     # Queue a nurse to run to this target (visual parity with Retro)
                                    avail = [n for n in self.env.game.nurses if n.available]
                                    if avail and (not getattr(self, "pending_assignments", None) or len(self.pending_assignments) == 0):
                                        # ensure nurse positions present
                                        for n in avail:
                                            if n not in self.nurse_positions:
                                                self.nurse_positions[n] = self.nurse_stations.get(n, (850, self.bed_area_y + 50))
                                        def dist2(n):
                                            nx, ny = self.nurse_positions.get(n, (tx, ty))
                                            dx = nx - tx; dy = ny - ty
                                            return dx*dx + dy*dy
                                        nearest = min(avail, key=dist2)
                                        # Use the nurse the environment actually assigned (if any)
                                        hold_nurse = getattr(p, 'assigned_nurse', None)
                                        # Temporarily detach the nurse so healing waits until arrival
                                        if hold_nurse is not None:
                                            p.assigned_nurse = None
                                            # keep nurse busy (available False) so counters remain consistent
                                        task = {'nurse': nearest, 'patient': p}
                                        if target_bed is not None:
                                            task['bed'] = target_bed
                                        if target_vent is not None:
                                            task['vent'] = target_vent
                                        self.pending_assignments.append(task)
                                        # Defer the engine assignment until nurse arrives
                                        self.deferred_action = np.array([pid, at], dtype=np.int64)
                                        self._push_reco("Deferred: waiting for nurse arrival to apply assignment")
                    except Exception:
                        pass
                    done = terminated or truncated
 
            # Update nurse animations each frame
            self._update_nurse_positions(size=self.nurse_size)
            self.draw()
            # EMR overlay after drawing
            self._draw_emr_overlay()
            self.clock.tick(10)  # 10 FPS
        
        pygame.quit()
        sys.exit()

    # --- Nurse animation helpers (parity with Retro) ---
    def _row_corridor_y(self):
        # Midline of the bed area as a simple corridor
        return self.bed_area_y + 50

    def _plan_path(self, start, target, use_corridor=True):
        cx, cy = start
        tx, ty = target
        if not use_corridor:
            return [(tx, ty)]
        corridor_y = self._row_corridor_y()
        path = []
        if abs(cy - corridor_y) > 2:
            path.append((cx, corridor_y))
        if abs(tx - cx) > 2:
            path.append((tx, corridor_y))
        if abs(ty - corridor_y) > 2:
            path.append((tx, ty))
        return path

    def _get_nurse_target(self, nurse, size=None):
        # If there is a pending assignment for this nurse, go to that resource tile
        for task in self.pending_assignments:
            if task.get('nurse') == nurse:
                if 'bed' in task and task['bed'] in self.bed_positions:
                    bx, by, bw, bh = self.bed_positions[task['bed']]
                    return bx + bw - (size or self.nurse_size), by
                if 'vent' in task and task['vent'] in self.vent_positions:
                    vx, vy, vw, vh = self.vent_positions[task['vent']]
                    return vx + vw - (size or self.nurse_size), vy
        # Otherwise go to station
        return self.nurse_stations.get(nurse, (850, self.bed_area_y + 50))

    def _update_nurse_positions(self, size=None):
        if size is None:
            size = self.nurse_size
        for nurse in self.env.game.nurses:
            target_x, target_y = self._get_nurse_target(nurse, size=size)
            if nurse not in self.nurse_positions:
                self.nurse_positions[nurse] = self.nurse_stations.get(nurse, (850, self.bed_area_y + 50))
                self.nurse_paths[nurse] = []
                continue
            cur_x, cur_y = self.nurse_positions[nurse]
            # Idle if no pending assignment
            has_pending = any(t.get('nurse') == nurse for t in self.pending_assignments)
            is_idle = not has_pending
            use_corridor = not is_idle
            if is_idle:
                target_x, target_y = self.nurse_stations.get(nurse, (850, self.bed_area_y + 50))
                if abs(cur_x - target_x) <= 1 and abs(cur_y - target_y) <= 1:
                    self.nurse_positions[nurse] = (target_x, target_y)
                    self.nurse_paths[nurse] = []
                    continue
            dx_t = target_x - cur_x
            dy_t = target_y - cur_y
            dist_to_target = (dx_t * dx_t + dy_t * dy_t) ** 0.5
            if dist_to_target <= 2:
                self.nurse_positions[nurse] = (target_x, target_y)
                self.nurse_paths[nurse] = []
                continue
            if dist_to_target <= 20:
                use_corridor = False
            if nurse not in self.nurse_paths:
                self.nurse_paths[nurse] = []
            if (not self.nurse_paths[nurse]
                or (abs(self.nurse_paths[nurse][-1][0] - target_x) > 3 and abs(self.nurse_paths[nurse][-1][1] - target_y) > 3)):
                self.nurse_paths[nurse] = self._plan_path((cur_x, cur_y), (target_x, target_y), use_corridor=use_corridor)
            # Advance toward next waypoint
            if self.nurse_paths[nurse]:
                wx, wy = self.nurse_paths[nurse][0]
            else:
                wx, wy = target_x, target_y
            dx = wx - cur_x
            dy = wy - cur_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 1:
                if self.nurse_paths[nurse]:
                    self.nurse_paths[nurse].pop(0)
                if not self.nurse_paths[nurse] and dist_to_target <= 2:
                    self.nurse_positions[nurse] = (target_x, target_y)
                    continue
                self.nurse_positions[nurse] = (wx, wy)
                continue
            step = min(self.nurse_speed, dist)
            if dist > 0:
                new_x = cur_x + dx / dist * step
                new_y = cur_y + dy / dist * step
            else:
                new_x, new_y = wx, wy
            self.nurse_positions[nurse] = (new_x, new_y)

        # Complete pending tasks when nurse reaches target tile (trigger deferred engine assignment)
        if self.pending_assignments:
            remaining = []
            for task in self.pending_assignments:
                nurse = task['nurse']
                nx, ny = self.nurse_positions.get(nurse, (None, None))
                if nx is None:
                    remaining.append(task)
                    continue
                if 'bed' in task and task['bed'] in self.bed_positions:
                    bx, by, bw, bh = self.bed_positions[task['bed']]
                    reached_rect = (bx - 4) <= nx <= (bx + bw + 4) and (by - 4) <= ny <= (by + bh + 4)
                    if not reached_rect:
                        remaining.append(task)
                        continue
                if 'vent' in task and task['vent'] in self.vent_positions:
                    vx, vy, vw, vh = self.vent_positions[task['vent']]
                    reached_rect = (vx - 4) <= nx <= (vx + vw + 4) and (vy - 4) <= ny <= (vy + vh + 4)
                    if not reached_rect:
                        remaining.append(task)
                        continue
                # reached -> apply deferred assignment at next loop iteration
                self.ready_to_apply_deferred = True
                # nurse will head back to station automatically when idle
            self.pending_assignments = remaining


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run SimICU in Modern AI Mode")
    parser.add_argument(
        "--model",
        type=str,
        default="models/sim_icu_ai_agent",
        help="Path to trained model (default: models/sim_icu_ai_agent)"
    )
    
    args = parser.parse_args()
    
    game = ModernSimICU(model_path=args.model)
    game.run()

