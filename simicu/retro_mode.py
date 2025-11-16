"""
Retro Player Mode - Pygame Frontend
A pixel-art style interface for human players to manage the ICU.
"""

import pygame
import sys
import os
import math
from sim_icu_logic import SimICU, PatientStatus


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
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.large_font = pygame.font.Font(None, 36)
        
        # Initialize game
        self.game = SimICU()
        self.selected_patient = None
        self.tick_speed = 1  # Ticks per frame
        self.paused = False

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

        # Object position maps for animation targets
        self.bed_positions = {}   # bed -> (x, y, w, h)
        self.vent_positions = {}  # vent -> (x, y, w, h)

        # Nurse movement state
        self.nurse_positions = {}  # nurse -> (x, y)
        self.nurse_stations = {}   # nurse -> (x, y)
        self.nurse_speed = 30      # pixels per tick
        self.nurse_size = 48       # draw size (bigger nurse)
        self.nurse_paths = {}      # nurse -> [(x, y), ...] waypoints
        
        # UI layout
        self.waiting_room_y = 50
        self.waiting_room_height = 200
        self.bed_area_y = 300
        self.bed_area_height = 400
        self.ui_panel_x = 900
        self.ui_panel_width = 300
    
    def draw_patient(self, patient, x, y, width=100, height=80):
        """Draw a patient icon"""
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
        bar_color = RED if patient.severity > 70 else ORANGE if patient.severity > 40 else YELLOW
        pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
        
        # Patient ID
        id_text = self.small_font.render(f"#{patient.id}", True, WHITE)
        self.screen.blit(id_text, (x + 5, y + 5))
        
        # Status text
        status_text = self.small_font.render(patient.status.value, True, WHITE)
        self.screen.blit(status_text, (x + 5, y + 20))
        
        # Severity number
        severity_text = self.small_font.render(f"{patient.severity}", True, WHITE)
        self.screen.blit(severity_text, (x + 5, y + 35))
        
        # Highlight if selected
        if self.selected_patient == patient:
            pygame.draw.rect(self.screen, YELLOW, (x - 2, y - 2, width + 4, height + 4), 3)
    
    def draw_bed(self, bed, x, y, width=120, height=120):
        """Draw a bed icon"""
        # Record for nurse animation targeting
        self.bed_positions[bed] = (x, y, width, height)
        # Try to draw sprite; fallback to rectangle if missing
        if self.bed_sprite_raw:
            key = (width, height)
            if key not in self._bed_sprite_cache:
                self._bed_sprite_cache[key] = pygame.transform.smoothscale(self.bed_sprite_raw, (width, height))
            sprite = self._bed_sprite_cache[key]
            self.screen.blit(sprite, (x, y))
            # Overlay availability tint/outline
            border_color = GREEN if bed.available else RED
            pygame.draw.rect(self.screen, border_color, (x, y, width, height), 2)
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
        title = self.large_font.render("SIMICU", True, WHITE)
        self.screen.blit(title, (panel_x + 20, y_offset))
        y_offset += 50
        
        # Score
        score = self.game.get_score()
        score_text = self.font.render(f"Saved: {score['patients_saved']}", True, GREEN)
        self.screen.blit(score_text, (panel_x + 20, y_offset))
        y_offset += 30
        
        lost_text = self.font.render(f"Lost: {score['patients_lost']}", True, RED)
        self.screen.blit(lost_text, (panel_x + 20, y_offset))
        y_offset += 30
        
        # Tick
        tick_text = self.font.render(f"Tick: {self.game.tick}", True, WHITE)
        self.screen.blit(tick_text, (panel_x + 20, y_offset))
        y_offset += 40
        
        # Resources
        resources_title = self.font.render("Resources:", True, WHITE)
        self.screen.blit(resources_title, (panel_x + 20, y_offset))
        y_offset += 30
        
        nurses_text = self.font.render(f"Nurses: {self.game.free_nurses}/{self.game.num_nurses}", True, WHITE)
        self.screen.blit(nurses_text, (panel_x + 20, y_offset))
        y_offset += 25
        
        beds_text = self.font.render(f"Beds: {self.game.free_beds}/{self.game.num_beds}", True, WHITE)
        self.screen.blit(beds_text, (panel_x + 20, y_offset))
        y_offset += 25
        
        vents_text = self.font.render(f"Vents: {self.game.free_vents}/{self.game.num_ventilators}", True, WHITE)
        self.screen.blit(vents_text, (panel_x + 20, y_offset))
        y_offset += 40
        
        # Instructions
        instructions = [
            "INSTRUCTIONS:",
            "1. Click patient to select",
            "2. Click bed to assign",
            "3. Click vent for critical",
            "SPACE: Pause/Resume",
            "R: Reset game"
        ]
        
        for instruction in instructions:
            inst_text = self.small_font.render(instruction, True, YELLOW)
            self.screen.blit(inst_text, (panel_x + 20, y_offset))
            y_offset += 20
        
        # Pause indicator
        if self.paused:
            pause_text = self.large_font.render("PAUSED", True, YELLOW)
            text_rect = pause_text.get_rect(center=(panel_x + self.ui_panel_width // 2, self.height - 50))
            self.screen.blit(pause_text, text_rect)
    
    def handle_click(self, pos):
        """Handle mouse click"""
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
            bed_x_start = 50
            bed_y = self.bed_area_y + 50
            for i, bed in enumerate(self.game.beds):
                bed_x = bed_x_start + (i % 4) * 150
                bed_y_offset = (i // 4) * 120
                if (bed_x <= x <= bed_x + 120 and 
                    bed_y + bed_y_offset <= y <= bed_y + bed_y_offset + 120):
                    if self.selected_patient and bed.available:
                        self.game.assign_patient_to_bed(self.selected_patient)
                        self.selected_patient = None
                    return
            
            # Check ventilators (to the right of beds)
            vent_x_start = 700
            for i, vent in enumerate(self.game.ventilators):
                vent_x = vent_x_start
                vent_y = self.bed_area_y + 50 + i * 80
                if (vent_x <= x <= vent_x + 100 and 
                    vent_y <= y <= vent_y + 60):
                    if self.selected_patient and vent.available:
                        self.game.assign_patient_to_ventilator(self.selected_patient)
                        self.selected_patient = None
                    return
    
    def draw(self):
        """Draw the entire game screen"""
        self.screen.fill(BLACK)
        
        # Draw waiting room
        waiting_title = self.font.render("WAITING ROOM", True, WHITE)
        self.screen.blit(waiting_title, (50, 20))
        pygame.draw.rect(self.screen, DARK_GRAY, 
                        (50, self.waiting_room_y, 800, self.waiting_room_height))
        pygame.draw.rect(self.screen, WHITE, 
                        (50, self.waiting_room_y, 800, self.waiting_room_height), 2)
        
        # Draw waiting patients
        waiting_patients = self.game.get_waiting_patients()
        for i, patient in enumerate(waiting_patients[:6]):  # Show up to 6
            self.draw_patient(patient, 50 + i * 120, self.waiting_room_y + 20)
        
        # Draw bed area
        bed_title = self.font.render("ICU BEDS", True, WHITE)
        self.screen.blit(bed_title, (50, self.bed_area_y - 30))
        
        for i, bed in enumerate(self.game.beds):
            bed_x = 50 + (i % 4) * 150
            bed_y = self.bed_area_y + 50 + (i // 4) * 120
            self.draw_bed(bed, bed_x, bed_y)
            
            # Draw patient in bed if occupied
            for patient in self.game.patients:
                if patient.assigned_bed == bed:
                    self.draw_patient(patient, bed_x + 10, bed_y - 20, 100, 60)
        
        # Draw ventilators
        vent_title = self.font.render("VENTILATORS", True, WHITE)
        self.screen.blit(vent_title, (700, self.bed_area_y - 30))
        
        for i, vent in enumerate(self.game.ventilators):
            vent_x = 700
            vent_y = self.bed_area_y + 50 + i * 80
            self.draw_ventilator(vent, vent_x, vent_y)
            
            # Draw patient on ventilator if occupied
            for patient in self.game.patients:
                if patient.assigned_ventilator == vent:
                    self.draw_patient(patient, vent_x + 10, vent_y - 20, 100, 60)
        
        # Draw nurses (animated between station and patient)
        nurse_title = self.font.render("NURSES", True, WHITE)
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
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.game.reset()
                        self.selected_patient = None
            
            if not self.paused:
                # Update game
                for _ in range(self.tick_speed):
                    self.game.update_tick()
            
            self.draw()
            self.clock.tick(10)  # 10 FPS for retro feel
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = RetroSimICU()
    game.run()

