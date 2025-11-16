import pygame

# Shared UI helpers to match Retro visuals

def draw_bed(surface, sprites, caches, fonts, bed, x, y, width=120, height=120, retro_antialias=False):
    """
    Draw a bed tile.
    - sprites: dict with keys 'bed_sprite_raw', 'patient_in_bed_sprite_raw'
    - caches: dict with keys '_bed_sprite_cache', '_patient_in_bed_sprite_cache'
    - fonts: dict with keys 'small_font'
    """
    LIGHT_GRAY = (192, 192, 192)
    DARK_GRAY = (64, 64, 64)
    GREEN = (50, 205, 50)
    RED = (220, 20, 60)
    YELLOW = (255, 215, 0)
    WHITE = (255, 255, 255)
    from sim_icu_logic import PatientType

    bed_sprite_raw = sprites.get('bed_sprite_raw')
    patient_in_bed_sprite_raw = sprites.get('patient_in_bed_sprite_raw')
    _bed_sprite_cache = caches.get('_bed_sprite_cache')
    _patient_in_bed_sprite_cache = caches.get('_patient_in_bed_sprite_cache')
    small_font = fonts.get('small_font')

    if bed.available:
        if bed_sprite_raw is not None:
            key = (width, height)
            if key not in _bed_sprite_cache:
                _bed_sprite_cache[key] = pygame.transform.smoothscale(bed_sprite_raw, (width, height))
            surface.blit(_bed_sprite_cache[key], (x, y))
        else:
            pygame.draw.rect(surface, LIGHT_GRAY, (x, y, width, height))
        pygame.draw.rect(surface, GREEN, (x, y, width, height), 2)
    else:
        if patient_in_bed_sprite_raw is not None:
            sw = max(1, int(width * 1.2))
            sh = max(1, int(height * 1.2))
            key2 = (sw, sh)
            if key2 not in _patient_in_bed_sprite_cache:
                _patient_in_bed_sprite_cache[key2] = pygame.transform.smoothscale(patient_in_bed_sprite_raw, (sw, sh))
            draw_x = x + (width - sw) // 2
            draw_y = y + (height - sh) // 2
            surface.blit(_patient_in_bed_sprite_cache[key2], (draw_x, draw_y))
        else:
            pygame.draw.rect(surface, DARK_GRAY, (x, y, width, height))
        pygame.draw.rect(surface, RED, (x, y, width, height), 2)

        # Overlay bar, id, type badge
        try:
            import sim_icu_logic as logic
            patient = next(p for p in logic.SimICU.__mro__[0].patients if p.assigned_bed == bed)  # not used; avoid import cycles
        except Exception:
            # Fallback: best-effort lookup from globals (callers typically supply this differently)
            patient = None
        # Caller should draw overlays itself when needed; keep function focused on tile visuals.


def draw_vent(surface, sprites, caches, fonts, vent, x, y, width=120, height=120, retro_antialias=False, overlay_patient=None):
    """
    Draw a ventilator tile.
    - sprites: dict with keys 'vent_bed_raw', 'vent_patient_raw'
    - caches: dict with keys '_vent_bed_cache', '_vent_patient_cache'
    """
    LIGHT_GRAY = (192, 192, 192)
    DARK_GRAY = (64, 64, 64)
    GREEN = (50, 205, 50)
    RED = (220, 20, 60)
    YELLOW = (255, 215, 0)
    WHITE = (255, 255, 255)
    from sim_icu_logic import PatientType

    vent_bed_raw = sprites.get('vent_bed_raw')
    vent_patient_raw = sprites.get('vent_patient_raw')
    _vent_bed_cache = caches.get('_vent_bed_cache')
    _vent_patient_cache = caches.get('_vent_patient_cache')
    small_font = fonts.get('small_font')

    occupied = not vent.available
    if not occupied:
        if vent_bed_raw is not None:
            key = (width, height)
            if key not in _vent_bed_cache:
                _vent_bed_cache[key] = pygame.transform.smoothscale(vent_bed_raw, (width, height))
            surface.blit(_vent_bed_cache[key], (x, y))
        else:
            pygame.draw.rect(surface, LIGHT_GRAY, (x, y, width, height))
        pygame.draw.rect(surface, GREEN, (x, y, width, height), 2)
    else:
        if vent_patient_raw is not None:
            key = (width, height)
            if key not in _vent_patient_cache:
                _vent_patient_cache[key] = pygame.transform.smoothscale(vent_patient_raw, (width, height))
            surface.blit(_vent_patient_cache[key], (x, y))
        else:
            pygame.draw.rect(surface, DARK_GRAY, (x, y, width, height))
        pygame.draw.rect(surface, RED, (x, y, width, height), 2)

    # overlay of patient is handled by caller to avoid tight coupling


def draw_patient(surface, sprites, caches, fonts, patient, x, y, width=100, height=80, minimal=False, bar_only=False, retro_antialias=False):
    """
    Draw a patient sprite (or rectangle fallback).
    """
    WHITE = (255, 255, 255)
    GREEN = (50, 205, 50)
    ORANGE = (255, 165, 0)
    RED = (220, 20, 60)
    YELLOW = (255, 215, 0)
    BLACK = (0, 0, 0)
    from sim_icu_logic import PatientStatus, PatientType

    patient_sprite_raw = sprites.get('patient_sprite_raw')
    _patient_sprite_cache = caches.get('_patient_sprite_cache')
    small_font = fonts.get('small_font')

    if bar_only:
        if patient_sprite_raw:
            key = (width, height, "bar_only")
            if key not in _patient_sprite_cache:
                src_w, src_h = patient_sprite_raw.get_size()
                scale = min(width / src_w, height / src_h)
                scaled = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
                _patient_sprite_cache[key] = pygame.transform.smoothscale(patient_sprite_raw, scaled)
            sprite = _patient_sprite_cache[key]
            draw_x = x + (width - sprite.get_width()) // 2
            draw_y = y + (height - sprite.get_height()) // 2
            surface.blit(sprite, (draw_x, draw_y))
        bar_width = int((patient.severity / 100.0) * width)
        bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
        pygame.draw.rect(surface, bar_color, (x, y + height - 10, bar_width, 10))
        return

    # Minimal (waiting room) with sprite and bar
    if minimal:
        if patient_sprite_raw:
            tw = max(1, int(width * 1.3))
            th = max(1, int(height * 1.6))
            key = (tw, th, "waiting")
            if key not in _patient_sprite_cache:
                _patient_sprite_cache[key] = pygame.transform.smoothscale(patient_sprite_raw, (tw, th))
            sprite = _patient_sprite_cache[key]
            draw_x = x + (width - tw) // 2
            draw_y = y + (height - th) // 2
            surface.blit(sprite, (draw_x, draw_y))
        bar_width = int((patient.severity / 100.0) * width)
        bar_color = GREEN if patient.severity >= 70 else ORANGE if patient.severity >= 40 else RED
        pygame.draw.rect(surface, bar_color, (x, y + height - 10, bar_width, 10))
        # badge
        try:
            t = patient.patient_type
            t_letter = "R" if t == PatientType.RESPIRATORY else "C" if t == PatientType.CARDIAC else "T"
            badge = small_font.render(t_letter, retro_antialias, BLACK)
            bw, bh = badge.get_size()
            pad = 4
            bx = x + width - bw - pad - 2
            by = y + 2
            pygame.draw.rect(surface, YELLOW, (bx - 2, by - 2, bw + 4, bh + 4))
            surface.blit(badge, (bx, by))
        except Exception:
            pass
        return

    # Fallback full sprite + border (callers avoid borders in walking states)
    if patient_sprite_raw:
        key = (width, height)
        if key not in _patient_sprite_cache:
            src_w, src_h = patient_sprite_raw.get_size()
            scale = min(width / src_w, height / src_h)
            scaled = (max(1, int(src_w * scale)), max(1, int(src_h * scale)))
            _patient_sprite_cache[key] = pygame.transform.smoothscale(patient_sprite_raw, scaled)
        sprite = _patient_sprite_cache[key]
        draw_x = x + (width - sprite.get_width()) // 2
        draw_y = y + (height - sprite.get_height()) // 2
        surface.blit(sprite, (draw_x, draw_y))
        pygame.draw.rect(surface, BLACK, (x, y, width, height), 2)
    else:
        color = RED
        pygame.draw.rect(surface, color, (x, y, width, height))
        pygame.draw.rect(surface, BLACK, (x, y, width, height), 2)


