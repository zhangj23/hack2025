from stable_baselines3 import PPO
from sim_icu_env import SimICUEnv
from stable_baselines3.common.monitor import Monitor


def main(model_path: str = "models/best_model/best_model.zip"):
    print("Running 'Modern' AI Agent with human render...")
    env = SimICUEnv(max_patients=10, max_ticks=1000, render_mode="human")
    env = Monitor(env)

    model = PPO.load(model_path)

    obs, info = env.reset()
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        env.render()

    score = env.game.get_score()
    print(f"Final Score: Saved={score['patients_saved']}, Lost={score['patients_lost']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run trained PPO model with human render")
    parser.add_argument("--model", type=str, default="models/best_model/best_model.zip", help="Path to model zip")
    args = parser.parse_args()
    main(model_path=args.model)


