import os
import shutil

# --- CONFIGURATION ---
FOLDERS = [
    "strategies",
    "execution",
    "data",
    "config",
    "tests",
    "models",
    "logs"
]

# Map: "Old Filename" -> "New Folder/New Filename"
MOVES = {
    # Data & State
    "feed_live_data.py": "data/feed_live_data.py",
    "MCX_gold_daily.csv": "data/MCX_gold_daily.csv",
    "paper_state_mcx.json": "data/paper_state_mcx.json",
    
    # Execution & Alerts
    "telegram_alerts.py": "execution/telegram_alerts.py",
    
    # Strategies (Renaming 'paper_trading' to a specific strategy name)
    "paper_trading_mcx.py": "strategies/gold_scalper.py",
    "train_ppo.py": "strategies/train_ppo.py",
    
    # Entry Point (Renaming 'run_loop' to standard 'main')
    "run_loop.py": "main.py",
    
    # Config
    ".env": "config/.env"
}

def create_structure():
    print("\U0001f3d7️  Building Project Architecture...")
    
    # 1. Create Directories
    for folder in FOLDERS:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"   ✅ Created /{folder}")
        
        # Add __init__.py to make it a Python Package
        init_file = os.path.join(folder, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, 'a').close()

    # 2. Move Files
    print("\n📦 Moving Assets...")
    for old_name, new_path in MOVES.items():
        if os.path.exists(old_name):
            # Check if destination exists (data folder might have sub-path)
            # shutil.move handles paths nicely
            try:
                shutil.move(old_name, new_path)
                print(f"   ➡️  Moved {old_name} to {new_path}")
            except Exception as e:
                print(f"   ⚠️  Could not move {old_name}: {e}")
        else:
            print(f"   ℹ️  Skipped {old_name} (Not found)")

    # 3. Create Settings Placeholder
    if not os.path.exists("config/settings.py"):
        with open("config/settings.py", "w") as f:
            f.write("ENABLE_MCX = False\nDEBUG_MODE = True\n")
        print("   ✅ Created config/settings.py")

    print("\n🎉 Architecture Complete! (Note: Imports in your code will need updating)")

if __name__ == "__main__":
    create_structure()
