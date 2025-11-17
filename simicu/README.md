# SimICU - Retro vs. Modern ICU Management

A reinforcement learning project that contrasts a human-driven "retro" approach with a data-driven "modern" AI for managing an Intensive Care Unit (ICU).

## 🎮 Project Overview

SimICU is a simulation game where you manage ICU resources (nurses, beds, ventilators) to save as many patients as possible. The project demonstrates two approaches:

- **Retro Mode**: Human player manually assigns patients to resources using a pixel-art Pygame interface
- **Modern Mode**: AI agent (trained with reinforcement learning) automatically manages the ICU with optimized decision-making

## 🚀 Quick Start

### Installation

1. Install Python 3.8 or higher

2. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the Demo

Run the interactive demo to choose between modes:

```bash
python demo.py
```

Or run modes directly:

**Retro Mode (Human Player):**

```bash
python retro_mode.py
```

**Modern Mode (AI Agent):**

```bash
python modern_ai_mode.py
```

**Note**: Modern mode requires a trained model. If you don't have one, train it first (see below).

## 🤖 Training the AI Agent

Before running Modern Mode, you need to train the AI agent:

```bash
python train.py
```

This will:

- Train a PPO (Proximal Policy Optimization) agent for 100,000 timesteps
- Save the model to `models/sim_icu_ai_agent`
- Show training progress and evaluation metrics

**Training Options:**

```bash
# Train for more timesteps (better performance, longer training)
python train.py --timesteps 500000

# Specify custom save path
python train.py --save-path models/my_custom_model
```

Training typically takes 10-30 minutes depending on your hardware. The model will be saved automatically and can be used immediately after training completes.

## 📁 Project Structure

```
simicu/
├── sim_icu_logic.py      # Core simulation engine (shared backend)
├── sim_icu_env.py        # Gymnasium environment for RL
├── retro_mode.py         # Pygame frontend for human player
├── modern_mode.py        # Pygame visualization for AI agent
├── train.py              # Training script for RL agent
├── demo.py               # Interactive demo launcher
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🎯 How It Works

### Core Simulation Engine

The `SimICU` class (`sim_icu_logic.py`) runs the core game logic:

- **Time**: Discrete ticks (1 tick = 1 game-hour)
- **Patients**: Arrive randomly, have severity levels (0-100), and can be in different states
- **Resources**: Nurses, beds, and ventilators that can be assigned to patients
- **Game Logic**: Patients get worse while waiting, better when treated

### Retro Mode

Human players interact through a Pygame interface:

- Click patients to select them
- Click beds to assign patients (requires nurse)
- Click ventilators for critical patients
- Visual feedback with pixel-art style graphics

**Controls:**

- **Mouse Click**: Select/assign patients
- **SPACE**: Pause/Resume
- **R**: Reset game

### Modern Mode (AI)

The AI agent uses reinforcement learning:

- **Environment**: Wraps `SimICU` in a Gymnasium-compatible interface
- **State Space**: Patient severities, wait times, resource availability
- **Action Space**: Which patient to act on, and what action (bed/ventilator/nothing)
- **Reward Function**: Encourages saving patients, penalizes waiting and losing patients
- **Algorithm**: PPO (Proximal Policy Optimization) from Stable-Baselines3

**Controls:**

- **SPACE**: Pause/Resume
- **R**: Reset episode
- **+/-**: Speed up/down
- **ESC**: Quit

## 🔬 Technical Details

### Reinforcement Learning Setup

**State Representation:**

- For each patient: severity (0-100), wait time, status (waiting/in_bed/on_ventilator/cured/lost)
- Resource counts: free beds, free nurses, free ventilators
- Current tick number

**Action Space:**

- Multi-discrete: `[patient_id, action_type]`
- `patient_id`: 0 to max_patients-1
- `action_type`: 0 = assign bed, 1 = assign ventilator, 2 = do nothing

**Reward Function:**

- +100 for saving a patient
- -100 for losing a patient
- -0.1 per waiting patient (encourages action)
- -0.05 per unused resource (if patients waiting)
- +0.5 per treated patient (encourages treatment)

### Training Parameters

- **Algorithm**: PPO (Proximal Policy Optimization)
- **Policy**: MLP (Multi-Layer Perceptron)
- **Learning Rate**: 3e-4
- **Batch Size**: 64
- **Discount Factor (γ)**: 0.99
- **Default Training**: 100,000 timesteps

## 📊 Expected Results

After training, the AI agent typically achieves:

- **Success Rate**: 70-90% (patients saved / total patients)
- **Efficiency**: Better resource utilization than human players
- **Speed**: Makes decisions instantly, can run at high speed

The AI learns to:

- Prioritize critical patients (high severity)
- Efficiently allocate resources
- Balance between beds and ventilators
- Minimize wait times

## 🛠️ Customization

### Adjusting Game Difficulty

Edit `sim_icu_logic.py`:

- `arrival_rate`: How often patients arrive (higher = harder)
- `num_nurses`, `num_beds`, `num_ventilators`: Resource availability
- Severity increase/decrease rates in `Patient.update()`

### Modifying Reward Function

Edit `sim_icu_env.py`, method `_calculate_reward()`:

- Adjust reward/penalty values
- Add new reward components
- Change reward scaling

### Training Longer

For better performance, train for more timesteps:

```bash
python train.py --timesteps 500000
```

## 📝 License

This project is part of the deep-learning-workshop hackathon 2025.

## 🙏 Acknowledgments

- **Gymnasium**: RL environment standard
- **Stable-Baselines3**: Pre-built RL algorithms
- **Pygame**: Game development framework

## 🐛 Troubleshooting

**"Model not found" error:**

- Train the model first: `python train.py`

**Pygame window doesn't open:**

- Make sure pygame is installed: `pip install pygame`
- Check your display settings

**Training is slow:**

- This is normal! RL training takes time
- Reduce `--timesteps` for faster training (but worse performance)
- Use GPU if available (Stable-Baselines3 will auto-detect)

**Import errors:**

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Use Python 3.8 or higher

## 🎓 Learning Resources

- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [Stable-Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [PPO Algorithm Paper](https://arxiv.org/abs/1707.06347)

---

**Enjoy managing your ICU!** 🏥
