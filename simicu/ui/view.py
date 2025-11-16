import os
import pygame
from typing import Optional, Dict, Tuple, List
from sim_icu_logic import SimICU, PatientStatus, PatientType

GREEN = (50, 205, 50)
BLUE = (30, 144, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)
LIGHT_GRAY = (192, 192, 192)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
RED = (220, 20, 60)
DARK_GRAY = (64, 64, 64)


class SimICUView:
    """
    Shared UI view/controller for Retro and Modern modes.
    Encapsulates drawing, animations, pathing, and input mapping.
    """
    def __init__(self, game: SimICU, screen: pygame.Surface, retro_antialias: bool = False):
        self.game = game
        self.screen = screen
        self.retro_antialias = retro_antialias

        # Layout
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.waiting_room_y = 50
        self.waiting_room_height = 200
        self.bed_area_y = 300
        self.bed_area_height = 400
        self.ui_panel_x = 900
        self.ui_panel_width = 300

        # Fonts
        self.small_font = pygame.font.Font(None, 22)
        self.font = pygame.font.Font(None, 28)
        self.large_font = pygame.font.Font(None, 40)

        # Sprites and caches
        base_dir = os.path.dirname(os.path.dirname(__file__))
        sprites_dir = os.path.join(base_dir, "sprites")
        self._load_sprite("patient_sprite_raw", os.path.join(sprites_dir, "raised_hand.png"))
        self._load_sprite("patient_in_bed_sprite_raw", os.path.join(sprites_dir, "patient.png"))
        self._load_sprite("bed_sprite_raw", os.path.join(sprites_dir, "bed.png"))
        self._load_sprite("vent_bed_raw", os.path.join(sprites_dir, "vent_bed.png"))
        self._load_sprite("vent_patient_raw", os.path.join(sprites_dir, "vent_patient.png"))
        self._load_sprite("waiting_bg_raw", os.path.join(sprites_dir, "waiting_room.png"))
        self._load_sprite("floor_bg_raw", os.path.join(sprites_dir, "hospital_floor.png"), convert=False)
        self._load_sprite("nurse_sprite_raw", os.path.join(sprites_dir, "nurse.png"))

        self._patient_sprite_cache: Dict = {}
        self._patient_in_bed_sprite_cache: Dict = {}
        self._bed_sprite_cache: Dict = {}
        self._vent_bed_cache: Dict = {}
        self._vent_patient_cache: Dict = {}
        self._waiting_bg_cache: Dict = {}
        self._floor_bg_cache: Dict = {}
        self.patient_in_bed_scale = 1.2
        self.waiting_sprite_scale_w = 1.3
        self.waiting_sprite_scale_h = 1.6

        # Animations/state
        self.selected_patient = None
        self.patient_moves: Dict[int, Dict[str, float]] = {}  # patient_id -> {'x','y','tx','ty','speed'}
        self.patients_waiting_at_target: Dict[int, Tuple[float, float]] = {}
        self.nurse_size = 64
        self.nurse_speed = 28.0
        self.nurse_positions: Dict = {}
        self.nurse_paths: Dict = {}
        self.nurse_stations: Dict = {}
        self.pending_assignments: List[Dict] = []
        self.bed_positions: Dict = {}
        self.vent_positions: Dict = {}

        # Deferral for parity: only commit engine action on nurse arrival
        self.deferred_action = None
        self.ready_to_apply_deferred = False

    def _load_sprite(self, attr: str, path: str, convert: bool = True):
        try:
            surf = pygame.image.load(path)
            surf = surf.convert_alpha() if convert else surf.convert()
            setattr(self, attr, surf)
        except Exception:
            setattr(self, attr, None)

    # Controller API (mouse/AI use these)
    def select_patient(self, patient_id: int):
        for p in self.game.patients:
            if p.id == patient_id and p.status == PatientStatus.WAITING:
                self.selected_patient = p
                return True
        return False

    def click_bed(self, bed_index: int):
        if bed_index < 0 or bed_index >= len(self.game.beds):
            return False
        bed = self.game.beds[bed_index]
        if not self.selected_patient or not bed.available:
            return False
        # compute target pos and queue movement + nurse run (engine action is deferred)
        bed_x = 200 + (bed_index % 4) * 150
        bed_y = self.bed_area_y + 50 + (bed_index // 4) * 120
        # start movement if no other patient moving
        if not self.patient_moves:
            start_x, start_y = self._waiting_slot_of(self.selected_patient)
            self.patient_moves[self.selected_patient.id] = {'x': float(start_x), 'y': float(start_y),
                                                           'tx': bed_x + 10, 'ty': bed_y - 20, 'speed': 25.0}
            # queue nearest nurse
            nurse = self._nearest_available_nurse(bed_x, bed_y)
            if nurse:
                self.pending_assignments.append({'nurse': nurse, 'patient': self.selected_patient, 'bed': bed})
                # set deferred action (patient_id, action_type 0)
                self.deferred_action = (self.selected_patient.id, 0)
                self.selected_patient = None
                return True
        return False

    def click_vent(self, vent_index: int):
        if vent_index < 0 or vent_index >= len(self.game.ventilators):
            return False
        vent = self.game.ventilators[vent_index]
        if not self.selected_patient or not vent.available:
            return False
        vent_x = 50
        vent_y = self.bed_area_y + 50 + vent_index * 120
        if not self.patient_moves:
            start_x, start_y = self._waiting_slot_of(self.selected_patient)
            self.patient_moves[self.selected_patient.id] = {'x': float(start_x), 'y': float(start_y),
                                                           'tx': vent_x + 10, 'ty': vent_y - 20, 'speed': 25.0}
            nurse = self._nearest_available_nurse(vent_x, vent_y)
            if nurse:
                self.pending_assignments.append({'nurse': nurse, 'patient': self.selected_patient, 'vent': vent})
                self.deferred_action = (self.selected_patient.id, 1)
                self.selected_patient = None
                return True
        return False

    def _nearest_available_nurse(self, tx: int, ty: int):
        avail = [n for n in self.game.nurses if n.available]
        if not avail:
            return None
        for n in avail:
            if n not in self.nurse_positions:
                self.nurse_positions[n] = self.nurse_stations.get(n, (850, self.bed_area_y + 50))
        def dist2(n):
            nx, ny = self.nurse_positions.get(n, (tx, ty))
            dx = nx - tx; dy = ny - ty
            return dx*dx + dy*dy
        return min(avail, key=dist2)

    def _waiting_slot_of(self, patient):
        waiting = self.game.get_waiting_patients()
        try:
            idx = waiting.index(patient)
        except ValueError:
            idx = 0
        return 50 + idx * 120, self.waiting_room_y + 20

    # Animation and drawing
    def update_animations(self):
        # update nurse positions and complete tasks
        self._update_nurse_positions()
        # update patient movement and placeholders
        if self.patient_moves:
            finished = []
            for pid, mv in list(self.patient_moves.items()):
                dx = mv['tx'] - mv['x']; dy = mv['ty'] - mv['y']
                dist = max(1e-6, (dx*dx + dy*dy) ** 0.5)
                step = min(mv['speed'], dist)
                mv['x'] += (dx / dist) * step; mv['y'] += (dy / dist) * step
                if dist <= mv['speed'] + 0.1:
                    self.patients_waiting_at_target[pid] = (mv['tx'], mv['ty'])
                    finished.append(pid)
            for pid in finished:
                self.patient_moves.pop(pid, None)

    def draw(self):
        # background
        if getattr(self, "floor_bg_raw", None):
            key_bg = (self.width, self.height)
            if key_bg not in self._floor_bg_cache:
                self._floor_bg_cache[key_bg] = pygame.transform.smoothscale(self.floor_bg_raw, (self.width, self.height))
            self.screen.blit(self._floor_bg_cache[key_bg], (0, 0))
        else:
            self.screen.fill(BLACK)
        # waiting room
        title = self.font.render("WAITING ROOM", self.retro_antialias, WHITE)
        self.screen.blit(title, (50, 20))
        wr_x, wr_y, wr_w, wr_h = 50, self.waiting_room_y, 800, self.waiting_room_height
        if getattr(self, "waiting_bg_raw", None):
            key = (wr_w, wr_h)
            if key not in self._waiting_bg_cache:
                self._waiting_bg_cache[key] = pygame.transform.smoothscale(self.waiting_bg_raw, (wr_w, wr_h))
            self.screen.blit(self._waiting_bg_cache[key], (wr_x, wr_y))
        else:
            pygame.draw.rect(self.screen, DARK_GRAY, (wr_x, wr_y, wr_w, wr_h))
        pygame.draw.rect(self.screen, WHITE, (wr_x, wr_y, wr_w, wr_h), 2)

        # waiting patients (exclude moving)
        moving_ids = set(self.patient_moves.keys())
        waiting_patients = [p for p in self.game.get_waiting_patients() if p.id not in moving_ids]
        for i, patient in enumerate(waiting_patients[:6]):
            self._draw_patient(patient, 50 + i * 120, self.waiting_room_y + 20, minimal=True)

        # beds
        bed_title = self.font.render("ICU BEDS", self.retro_antialias, WHITE)
        self.screen.blit(bed_title, (200, self.bed_area_y - 30))
        for i, bed in enumerate(self.game.beds):
            bed_x = 200 + (i % 4) * 150
            bed_y = self.bed_area_y + 50 + (i // 4) * 120
            self.bed_positions[bed] = (bed_x, bed_y, 120, 120)
            self._draw_bed(bed, bed_x, bed_y)
            # fallback overlay if no patient-in-bed sprite
            if not getattr(self, "patient_in_bed_sprite_raw", None):
                for p in self.game.patients:
                    if p.assigned_bed == bed and (p.id not in self.patient_moves):
                        self._draw_patient(p, bed_x + 10, bed_y - 20, 100, 60)

        # ventilators
        vent_title = self.font.render("VENTILATORS", self.retro_antialias, WHITE)
        self.screen.blit(vent_title, (50, self.bed_area_y - 30))
        for i, vent in enumerate(self.game.ventilators):
            vent_x = 50
            vent_y = self.bed_area_y + 50 + i * 120
            self.vent_positions[vent] = (vent_x, vent_y, 120, 120)
            self._draw_vent(vent, vent_x, vent_y)
            if not getattr(self, "vent_patient_raw", None):
                for p in self.game.patients:
                    if p.assigned_ventilator == vent and (p.id not in self.patient_moves):
                        self._draw_patient(p, vent_x + 10, vent_y - 20, 100, 60)

        # moving patients
        for pid, mv in self.patient_moves.items():
            p = next((q for q in self.game.patients if q.id == pid), None)
            if p:
                self._draw_patient(p, int(mv['x']), int(mv['y']), 140, 110, bar_only=True)

        # standing-at-target placeholders
        for pid, (px, py) in list(self.patients_waiting_at_target.items()):
            p = next((q for q in self.game.patients if q.id == pid), None)
            if p and p.status == PatientStatus.WAITING:
                self._draw_patient(p, int(px), int(py), 100, 80, bar_only=True)

        # nurses
        nurse_title = self.font.render("NURSES", self.retro_antialias, WHITE)
        self.screen.blit(nurse_title, (850, self.bed_area_y - 30))
        for i, nurse in enumerate(self.game.nurses):
            self.nurse_stations[nurse] = (850, self.bed_area_y + 50 + i * 56)
        for nurse in self.game.nurses:
            nx, ny = self.nurse_positions.get(nurse, self.nurse_stations[nurse])
            self._draw_nurse(nurse, int(nx), int(ny), self.nurse_size)

    # internals
    def _draw_bed(self, bed, x, y):
        # available -> bed sprite; occupied -> patient-in-bed sprite + overlays drawn in Retro style
        if bed.available:
            if getattr(self, "bed_sprite_raw", None):
                key = (120, 120)
                if key not in self._bed_sprite_cache:
                    self._bed_sprite_cache[key] = pygame.transform.smoothscale(self.bed_sprite_raw, (120, 120))
                self.screen.blit(self._bed_sprite_cache[key], (x, y))
            else:
                pygame.draw.rect(self.screen, LIGHT_GRAY, (x, y, 120, 120))
            pygame.draw.rect(self.screen, GREEN, (x, y, 120, 120), 2)
        else:
            if getattr(self, "patient_in_bed_sprite_raw", None):
                sw = int(120 * self.patient_in_bed_scale)
                sh = int(120 * self.patient_in_bed_scale)
                key = (sw, sh)
                if key not in self._patient_in_bed_sprite_cache:
                    self._patient_in_bed_sprite_cache[key] = pygame.transform.smoothscale(self.patient_in_bed_sprite_raw, (sw, sh))
                self.screen.blit(self._patient_in_bed_sprite_cache[key], (x + (120 - sw)//2, y + (120 - sh)//2))
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, (x, y, 120, 120))
            pygame.draw.rect(self.screen, RED, (x, y, 120, 120), 2)
            try:
                patient = next(p for p in self.game.patients if p.assigned_bed == bed)
                bar_width = int((patient.severity / 100.0) * 120)
                bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
                pygame.draw.rect(self.screen, bar_color, (x, y + 120 - 10, bar_width, 10))
                id_text = self.small_font.render(f"#{patient.id}", self.retro_antialias, WHITE)
                self.screen.blit(id_text, (x + 4, y + 4))
                t_letter = "R" if patient.patient_type == PatientType.RESPIRATORY else "C" if patient.patient_type == PatientType.CARDIAC else "T"
                badge = self.small_font.render(t_letter, self.retro_antialias, BLACK)
                bw, bh = badge.get_size()
                pygame.draw.rect(self.screen, YELLOW, (x + 120 - bw - 8, y + 2, bw + 6, bh + 6))
                self.screen.blit(badge, (x + 120 - bw - 5, y + 5))
            except StopIteration:
                pass

    def _draw_vent(self, vent, x, y):
        occupied = not vent.available
        if not occupied:
            if getattr(self, "vent_bed_raw", None):
                key = (120, 120)
                if key not in self._vent_bed_cache:
                    self._vent_bed_cache[key] = pygame.transform.smoothscale(self.vent_bed_raw, (120, 120))
                self.screen.blit(self._vent_bed_cache[key], (x, y))
            else:
                pygame.draw.rect(self.screen, LIGHT_GRAY, (x, y, 120, 120))
            pygame.draw.rect(self.screen, GREEN, (x, y, 120, 120), 2)
        else:
            if getattr(self, "vent_patient_raw", None):
                key = (120, 120)
                if key not in self._vent_patient_cache:
                    self._vent_patient_cache[key] = pygame.transform.smoothscale(self.vent_patient_raw, (120, 120))
                self.screen.blit(self._vent_patient_cache[key], (x, y))
            else:
                pygame.draw.rect(self.screen, DARK_GRAY, (x, y, 120, 120))
            pygame.draw.rect(self.screen, RED, (x, y, 120, 120), 2)
            try:
                patient = next(p for p in self.game.patients if p.assigned_ventilator == vent and p.status == PatientStatus.ON_VENTILATOR)
                bar_width = int((patient.severity / 100.0) * 120)
                bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
                pygame.draw.rect(self.screen, bar_color, (x, y + 120 - 10, bar_width, 10))
                t_letter = "R" if patient.patient_type == PatientType.RESPIRATORY else "C" if patient.patient_type == PatientType.CARDIAC else "T"
                badge = self.small_font.render(t_letter, self.retro_antialias, BLACK)
                bw, bh = badge.get_size()
                pygame.draw.rect(self.screen, YELLOW, (x + 120 - bw - 8, y + 2, bw + 6, bh + 6))
                self.screen.blit(badge, (x + 120 - bw - 5, y + 5))
            except StopIteration:
                pass

    def _draw_patient(self, patient, x, y, width=100, height=80, minimal=False, bar_only=False):
        if bar_only:
            if getattr(self, "patient_sprite_raw", None):
                key = (width, height, "bar_only")
                if key not in self._patient_sprite_cache:
                    src_w, src_h = self.patient_sprite_raw.get_size()
                    scale = min(width / src_w, height / src_h)
                    scaled = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
                    self._patient_sprite_cache[key] = pygame.transform.smoothscale(self.patient_sprite_raw, scaled)
                sprite = self._patient_sprite_cache[key]
                self.screen.blit(sprite, (x + (width - sprite.get_width()) // 2, y + (height - sprite.get_height()) // 2))
            bar_width = int((patient.severity / 100.0) * width)
            bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
            pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
            return
        if minimal:
            if getattr(self, "patient_sprite_raw", None):
                tw = int(width * self.waiting_sprite_scale_w)
                th = int(height * self.waiting_sprite_scale_h)
                key = (tw, th, "waiting")
                if key not in self._patient_sprite_cache:
                    self._patient_sprite_cache[key] = pygame.transform.smoothscale(self.patient_sprite_raw, (tw, th))
                self.screen.blit(self._patient_sprite_cache[key], (x + (width - tw) // 2, y + (height - th) // 2))
            bar_width = int((patient.severity / 100.0) * width)
            bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
            pygame.draw.rect(self.screen, bar_color, (x, y + height - 10, bar_width, 10))
            # type badge
            t_letter = "R" if patient.patient_type == PatientType.RESPIRATORY else "C" if patient.patient_type == PatientType.CARDIAC else "T"
            badge = self.small_font.render(t_letter, self.retro_antialias, BLACK)
            bw, bh = badge.get_size()
            pygame.draw.rect(self.screen, YELLOW, (x + width - bw - 8, y + 2, bw + 6, bh + 6))
            self.screen.blit(badge, (x + width - bw - 5, y + 5))
            return
        # full sprite fallback
        if getattr(self, "patient_sprite_raw", None):
            key = (width, height)
            if key not in self._patient_sprite_cache:
                src_w, src_h = self.patient_sprite_raw.get_size()
                scale = min(width / src_w, height / src_h)
                scaled = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
                self._patient_sprite_cache[key] = pygame.transform.smoothscale(self.patient_sprite_raw, scaled)
            sprite = self._patient_sprite_cache[key]
            self.screen.blit(sprite, (x + (width - sprite.get_width()) // 2, y + (height - sprite.get_height()) // 2))
            pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)

    # Nurse pathing
    def _row_corridor_y(self):
        return self.bed_area_y + 50

    def _plan_path(self, start, target, use_corridor=True):
        cx, cy = start; tx, ty = target
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
        for task in self.pending_assignments:
            if task.get('nurse') == nurse:
                if 'bed' in task and task['bed'] in self.bed_positions:
                    bx, by, bw, bh = self.bed_positions[task['bed']]
                    return bx + bw - (size or self.nurse_size), by
                if 'vent' in task and task['vent'] in self.vent_positions:
                    vx, vy, vw, vh = self.vent_positions[task['vent']]
                    return vx + vw - (size or self.nurse_size), vy
        return self.nurse_stations.get(nurse, (850, self.bed_area_y + 50))

    def _update_nurse_positions(self, size=None):
        if size is None:
            size = self.nurse_size
        for nurse in self.game.nurses:
            target_x, target_y = self._get_nurse_target(nurse, size=size)
            if nurse not in self.nurse_positions:
                self.nurse_positions[nurse] = self.nurse_stations.get(nurse, (850, self.bed_area_y + 50))
                self.nurse_paths[nurse] = []
                continue
            cur_x, cur_y = self.nurse_positions[nurse]
            has_pending = any(t.get('nurse') == nurse for t in self.pending_assignments)
            is_idle = not has_pending
            use_corridor = not is_idle
            if is_idle:
                target_x, target_y = self.nurse_stations.get(nurse, (850, self.bed_area_y + 50))
                if abs(cur_x - target_x) <= 1 and abs(cur_y - target_y) <= 1:
                    self.nurse_positions[nurse] = (target_x, target_y)
                    self.nurse_paths[nurse] = []
                    continue
            dx_t = target_x - cur_x; dy_t = target_y - cur_y
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
            if self.nurse_paths[nurse]:
                wx, wy = self.nurse_paths[nurse][0]
            else:
                wx, wy = target_x, target_y
            dx = wx - cur_x; dy = wy - cur_y
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

        # complete pending tasks -> signal deferred action ready
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
                self.ready_to_apply_deferred = True
            self.pending_assignments = remaining

    def _draw_nurse(self, nurse, x, y, size=40):
        if getattr(self, "nurse_sprite_raw", None):
            sprite = pygame.transform.smoothscale(self.nurse_sprite_raw, (size, size))
            self.screen.blit(sprite, (x, y))
        else:
            pygame.draw.circle(self.screen, GREEN if nurse.available else RED, (x + size // 2, y + size // 2), size // 2)


