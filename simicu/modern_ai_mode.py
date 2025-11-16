"""
Modern AI runner that reuses RetroSimICU as the view/controller.
The RL model simulates user input by calling RetroSimICU's AI controller helpers.
"""

import pygame
import sys
import numpy as np
from stable_baselines3 import PPO
from sim_icu_env import SimICUEnv
from retro_mode import RetroSimICU
from sim_icu_logic import PatientStatus


def build_obs_from_game(env_helper: SimICUEnv, game) -> np.ndarray:
    """Reuse SimICUEnv's normalization but point it at the live Retro game instance."""
    # Temporarily swap the game in the helper env to compute observation
    original = env_helper.game
    env_helper.game = game
    obs = env_helper._get_state()
    env_helper.game = original
    return obs


def main(model_path: str = "models/sim_icu_ai_agent"):
    pygame.init()
    # Create the Retro view
    ui = RetroSimICU()
    ui.show_intro = False  # skip intro for AI demo

    # Helper env for observation building (uses same shapes/scales as training)
    env_helper = SimICUEnv(max_patients=10, max_ticks=1000)

    # Load model
    print(f"Loading AI model from {model_path}...")
    model = PPO.load(model_path)
    print("Model loaded successfully!")

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # If Retro view signaled game over, freeze counts and just render
        if getattr(ui, 'game_over', False):
            ui.draw()
            clock.tick(10)
            continue

        # Build observation from the Retro game's state
        obs = build_obs_from_game(env_helper, ui.game)
        action, _ = model.predict(obs, deterministic=True)
        pid, at = int(action[0]), int(action[1])

        # Clear stale selection if patient is no longer waiting
        if ui.selected_patient is not None and ui.selected_patient.status != PatientStatus.WAITING:
            ui.selected_patient = None

        # Map action to Retro controller API
        applied = False
        # If we already have a selected patient, stick with them until assignment is issued
        target_patient = None
        if ui.selected_patient is not None and ui.selected_patient.status == PatientStatus.WAITING:
            target_patient = ui.selected_patient
        elif at in (0, 1) and pid < len(ui.game.patients):
            cand = ui.game.patients[pid]
            if cand.status == PatientStatus.WAITING:
                target_patient = cand

        if target_patient is not None:
            # Select if none currently selected
            if ui.selected_patient is None:
                ui.ai_select_patient(target_patient.id)
            # Attempt click only when cooldown is zero
            if ui.input_cooldown_ticks == 0 and ui.selected_patient is not None and ui.selected_patient.status == PatientStatus.WAITING:
                if at == 0:
                    # Prefer bed; if none, fall back to vent
                    if ui.game.free_beds > 0 and ui.game.free_nurses > 0:
                        try:
                            bidx = next(i for i, b in enumerate(ui.game.beds) if b.available)
                            applied = ui.ai_click_bed(bidx)
                        except StopIteration:
                            applied = False
                    elif ui.game.free_vents > 0 and ui.game.free_nurses > 0:
                        try:
                            vidx = next(i for i, v in enumerate(ui.game.ventilators) if v.available)
                            applied = ui.ai_click_vent(vidx)
                        except StopIteration:
                            applied = False
                else:
                    # Prefer vent; if none, fall back to bed
                    if ui.game.free_vents > 0 and ui.game.free_nurses > 0:
                        try:
                            vidx = next(i for i, v in enumerate(ui.game.ventilators) if v.available)
                            applied = ui.ai_click_vent(vidx)
                        except StopIteration:
                            applied = False
                    elif ui.game.free_beds > 0 and ui.game.free_nurses > 0:
                        try:
                            bidx = next(i for i, b in enumerate(ui.game.beds) if b.available)
                            applied = ui.ai_click_bed(bidx)
                        except StopIteration:
                            applied = False

        # Heuristic fallback: if action not applied, no movement/pending, cooldown clear -> auto-assign best waiting
        if (not applied) and ui.input_cooldown_ticks == 0 and not ui.patient_moves and not ui.pending_assignments:
            waiting = ui.game.get_waiting_patients()
            if waiting:
                # Pick the most critical: sort by severity, then waiting time
                waiting.sort(key=lambda p: (p.severity, p.time_waiting), reverse=True)
                best = waiting[0]
                if ui.selected_patient is None:
                    ui.ai_select_patient(best.id)
                # Prefer vent for respiratory if nurse+vent available, else bed if nurse+bed available
                if getattr(best, 'patient_type', None) and best.patient_type.name.upper() == 'RESPIRATORY':
                    if ui.game.free_vents > 0 and ui.game.free_nurses > 0:
                        try:
                            vidx = next(i for i, v in enumerate(ui.game.ventilators) if v.available)
                            applied = ui.ai_click_vent(vidx)
                        except StopIteration:
                            applied = False
                    elif ui.game.free_beds > 0 and ui.game.free_nurses > 0:
                        try:
                            bidx = next(i for i, b in enumerate(ui.game.beds) if b.available)
                            applied = ui.ai_click_bed(bidx)
                        except StopIteration:
                            applied = False
                else:
                    if ui.game.free_beds > 0 and ui.game.free_nurses > 0:
                        try:
                            bidx = next(i for i, b in enumerate(ui.game.beds) if b.available)
                            applied = ui.ai_click_bed(bidx)
                        except StopIteration:
                            applied = False
                    elif ui.game.free_vents > 0 and ui.game.free_nurses > 0:
                        try:
                            vidx = next(i for i, v in enumerate(ui.game.ventilators) if v.available)
                            applied = ui.ai_click_vent(vidx)
                        except StopIteration:
                            applied = False

        # Advance simulation pacing like Retro
        ui.ai_tick(1)
        ui.draw()
        clock.tick(10)  # 10 FPS

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run SimICU - Modern AI using Retro view")
    parser.add_argument("--model", type=str, default="models/sim_icu_ai_agent", help="Path to trained model")
    args = parser.parse_args()
    main(model_path=args.model)


