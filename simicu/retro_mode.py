"""
Retro Player Mode - Pygame Frontend
A pixel-art style interface for human players to manage the ICU.
"""

import pygame
import sys
import os
import math
from sim_icu_logic import SimICU, PatientStatus, PatientType


# Colors (retro palette)
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


class RetroSimICU:
    """Pygame frontend for SimICU"""
    
    def __init__(self):
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("SimICU - Retro Mode")
        self.clock = pygame.time.Clock()
        # Retro-styled fonts (bigger, crisp). Using pygame bundled font as fallback.
        try:
            base_font = pygame.font.match_font('freesansbold')
        except Exception:
            base_font = None
        self.retro_antialias = False  # disable AA for a pixel/retro look
        self.small_font = pygame.font.Font(base_font, 22)
        self.font = pygame.font.Font(base_font, 28)
        self.large_font = pygame.font.Font(base_font, 40)
        self.title_font = pygame.font.Font(base_font, 64)
        
        # Initialize game
        self.game = SimICU()
        self.selected_patient = None
        self.tick_speed = 1  # Ticks per frame
        self.fps = 10         # Target frames per second (lower = slower game)
        # Tick pacing: update simulation once every N frames (keep FPS constant)
        self.update_every_n_frames = 2  # higher -> slower simulation
        self._frame_counter = 0
        self.paused = False
        self.show_intro = True

        # Sprites
        base_dir = os.path.dirname(__file__)
        bed_path = os.path.join(base_dir, "sprites", "bed.png")
        try:
            self.bed_sprite_raw = pygame.image.load(bed_path).convert_alpha()
        except Exception:
            self.bed_sprite_raw = None  # fallback to rects if not found
        self._bed_sprite_cache = {}

        nurse_path = os.path.join(base_dir, "sprites", "nurse.png")
        try:
            self.nurse_sprite_raw = pygame.image.load(nurse_path).convert_alpha()
        except Exception:
            self.nurse_sprite_raw = None
        self._nurse_sprite_cache = {}

        # Patient sprite (standing)
        standing_path = os.path.join(base_dir, "sprites", "standing.png")
        try:
            self.patient_sprite_raw = pygame.image.load(standing_path).convert_alpha()
        except Exception:
            self.patient_sprite_raw = None
        self._patient_sprite_cache = {}

        # Patient-in-bed sprite (bed occupied visual)
        bed_patient_path = os.path.join(base_dir, "sprites", "patient.png")
        try:
            self.patient_in_bed_sprite_raw = pygame.image.load(bed_patient_path).convert_alpha()
        except Exception:
            self.patient_in_bed_sprite_raw = None
        self._patient_in_bed_sprite_cache = {}
        # Scale factor to draw patient-in-bed a bit larger than the bed tile
        self.patient_in_bed_scale = 1.2
        # Scale for standing sprite in waiting room
        self.waiting_sprite_scale_w = 1.3
        self.waiting_sprite_scale_h = 1.6

        # Sitting sprite for waiting room default
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

        # Object position maps for animation targets
        self.bed_positions = {}   # bed -> (x, y, w, h)
        self.vent_positions = {}  # vent -> (x, y, w, h)

        # Nurse movement state
        self.nurse_positions = {}  # nurse -> (x, y)
        self.nurse_stations = {}   # nurse -> (x, y)
        self.nurse_speed = 60      # pixels per tick
        self.nurse_size = 48       # draw size (bigger nurse)
        self.nurse_paths = {}      # nurse -> [(x, y), ...] waypoints
        self.pending_assignments = []  # [{'nurse': Nurse, 'patient': Patient, 'bed': Bed}]
        self.input_cooldown_ticks = 0  # limit human action rate
        
        # UI layout
        self.waiting_room_y = 50
        self.waiting_room_height = 200
        self.bed_area_y = 300
        self.bed_area_height = 400
        self.ui_panel_x = 900
        self.ui_panel_width = 300
    
    def draw_patient(self, patient, x, y, width=100, height=80, minimal=False):
        """Draw a patient.
        minimal=True renders only the life bar (used for waiting room).
        """
        if minimal:
            # Waiting room: show standing sprite (if available) + life bar + number only.
            # Pick which sprite to show: sitting by default, standing when selected
            sprite_raw = None
            cache = None
            if self.selected_patient == patient and self.patient_sprite_raw:
                sprite_raw = self.patient_sprite_raw
                cache = self._patient_sprite_cache
            elif self.sitting_sprite_raw:
                sprite_raw = self.sitting_sprite_raw
                cache = self._sitting_sprite_cache
            elif self.patient_sprite_raw:
                sprite_raw = self.patient_sprite_raw
                cache = self._patient_sprite_cache
            if sprite_raw is not None:
                tw = max(1, int(width * self.waiting_sprite_scale_w))
                th = max(1, int(height * self.waiting_sprite_scale_h))
                key = (tw, th, "waiting")
                if key not in cache:
                    cache[key] = pygame.transform.smoothscale(sprite_raw, (tw, th))
                sprite = cache[key]
                draw_x = x + (width - tw) // 2
                draw_y = y + (height - th) // 2
                self.screen.blit(sprite, (draw_x, draw_y))
            # Life bar and value
            bar_width = int((patient.severity / 100.0) * width)
            bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
            pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
            life_value = int(round(patient.severity))
            value_text = self.small_font.render(f"{life_value}", True, WHITE)
            self.screen.blit(value_text, (x + 5, y + 5))
            # Type badge (top-right)
            try:
                t = patient.patient_type
                t_letter = "R" if t == PatientType.RESPIRATORY else "C" if t == PatientType.CARDIAC else "T"
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
        # If we have a sprite, draw it scaled; otherwise fallback to colored box
        drew_sprite = False
        if self.patient_sprite_raw:
            key = (width, height)
            if key not in self._patient_sprite_cache:
                # Keep aspect ratio while fitting inside the target rect
                src_w, src_h = self.patient_sprite_raw.get_size()
                scale = min(width / src_w, height / src_h)
                scaled = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
                self._patient_sprite_cache[key] = pygame.transform.smoothscale(self.patient_sprite_raw, scaled)
            sprite = self._patient_sprite_cache[key]
            # center inside the box area
            draw_x = x + (width - sprite.get_width()) // 2
            draw_y = y + (height - sprite.get_height()) // 2
            self.screen.blit(sprite, (draw_x, draw_y))
            # outline the box for selection clarity
            pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
            drew_sprite = True
        if not drew_sprite:
            # Patient body (rectangle)
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

        # Patient type badge (top-right)
        try:
            t = patient.patient_type
            t_letter = "R" if t == PatientType.RESPIRATORY else "C" if t == PatientType.CARDIAC else "T"
            badge = self.small_font.render(t_letter, self.retro_antialias, BLACK)
            bw, bh = badge.get_size()
            pad = 4
            bx = x + width - bw - pad - 2
            by = y + 2
            pygame.draw.rect(self.screen, YELLOW, (bx - 2, by - 2, bw + 4, bh + 4))
            self.screen.blit(badge, (bx, by))
        except Exception:
            pass
        
        # Highlight if selected
        if self.selected_patient == patient:
            pygame.draw.rect(self.screen, YELLOW, (x - 2, y - 2, width + 4, height + 4), 3)
    
    def draw_bed(self, bed, x, y, width=120, height=120):
        """Draw a bed icon"""
        # Record for nurse animation targeting
        self.bed_positions[bed] = (x, y, width, height)
        # Try to draw sprite; fallback to rectangle if missing
        if self.bed_sprite_raw or self.patient_in_bed_sprite_raw:
            if bed.available:
                # draw empty bed
                if self.bed_sprite_raw:
                    key = (width, height)
                    if key not in self._bed_sprite_cache:
                        self._bed_sprite_cache[key] = pygame.transform.smoothscale(self.bed_sprite_raw, (width, height))
                    sprite = self._bed_sprite_cache[key]
                    self.screen.blit(sprite, (x, y))
                else:
                    pygame.draw.rect(self.screen, LIGHT_GRAY, (x, y, width, height))
                pygame.draw.rect(self.screen, GREEN, (x, y, width, height), 2)
            else:
                # occupied bed -> draw patient-in-bed sprite if available
                if self.patient_in_bed_sprite_raw:
                    # Scale a bit larger than bed and center
                    sw = max(1, int(width * self.patient_in_bed_scale))
                    sh = max(1, int(height * self.patient_in_bed_scale))
                    key2 = (sw, sh)
                    if key2 not in self._patient_in_bed_sprite_cache:
                        self._patient_in_bed_sprite_cache[key2] = pygame.transform.smoothscale(self.patient_in_bed_sprite_raw, (sw, sh))
                    occ_sprite = self._patient_in_bed_sprite_cache[key2]
                    draw_x = x + (width - sw) // 2
                    draw_y = y + (height - sh) // 2
                    self.screen.blit(occ_sprite, (draw_x, draw_y))
                else:
                    # fallback rectangle for occupied
                    pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))
                pygame.draw.rect(self.screen, RED, (x, y, width, height), 2)
        else:
            if bed.available:
                color = LIGHT_GRAY
            else:
                color = DARK_GRAY
            pygame.draw.rect(self.screen, color, (x, y, width, height))
            pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
            # Bed label
            label = "BED" if bed.available else "OCCUPIED"
            label_text = self.small_font.render(label, True, BLACK if bed.available else WHITE)
            text_rect = label_text.get_rect(center=(x + width // 2, y + height // 2))
            self.screen.blit(label_text, text_rect)
        # If bed is occupied, draw the patient's life bar on top of the bed
        if not bed.available:
            try:
                patient = next(p for p in self.game.patients if p.assigned_bed == bed)
                bar_width = int((patient.severity / 100.0) * width)
                bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
                pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
                # Optional: small id tag in corner
                id_text = self.small_font.render(f"#{patient.id}", self.retro_antialias, WHITE)
                self.screen.blit(id_text, (x + 4, y + 4))
                # Type badge
                t = patient.patient_type
                t_letter = "R" if t == PatientType.RESPIRATORY else "C" if t == PatientType.CARDIAC else "T"
                badge = self.small_font.render(t_letter, self.retro_antialias, BLACK)
                bw, bh = badge.get_size()
                pad = 4
                bx = x + width - bw - pad - 2
                by = y + 2
                pygame.draw.rect(self.screen, YELLOW, (bx - 2, by - 2, bw + 4, bh + 4))
                self.screen.blit(badge, (bx, by))
            except StopIteration:
                pass
    
    def draw_nurse(self, nurse, x, y, size=40):
        """Draw a nurse icon at the given coordinates."""
        draw_x, draw_y = x, y
        # Draw sprite if available, else fallback circle
        if self.nurse_sprite_raw:
            key = (size, size)
            if key not in self._nurse_sprite_cache:
                self._nurse_sprite_cache[key] = pygame.transform.smoothscale(self.nurse_sprite_raw, (size, size))
            sprite = self._nurse_sprite_cache[key]
            self.screen.blit(sprite, (draw_x, draw_y))
        else:
            color = GREEN if nurse.available else RED
            pygame.draw.circle(self.screen, color, (draw_x + size // 2, draw_y + size // 2), size // 2)
            pygame.draw.circle(self.screen, BLACK, (draw_x + size // 2, draw_y + size // 2), size // 2, 2)

    def _get_nurse_target(self, nurse, size=None):
        if size is None:
            size = self.nurse_size
        """Compute the target (x, y) for a nurse: patient location if assigned, else station."""
        # If a pending assignment exists for this nurse, head to that bed/vent
        for task in self.pending_assignments:
            if task.get('nurse') == nurse:
                if 'bed' in task and task['bed'] in self.bed_positions:
                    tx, ty, tw, th = self.bed_positions[task['bed']]
                    return tx + tw - size, ty
                if 'vent' in task and task['vent'] in self.vent_positions:
                    vx, vy, vw, vh = self.vent_positions[task['vent']]
                    return vx, vy
        # If assigned, target the patient's bed/vent center
        if not nurse.available:
            assigned_patient = None
            for p in self.game.patients:
                if p.assigned_nurse == nurse:
                    assigned_patient = p
                    break
            if assigned_patient is not None:
                target_rect = None
                if assigned_patient.assigned_ventilator and assigned_patient.assigned_ventilator in self.vent_positions:
                    target_rect = self.vent_positions[assigned_patient.assigned_ventilator]
                elif assigned_patient.assigned_bed and assigned_patient.assigned_bed in self.bed_positions:
                    target_rect = self.bed_positions[assigned_patient.assigned_bed]
                if target_rect:
                    tx, ty, tw, th = target_rect
                    # Aim near top-right corner
                    return tx + tw - size, ty
        # Otherwise, go to station
        return self.nurse_stations.get(nurse, (850, self.bed_area_y + 50))

    def _row_corridor_y(self):
        """
        Return a safe Y corridor between bed rows to avoid walking through beds.
        Assumes two rows laid out by 120px height tiles with a gap.
        """
        # Row 0 top is self.bed_area_y + 50, row 1 top is +120
        return self.bed_area_y + 50 + 120 + 10  # 10px gap between rows

    def _plan_path(self, cur, target):
        """
        Plan a simple 2-turn Manhattan path using a safe corridor between rows.
        cur, target: (x, y)
        """
        cx, cy = cur
        tx, ty = target
        corridor_y = self._row_corridor_y()
        path = []
        # Move vertically to corridor first if not already near it
        if abs(cy - corridor_y) > 2:
            path.append((cx, corridor_y))
        # Move horizontally along corridor to target x
        if abs(tx - cx) > 2:
            path.append((tx, corridor_y))
        # Move vertically down/up to target y
        if abs(ty - corridor_y) > 2:
            path.append((tx, ty))
        return path

    def _update_nurse_positions(self, size=None):
        """Move nurses toward their targets each tick with simple corridor pathfinding."""
        if size is None:
            size = self.nurse_size
        for nurse in self.game.nurses:
            target_x, target_y = self._get_nurse_target(nurse, size=size)
            # Initialize position at station if unknown
            if nurse not in self.nurse_positions:
                self.nurse_positions[nurse] = (target_x, target_y)
                self.nurse_paths[nurse] = []
                continue
            cur_x, cur_y = self.nurse_positions[nurse]

            # Recompute path if target changed significantly or path empty
            if nurse not in self.nurse_paths:
                self.nurse_paths[nurse] = []
            if not self.nurse_paths[nurse] or self.nurse_paths[nurse][-1] != (target_x, target_y):
                self.nurse_paths[nurse] = self._plan_path((cur_x, cur_y), (target_x, target_y))

            # Advance toward next waypoint
            if self.nurse_paths[nurse]:
                wx, wy = self.nurse_paths[nurse][0]
            else:
                wx, wy = target_x, target_y

            dx = wx - cur_x
            dy = wy - cur_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 1:
                # Reached waypoint
                if self.nurse_paths[nurse]:
                    self.nurse_paths[nurse].pop(0)
                self.nurse_positions[nurse] = (wx, wy)
                continue
            step = min(self.nurse_speed, dist)
            if dist > 0:
                new_x = cur_x + dx / dist * step
                new_y = cur_y + dy / dist * step
            else:
                new_x, new_y = wx, wy
            self.nurse_positions[nurse] = (new_x, new_y)

        # Check pending assignments: if nurse reached target (bed or vent), perform assignment now
        if self.pending_assignments:
            remaining = []
            for task in self.pending_assignments:
                nurse = task['nurse']
                patient = task['patient']
                nx, ny = self.nurse_positions.get(nurse, (None, None))
                if nx is None:
                    remaining.append(task)
                    continue
                # Bed-targeted task
                if 'bed' in task:
                    bed = task['bed']
                    if bed in self.bed_positions:
                        bx, by, bw, bh = self.bed_positions[bed]
                        reached_rect = (bx - 4) <= nx <= (bx + bw + 4) and (by - 4) <= ny <= (by + bh + 4)
                        target_x = bx + bw - size
                        target_y = by
                        dx_t = nx - target_x
                        dy_t = ny - target_y
                        reached_target = (dx_t * dx_t + dy_t * dy_t) ** 0.5 <= 8
                        if reached_rect or reached_target:
                            try:
                                if hasattr(self.game, "assign_patient_to_specific_bed"):
                                    self.game.assign_patient_to_specific_bed(patient, bed, nurse)
                                else:
                                    self.game.assign_patient_to_bed(patient)
                            except Exception:
                                self.game.assign_patient_to_bed(patient)
                            continue  # completed
                    remaining.append(task)
                    continue
                # Vent-targeted task
                if 'vent' in task:
                    vent = task['vent']
                    if vent in self.vent_positions:
                        vx, vy, vw, vh = self.vent_positions[vent]
                        reached_rect = (vx - 4) <= nx <= (vx + vw + 4) and (vy - 4) <= ny <= (vy + vh + 4)
                        if reached_rect:
                            try:
                                self.game.assign_patient_to_ventilator(patient)
                            except Exception:
                                self.game.assign_patient_to_ventilator(patient)
                            continue  # completed
                    remaining.append(task)
                    continue
            self.pending_assignments = remaining
    
    def draw_ventilator(self, vent, x, y, width=100, height=60):
        """Draw a ventilator icon"""
        color = LIGHT_GRAY if vent.available else DARK_GRAY
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        # Ventilator label
        label = "VENT" if vent.available else "IN USE"
        label_text = self.small_font.render(label, True, BLACK if vent.available else WHITE)
        text_rect = label_text.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(label_text, text_rect)
        # Record for nurse animation targeting
        self.vent_positions[vent] = (x, y, width, height)
    
    def draw_ui_panel(self):
        """Draw the UI information panel"""
        panel_x = self.ui_panel_x
        panel_y = 50
        
        # Background
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, self.ui_panel_width, self.height - 100))
        pygame.draw.rect(self.screen, BLACK, (panel_x, panel_y, self.ui_panel_width, self.height - 100), 2)
        
        y_offset = panel_y + 20
        
        # Title
        title = self.large_font.render("SIMICU", self.retro_antialias, WHITE)
        self.screen.blit(title, (panel_x + 20, y_offset))
        y_offset += 50
        
        # Score
        score = self.game.get_score()
        score_text = self.font.render(f"Saved: {score['patients_saved']}", self.retro_antialias, GREEN)
        self.screen.blit(score_text, (panel_x + 20, y_offset))
        y_offset += 30
        
        lost_text = self.font.render(f"Lost: {score['patients_lost']}", self.retro_antialias, RED)
        self.screen.blit(lost_text, (panel_x + 20, y_offset))
        y_offset += 30
        
        # Tick
        tick_text = self.font.render(f"Tick: {self.game.tick}", self.retro_antialias, WHITE)
        self.screen.blit(tick_text, (panel_x + 20, y_offset))
        y_offset += 40
        
        # Speed/FPS display
        speed_text = self.font.render(f"FPS: {self.fps}", self.retro_antialias, WHITE)
        self.screen.blit(speed_text, (panel_x + 20, y_offset))
        y_offset += 30
        rate_text = self.small_font.render(f"Tick every {self.update_every_n_frames} frame(s)", self.retro_antialias, WHITE)
        self.screen.blit(rate_text, (panel_x + 20, y_offset))
        y_offset += 25
        
        # Resources
        resources_title = self.font.render("Resources:", self.retro_antialias, WHITE)
        self.screen.blit(resources_title, (panel_x + 20, y_offset))
        y_offset += 30
        
        nurses_text = self.font.render(f"Nurses: {self.game.free_nurses}/{self.game.num_nurses}", self.retro_antialias, WHITE)
        self.screen.blit(nurses_text, (panel_x + 20, y_offset))
        y_offset += 25
        
        beds_text = self.font.render(f"Beds: {self.game.free_beds}/{self.game.num_beds}", self.retro_antialias, WHITE)
        self.screen.blit(beds_text, (panel_x + 20, y_offset))
        y_offset += 25
        
        vents_text = self.font.render(f"Vents: {self.game.free_vents}/{self.game.num_ventilators}", self.retro_antialias, WHITE)
        self.screen.blit(vents_text, (panel_x + 20, y_offset))
        y_offset += 40
        
        # Instructions
        instructions = [
            "INSTRUCTIONS:",
            "1. Click patient to select",
            "2. Click bed to assign",
            "3. Click vent for critical",
            "+/-: Speed up/down",
            "[ / ]: Slow/Fast ticks",
            "SPACE: Pause/Resume",
            "R: Reset game"
        ]
        
        for instruction in instructions:
            inst_text = self.small_font.render(instruction, self.retro_antialias, YELLOW)
            self.screen.blit(inst_text, (panel_x + 20, y_offset))
            y_offset += 20
        
        # Pause indicator
        if self.paused:
            pause_text = self.large_font.render("PAUSED", self.retro_antialias, YELLOW)
            text_rect = pause_text.get_rect(center=(panel_x + self.ui_panel_width // 2, self.height - 50))
            self.screen.blit(pause_text, text_rect)
    
    def handle_click(self, pos):
        """Handle mouse click"""
        if self.input_cooldown_ticks > 0:
            return
        x, y = pos
        
        # Check if clicking in waiting room
        if y >= self.waiting_room_y and y <= self.waiting_room_y + self.waiting_room_height:
            waiting_patients = self.game.get_waiting_patients()
            for i, patient in enumerate(waiting_patients):
                patient_x = 50 + i * 120
                patient_y = self.waiting_room_y + 20
                if (patient_x <= x <= patient_x + 100 and 
                    patient_y <= y <= patient_y + 80):
                    self.selected_patient = patient
                    return
        
        # Check if clicking on beds
        if y >= self.bed_area_y and y <= self.bed_area_y + self.bed_area_height:
            bed_x_start = 200
            bed_y = self.bed_area_y + 50
            for i, bed in enumerate(self.game.beds):
                bed_x = bed_x_start + (i % 4) * 150
                bed_y_offset = (i // 4) * 120
                if (bed_x <= x <= bed_x + 120 and 
                    bed_y + bed_y_offset <= y <= bed_y + bed_y_offset + 120):
                    if self.selected_patient and bed.available:
                        # Find nearest available nurse (by current animated position), else ignore
                        available_nurses = [n for n in self.game.nurses if n.available]
                        if not available_nurses:
                            return
                        # Compute bed target point
                        bx, by, bw, bh = bed_x, bed_y + bed_y_offset, 120, 120
                        target_x = bx + bw - self.nurse_size
                        target_y = by
                        # Ensure nurse positions initialized
                        for n in available_nurses:
                            if n not in self.nurse_positions:
                                self.nurse_positions[n] = self.nurse_stations.get(n, (850, self.bed_area_y + 50))
                        # Pick nearest
                        def dist2(n):
                            nx, ny = self.nurse_positions.get(n, (target_x, target_y))
                            dx = nx - target_x
                            dy = ny - target_y
                            return dx * dx + dy * dy
                        nearest = min(available_nurses, key=dist2)
                        # Queue assignment: nurse will run to bed, then we assign
                        self.pending_assignments.append({'nurse': nearest, 'patient': self.selected_patient, 'bed': bed})
                        # Small input cooldown to simulate human latency
                        self.input_cooldown_ticks = 8
                        self.selected_patient = None
                    return
            
            # Check ventilators (now on the left side)
            vent_x_start = 50
            for i, vent in enumerate(self.game.ventilators):
                vent_x = vent_x_start
                vent_y = self.bed_area_y + 50 + i * 80
                if (vent_x <= x <= vent_x + 100 and 
                    vent_y <= y <= vent_y + 60):
                    if self.selected_patient and vent.available:
                        # Queue ventilator assignment with nearest available nurse.
                        available_nurses = [n for n in self.game.nurses if n.available]
                        if not available_nurses:
                            return
                        # Target current patient's bed if any, else target this ventilator panel
                        if self.selected_patient.assigned_bed and self.selected_patient.assigned_bed in self.bed_positions:
                            tx, ty, tw, th = self.bed_positions[self.selected_patient.assigned_bed]
                            target_x = tx + tw - self.nurse_size
                            target_y = ty
                        else:
                            target_x = vent_x
                            target_y = vent_y
                        for n in available_nurses:
                            if n not in self.nurse_positions:
                                self.nurse_positions[n] = self.nurse_stations.get(n, (850, self.bed_area_y + 50))
                        def dist2(n):
                            nx, ny = self.nurse_positions.get(n, (target_x, target_y))
                            dx = nx - target_x
                            dy = ny - target_y
                            return dx * dx + dy * dy
                        nearest = min(available_nurses, key=dist2)
                        # Queue a 'vent' pending assignment; assignment will occur on arrival
                        self.pending_assignments.append({'nurse': nearest, 'patient': self.selected_patient, 'vent': vent})
                        self.input_cooldown_ticks = 8
                        self.selected_patient = None
                    return
    
    def draw(self):
        """Draw the entire game screen"""
        self.screen.fill(BLACK)
        if self.show_intro:
            return self.draw_intro_overlay()
        
        # Draw waiting room
        waiting_title = self.font.render("WAITING ROOM", self.retro_antialias, WHITE)
        self.screen.blit(waiting_title, (50, 20))
        # Background image for waiting room
        wr_x, wr_y, wr_w, wr_h = 50, self.waiting_room_y, 800, self.waiting_room_height
        if self.waiting_bg_raw:
            key = (wr_w, wr_h)
            if key not in self._waiting_bg_cache:
                self._waiting_bg_cache[key] = pygame.transform.smoothscale(self.waiting_bg_raw, (wr_w, wr_h))
            self.screen.blit(self._waiting_bg_cache[key], (wr_x, wr_y))
        else:
            pygame.draw.rect(self.screen, DARK_GRAY, (wr_x, wr_y, wr_w, wr_h))
        pygame.draw.rect(self.screen, WHITE, (wr_x, wr_y, wr_w, wr_h), 2)
        
        # Draw waiting patients
        waiting_patients = self.game.get_waiting_patients()
        for i, patient in enumerate(waiting_patients[:6]):  # Show up to 6
            # In waiting room show only health bar (no box/id/status)
            self.draw_patient(patient, 50 + i * 120, self.waiting_room_y + 20, minimal=True)
        
        # Draw bed area (shifted right to make room for ventilators on the left)
        bed_title = self.font.render("ICU BEDS", self.retro_antialias, WHITE)
        self.screen.blit(bed_title, (200, self.bed_area_y - 30))
        
        for i, bed in enumerate(self.game.beds):
            bed_x = 200 + (i % 4) * 150
            bed_y = self.bed_area_y + 50 + (i // 4) * 120
            self.draw_bed(bed, bed_x, bed_y)
            
            # Draw patient in bed if occupied
            # If we have a patient-in-bed sprite, the bed already shows patient;
            # otherwise, overlay a smaller patient icon.
            if not getattr(self, "patient_in_bed_sprite_raw", None):
                for patient in self.game.patients:
                    if patient.assigned_bed == bed:
                        self.draw_patient(patient, bed_x + 10, bed_y - 20, 100, 60)
        
        # Draw ventilators (moved to the left side)
        vent_title = self.font.render("VENTILATORS", self.retro_antialias, WHITE)
        self.screen.blit(vent_title, (50, self.bed_area_y - 30))
        
        for i, vent in enumerate(self.game.ventilators):
            vent_x = 50
            vent_y = self.bed_area_y + 50 + i * 80
            self.draw_ventilator(vent, vent_x, vent_y)
            
            # Draw patient on ventilator if occupied
            for patient in self.game.patients:
                if patient.assigned_ventilator == vent:
                    self.draw_patient(patient, vent_x + 10, vent_y - 20, 100, 60)
        
        # Draw nurses (animated between station and patient)
        nurse_title = self.font.render("NURSES", self.retro_antialias, WHITE)
        self.screen.blit(nurse_title, (850, self.bed_area_y - 30))
        # Define stations and update positions
        for i, nurse in enumerate(self.game.nurses):
            station_x = 850
            station_y = self.bed_area_y + 50 + i * 56
            self.nurse_stations[nurse] = (station_x, station_y)
        # Move nurses toward their targets
        self._update_nurse_positions(size=self.nurse_size)
        # Draw at current positions
        for nurse in self.game.nurses:
            nx, ny = self.nurse_positions.get(nurse, self.nurse_stations[nurse])
            self.draw_nurse(nurse, int(nx), int(ny), self.nurse_size)
        
        # Draw UI panel
        self.draw_ui_panel()
        
        pygame.display.flip()

    def draw_intro_overlay(self):
        """Intro screen with title, description, and Play button."""
        self.screen.fill(BLACK)
        title = self.title_font.render("SIMICU - RETRO MODE", self.retro_antialias, YELLOW)
        subtitle = self.large_font.render("HUMAN VS AI ICU MANAGEMENT", self.retro_antialias, WHITE)
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 120))
        self.screen.blit(subtitle, ((self.width - subtitle.get_width()) // 2, 165))

        lines = [
            "Goal: Save as many patients as possible with limited beds, nurses, and ventilators.",
            "Patients worsen while waiting; treatment has setup delays; step-down beds cause ICU gridlock.",
            "",
            "How to Play:",
            " - Click a patient in the waiting room to select.",
            " - Click an available bed to admit, or a ventilator to escalate.",
            " - SPACE: Pause/Resume   R: Reset",
        ]
        y = 220
        for line in lines:
            t = self.font.render(line, self.retro_antialias, LIGHT_GRAY)
            self.screen.blit(t, (100, y))
            y += 24

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
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        if self.show_intro:
                            if hasattr(self, "_intro_button"):
                                bx, by, bw, bh = self._intro_button
                                mx, my = event.pos
                                if bx <= mx <= bx + bw and by <= my <= by + bh:
                                    self.show_intro = False
                            continue
                        self.handle_click(event.pos)
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
                            self.game.reset()
                            self.selected_patient = None
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.fps = min(30, self.fps + 1)
                    elif event.key == pygame.K_MINUS:
                        self.fps = max(2, self.fps - 1)
                    elif event.key == pygame.K_LEFTBRACKET:
                        self.update_every_n_frames = min(10, self.update_every_n_frames + 1)
                    elif event.key == pygame.K_RIGHTBRACKET:
                        self.update_every_n_frames = max(1, self.update_every_n_frames - 1)
            
            if not self.paused:
                # Update game
                if not self.show_intro:
                    self._frame_counter = (self._frame_counter + 1) % self.update_every_n_frames
                    if self._frame_counter == 0:
                        for _ in range(self.tick_speed):
                            self.game.update_tick()
                # Decrement human input cooldown
                if self.input_cooldown_ticks > 0:
                    self.input_cooldown_ticks -= 1
            
            self.draw()
            self.clock.tick(self.fps)  # Lower FPS for slower, retro feel
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = RetroSimICU()
    game.run()

