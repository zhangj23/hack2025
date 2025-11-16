"""
Modern AI Mode - Run the trained RL agent
This demonstrates the AI agent managing the ICU automatically.
"""

import pygame
import sys
import numpy as np
from stable_baselines3 import PPO
from sim_icu_env import SimICUEnv
from sim_icu_logic import PatientStatus
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
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.large_font = pygame.font.Font(None, 36)
        
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

        # Patient sprite (standing)
        base_dir = os.path.dirname(__file__)
        standing_path = os.path.join(base_dir, "sprites", "standing.png")
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
    
    def draw_patient(self, patient, x, y, width=100, height=80, minimal=False):
        """Draw a patient icon (sprite if available).
        minimal=True renders only the life bar (used for waiting room).
        """
        if minimal:
            # Waiting room: show standing sprite (if available) + life bar + number only.
            if getattr(self, "patient_sprite_raw", None):
                tw = max(1, int(width * self.waiting_sprite_scale_w))
                th = max(1, int(height * self.waiting_sprite_scale_h))
                key = (tw, th, "waiting")
                if key not in self._patient_sprite_cache:
                    self._patient_sprite_cache[key] = pygame.transform.smoothscale(self.patient_sprite_raw, (tw, th))
                sprite = self._patient_sprite_cache[key]
                draw_x = x + (width - tw) // 2
                draw_y = y + (height - th) // 2
                self.screen.blit(sprite, (draw_x, draw_y))
            bar_width = int((patient.severity / 100.0) * width)
            bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
            pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
            life_value = int(round(patient.severity))
            value_text = self.small_font.render(f"{life_value}", True, WHITE)
            self.screen.blit(value_text, (x + 5, y + 5))
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
    
    def draw_bed(self, bed, x, y, width=120, height=100):
        """Draw a bed icon (uses patient.png when occupied)."""
        if not bed.available and getattr(self, "patient_in_bed_sprite_raw", None):
            sw = max(1, int(width * self.patient_in_bed_scale))
            sh = max(1, int(height * self.patient_in_bed_scale))
            key = (sw, sh)
            if key not in self._patient_in_bed_sprite_cache:
                self._patient_in_bed_sprite_cache[key] = pygame.transform.smoothscale(self.patient_in_bed_sprite_raw, (sw, sh))
            draw_x = x + (width - sw) // 2
            draw_y = y + (height - sh) // 2
            self.screen.blit(self._patient_in_bed_sprite_cache[key], (draw_x, draw_y))
            pygame.draw.rect(self.screen, RED, (x, y, width, height), 2)
            return

        # Fallback rectangles for empty bed or when sprite missing
        color = LIGHT_GRAY if bed.available else DARK_GRAY
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        label = "BED" if bed.available else "OCCUPIED"
        label_text = self.small_font.render(label, True, BLACK if bed.available else WHITE)
        text_rect = label_text.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(label_text, text_rect)
    
    def draw_nurse(self, nurse, x, y, size=40):
        """Draw a nurse icon"""
        color = GREEN if nurse.available else RED
        pygame.draw.circle(self.screen, color, (x + size // 2, y + size // 2), size // 2)
        pygame.draw.circle(self.screen, BLACK, (x + size // 2, y + size // 2), size // 2, 2)
        
        label = "N" if nurse.available else "BUSY"
        label_text = self.small_font.render(label, True, WHITE)
        text_rect = label_text.get_rect(center=(x + size // 2, y + size // 2))
        self.screen.blit(label_text, text_rect)
    
    def draw_ventilator(self, vent, x, y, width=100, height=60):
        """Draw a ventilator icon"""
        color = LIGHT_GRAY if vent.available else DARK_GRAY
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        label = "VENT" if vent.available else "IN USE"
        label_text = self.small_font.render(label, True, BLACK if vent.available else WHITE)
        text_rect = label_text.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(label_text, text_rect)
    
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
            "+/-: Speed up/down",
            "ESC: Quit"
        ]
        
        for control in controls:
            ctrl_text = self.small_font.render(control, True, YELLOW)
            self.screen.blit(ctrl_text, (panel_x + 20, y_offset))
            y_offset += 20
        
        # Pause indicator
        if self.paused:
            pause_text = self.large_font.render("PAUSED", True, YELLOW)
            text_rect = pause_text.get_rect(center=(panel_x + self.ui_panel_width // 2, self.height - 50))
            self.screen.blit(pause_text, text_rect)
    
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
        waiting_patients = self.env.game.get_waiting_patients()
        for i, patient in enumerate(waiting_patients[:6]):  # Show up to 6
            self.draw_patient(patient, 50 + i * 120, self.waiting_room_y + 20, minimal=True)
        
        # Draw bed area
        bed_title = self.font.render("ICU BEDS", True, WHITE)
        self.screen.blit(bed_title, (50, self.bed_area_y - 30))
        
        for i, bed in enumerate(self.env.game.beds):
            bed_x = 50 + (i % 4) * 150
            bed_y = self.bed_area_y + 50 + (i // 4) * 120
            self.draw_bed(bed, bed_x, bed_y)
            
            # Draw patient in bed if occupied
            if not getattr(self, "patient_in_bed_sprite_raw", None):
                for patient in self.env.game.patients:
                    if patient.assigned_bed == bed:
                        self.draw_patient(patient, bed_x + 10, bed_y - 20, 100, 60)
        
        # Draw ventilators
        vent_title = self.font.render("VENTILATORS", True, WHITE)
        self.screen.blit(vent_title, (700, self.bed_area_y - 30))
        
        for i, vent in enumerate(self.env.game.ventilators):
            vent_x = 700
            vent_y = self.bed_area_y + 50 + i * 80
            self.draw_ventilator(vent, vent_x, vent_y)
            
            # Draw patient on ventilator if occupied
            for patient in self.env.game.patients:
                if patient.assigned_ventilator == vent:
                    self.draw_patient(patient, vent_x + 10, vent_y - 20, 100, 60)
        
        # Draw nurses
        nurse_title = self.font.render("NURSES", True, WHITE)
        self.screen.blit(nurse_title, (850, self.bed_area_y - 30))
        for i, nurse in enumerate(self.env.game.nurses):
            self.draw_nurse(nurse, 850, self.bed_area_y + 50 + i * 50, 40)
        
        # Draw UI panel
        self.draw_ui_panel()
        
        pygame.display.flip()
    
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
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.obs, self.info = self.env.reset()
                        self.episode += 1
                        done = False
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.speed = min(10, self.speed + 1)
                    elif event.key == pygame.K_MINUS:
                        self.speed = max(1, self.speed - 1)
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            if not self.paused and not done:
                # Let AI make decisions
                for _ in range(self.speed):
                    action, _ = self.model.predict(self.obs, deterministic=True)
                    self.obs, reward, terminated, truncated, self.info = self.env.step(action)
                    done = terminated or truncated
                    
                    if done:
                        # Show final score
                        score = self.env.game.get_score()
                        print(f"\nEpisode {self.episode} Complete!")
                        print(f"  Saved: {score['patients_saved']}")
                        print(f"  Lost: {score['patients_lost']}")
                        total = score['patients_saved'] + score['patients_lost']
                        if total > 0:
                            print(f"  Success Rate: {(score['patients_saved'] / total * 100):.1f}%")
                        
                        # Auto-reset after a short delay
                        import time
                        time.sleep(2)
                        self.obs, self.info = self.env.reset()
                        self.episode += 1
                        done = False
                        break
            
            self.draw()
            self.clock.tick(10)  # 10 FPS
        
        pygame.quit()
        sys.exit()


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

