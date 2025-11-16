import numpy as np
from sim_icu_env import SimICUEnv
from stable_baselines3.common.monitor import Monitor


def get_greedy_action(state: np.ndarray, max_patients: int):
    """
    Greedy policy on the normalized observation:
    - Observation layout per patient slot: [severity, time_waiting, status_encoded, type_encoded] in [0,1]
    - Tail: [free_beds, free_nurses, free_vents, free_step_down, tick] normalized
    Strategy:
      1) Identify waiting patients (status_encoded == 0.0)
      2) Pick the most critical by (severity desc, time_waiting desc)
      3) If vents+nurses available and severity > 0.7, assign vent; else if beds+nurses available, assign bed; else do nothing
    Returns (slot_id, action_type) where action_type: 0=bed, 1=vent, 2=idle
    """
    waiting = []
    for i in range(max_patients):
        base = i * 4
        severity = float(state[base + 0])
        time_wait = float(state[base + 1])
        status_norm = float(state[base + 2])  # 0.0 == WAITING
        if status_norm == 0.0 and severity > 0.0:
            waiting.append((i, severity, time_wait))

    if not waiting:
        return (0, 2)

    # Sickest first: lowest life (severity), tie-break by longer wait
    waiting.sort(key=lambda t: (t[1], -t[2]))
    slot_id, sev, tw = waiting[0]

    free_beds = float(state[-5])  # normalized fraction free
    free_nurses = float(state[-4])
    free_vents = float(state[-3])

    beds_available = free_beds > 0.0 and free_nurses > 0.0
    vents_available = free_vents > 0.0 and free_nurses > 0.0

    # Prefer vent when critically low life
    if vents_available and sev < 0.3:
        return (slot_id, 1)
    if beds_available:
        return (slot_id, 0)
    return (slot_id, 2)


if __name__ == "__main__":
    print("Testing Greedy Agent baseline...")
    env = SimICUEnv(max_patients=10, max_ticks=1000, render_mode=None)
    env = Monitor(env)

    episodes = 5
    total_saved = 0
    total_lost = 0
    for ep in range(episodes):
        obs, info = env.reset()
        done = False
        while not done:
            action = get_greedy_action(obs, max_patients=10)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

        # Unwrap Monitor to access underlying environment for the final score
        base_env = env.env if hasattr(env, 'env') else env
        score = base_env.game.get_score()
        total_saved += score['patients_saved']
        total_lost += score['patients_lost']
        print(f"Episode {ep+1}: Saved={score['patients_saved']} Lost={score['patients_lost']}")

    print("\n--- Greedy Agent Results ---")
    print(f"Avg Saved: {total_saved / episodes:.2f}")
    print(f"Avg Lost: {total_lost / episodes:.2f}")


