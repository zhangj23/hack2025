"""
Training Script for SimICU RL Agent
This script trains a reinforcement learning agent using Stable-Baselines3.
"""

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from sim_icu_env import SimICUEnv
import os
from stable_baselines3.common.monitor import Monitor


def train_agent(total_timesteps=100000, save_path="models/sim_icu_ai_agent"):
    """
    Train a PPO agent on the SimICU environment.
    
    Args:
        total_timesteps: Number of training steps
        save_path: Path to save the trained model
    """
    print("=" * 60)
    print("SimICU - Training Reinforcement Learning Agent")
    print("=" * 60)
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
    
    print("\n1. Creating environment...")
    # Vectorized training environment (4 parallel envs) with curriculum: easy first (arrival 0.05)
    env = make_vec_env(lambda: Monitor(SimICUEnv(max_patients=10, max_ticks=300, render_mode=None, arrival_rate=0.05)), n_envs=4)
 
    # Create evaluation environment (harder arrival rate to measure true performance)
    eval_env = make_vec_env(lambda: Monitor(SimICUEnv(max_patients=10, max_ticks=300, render_mode=None, arrival_rate=0.10)), n_envs=1)
    
    # Create the AI agent using PPO (Proximal Policy Optimization)
    print("2. Creating PPO agent...")
    model = PPO(
        "MlpPolicy",  # Multi-layer perceptron policy (standard neural network)
        env,
        verbose=1,  # Print training progress
        learning_rate=3e-4,  # Learning rate
        n_steps=4096,  # Steps per update (per env)
        batch_size=256,  # Batch size for training
        n_epochs=10,  # Number of epochs per update
        gamma=0.995,  # Discount factor
        gae_lambda=0.95,  # GAE lambda parameter
        clip_range=0.2,  # PPO clip range
        ent_coef=0.02,  # Stronger exploration
        vf_coef=0.5,  # Value function coefficient
        max_grad_norm=0.5,  # Gradient clipping
        tensorboard_log="./logs/",  # TensorBoard logging
    )
    
    # Setup callbacks
    print("3. Setting up callbacks...")
    
    # Evaluation callback (evaluates agent periodically)
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(os.path.dirname(save_path), "best_model"),
        log_path="./logs/eval/",
        eval_freq=5000,  # Evaluate every 5000 steps
        deterministic=True,
        render=True
    )
    
    # Checkpoint callback (saves model periodically)
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,  # Save every 10000 steps
        save_path=os.path.join(os.path.dirname(save_path), "checkpoints"),
        name_prefix="sim_icu_model"
    )
    
    # Train the model
    print(f"\n4. Training agent for {total_timesteps} timesteps...")
    print("   This may take a while. Progress will be shown below.\n")
    
    # Check if progress bar dependencies are available
    try:
        import tqdm
        import rich
        use_progress_bar = True
    except ImportError:
        print("   Note: Progress bar disabled (tqdm/rich not installed).")
        print("   Install with: pip install tqdm rich\n")
        use_progress_bar = False
    
    # Curriculum: first stage on easier arrivals, then harder
    stage1 = max(50000, int(total_timesteps * 0.33))
    stage2 = max(0, total_timesteps - stage1)

    model.learn(
        total_timesteps=stage1,
        callback=[eval_callback, checkpoint_callback],
        progress_bar=use_progress_bar
    )

    if stage2 > 0:
        # Switch to harder environment
        env_hard = make_vec_env(lambda: Monitor(SimICUEnv(max_patients=10, max_ticks=300, render_mode=None, arrival_rate=0.10)), n_envs=4)
        model.set_env(env_hard)
        model.learn(
            total_timesteps=stage2,
            callback=[eval_callback, checkpoint_callback],
            progress_bar=use_progress_bar
        )
    
    # Save the final model
    print(f"\n5. Saving trained model to {save_path}...")
    model.save(save_path)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Model saved to: {save_path}")
    print("=" * 60)
    
    # Test the trained model
    print("\n6. Testing trained model...")
    test_agent(model, num_episodes=3)
    
    return model


def test_agent(model, num_episodes=5):
    """Test the trained agent on a single non-vectorized environment"""
    print(f"\nRunning {num_episodes} test episodes...")
    
    total_saved = 0
    total_lost = 0
    
    for episode in range(num_episodes):
        # Use a fresh single environment for evaluation
        eval_env = Monitor(SimICUEnv(max_patients=10, max_ticks=300, render_mode=None))
        obs, info = eval_env.reset()
        done = False
        episode_saved = 0
        episode_lost = 0
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = eval_env.step(action)
            done = terminated or truncated
            
            if info.get('patients_saved', 0) > episode_saved:
                episode_saved = info['patients_saved']
            if info.get('patients_lost', 0) > episode_lost:
                episode_lost = info['patients_lost']
        
        total_saved += episode_saved
        total_lost += episode_lost
        
        print(f"Episode {episode + 1}: Saved={episode_saved}, Lost={episode_lost}")
    
    avg_saved = total_saved / num_episodes
    avg_lost = total_lost / num_episodes
    print(f"\nAverage over {num_episodes} episodes:")
    print(f"  Saved: {avg_saved:.1f}")
    print(f"  Lost: {avg_lost:.1f}")
    print(f"  Success Rate: {(avg_saved / (avg_saved + avg_lost) * 100):.1f}%" if (avg_saved + avg_lost) > 0 else "  Success Rate: N/A")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train SimICU RL Agent")
    parser.add_argument(
        "--timesteps",
        type=int,
        default=100000,
        help="Number of training timesteps (default: 100000)"
    )
    parser.add_argument(
        "--save-path",
        type=str,
        default="models/sim_icu_ai_agent",
        help="Path to save the trained model (default: models/sim_icu_ai_agent)"
    )
    
    args = parser.parse_args()
    
    train_agent(total_timesteps=args.timesteps, save_path=args.save_path)

