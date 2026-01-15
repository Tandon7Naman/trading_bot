"""
Gold Trading Bot Launcher
Automatically activates venv and runs bot
"""
import sys
import os
from pathlib import Path
import subprocess

# Project root
project_root = Path(__file__).parent

# Virtual environment python
venv_python = project_root / '.venv' / 'Scripts' / 'python.exe'

if not venv_python.exists():
    print("❌ Virtual environment not found!")
    print(f"Expected: {venv_python}")
    print("\nCreate it with: python -m venv .venv")
    sys.exit(1)

# Run bot with venv python
print("=" * 70)
print("🚀 STARTING GOLD TRADING BOT (with venv)")
print("=" * 70)

# Change to src directory
os.chdir(project_root / 'src')

# Run with venv python
result = subprocess.run([str(venv_python), 'dual_market_bot.py'])
sys.exit(result.returncode)
