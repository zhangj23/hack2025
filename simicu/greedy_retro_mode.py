"""
Greedy baseline runner that uses the RetroSimICU view/controller.
It simulates clicks using RetroSimICU.ai_* helpers, mirroring human input.
"""

import pygame
import sys
from sim_icu_logic import PatientStatus, PatientType
from retro_mode import RetroSimICU


def pick_best_waiting(game):
    """Return the most critical waiting patient by (severity desc, wait_time desc)."""
    waiting = [p for p in game.get_waiting_patients()]
    if not waiting:
        return None
    # Sickest first: lowest life; tie-break longer wait
    waiting.sort(key=lambda p: (p.severity, -p.time_waiting))
    return waiting[0]


def greedy_decide(game, patient):
    """
    Decide resource target for patient:
    - Prefer ventilator for RESPIRATORY if vent+nurse available
    - Otherwise prefer bed if bed+nurse available
    - Otherwise None
    Returns ('vent', index) | ('bed', index) | None
    """
    if patient is None:
        return None
    vents_avail = game.free_vents > 0 and game.free_nurses > 0
    beds_avail = game.free_beds > 0 and game.free_nurses > 0
    if getattr(patient, 'patient_type', None) == PatientType.RESPIRATORY and vents_avail:
        try:
            vidx = next(i for i, v in enumerate(game.ventilators) if v.available)
            return ('vent', vidx)
        except StopIteration:
            pass
    if beds_avail:
        try:
            bidx = next(i for i, b in enumerate(game.beds) if b.available)
            return ('bed', bidx)
        except StopIteration:
            pass
    if vents_avail:
        try:
            vidx = next(i for i, v in enumerate(game.ventilators) if v.available)
            return ('vent', vidx)
        except StopIteration:
            pass
    return None


def main():
    pygame.init()
    ui = RetroSimICU()
    ui.show_intro = False  # start immediately
    pygame.display.set_caption("SimICU - Greedy Baseline")

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Freeze on game over (render only)
        if getattr(ui, 'game_over', False):
            ui.draw()
            clock.tick(10)
            continue

        # Clear stale selection if patient left waiting state
        if ui.selected_patient is not None and ui.selected_patient.status != PatientStatus.WAITING:
            ui.selected_patient = None

        # Only decide when no movement/pending and cooldown cleared
        if ui.input_cooldown_ticks == 0 and not ui.patient_moves and not ui.pending_assignments:
            # Keep operating on existing selection if still waiting; else pick best waiting
            candidate = ui.selected_patient if (ui.selected_patient and ui.selected_patient.status == PatientStatus.WAITING) else pick_best_waiting(ui.game)
            if candidate:
                if ui.selected_patient is None:
                    ui.ai_select_patient(candidate.id)
                decision = greedy_decide(ui.game, candidate)
                if decision:
                    kind, idx = decision
                    if kind == 'bed':
                        ui.ai_click_bed(idx)
                    elif kind == 'vent':
                        ui.ai_click_vent(idx)

        # Advance sim and draw
        ui.ai_tick(1)
        ui.draw()
        clock.tick(10)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()


