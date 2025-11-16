"""
Demo Script - Compare Retro vs Modern
This script allows you to choose between Retro (human) and Modern (AI) modes.
"""

import sys
import os


def main():
    print("=" * 60)
    print("SimICU - Retro vs. Modern Demo")
    print("=" * 60)
    print("\nChoose a mode:")
    print("1. Retro Mode (Human Player)")
    print("2. Modern Mode (AI Agent)")
    print("3. Train AI Agent")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        print("\nStarting Retro Mode...")
        from retro_mode import RetroSimICU
        game = RetroSimICU()
        game.run()
    
    elif choice == "2":
        model_path = "models/sim_icu_ai_agent"
        if not os.path.exists(model_path + ".zip"):
            print(f"\nERROR: Trained model not found at {model_path}")
            print("Please train the model first by choosing option 3.")
            return
        
        print("\nStarting Modern AI Mode...")
        from modern_mode import ModernSimICU
        game = ModernSimICU(model_path=model_path)
        game.run()
    
    elif choice == "3":
        print("\nStarting Training...")
        print("This will take some time. Press Ctrl+C to stop early.")
        from train import train_agent
        try:
            train_agent()
        except KeyboardInterrupt:
            print("\n\nTraining interrupted by user.")
    
    elif choice == "4":
        print("Goodbye!")
        sys.exit(0)
    
    else:
        print("Invalid choice. Please run again and select 1-4.")


if __name__ == "__main__":
    main()

