# Gold Trading Bot Project Summary

## Overview
This project is a robust, AI-powered gold trading bot for MCX Gold, featuring advanced reinforcement learning (PPO), technical indicator-based decision making, secure credential management, and a real-time dashboard. The system is designed for both backtesting and live (paper) trading, with professional project hygiene and self-repairing state management.

---

## Key Features
- **Smart Trainer (train_ppo.py):**
  - Uses PPO (Proximal Policy Optimization) with custom Gym environment.
  - Technical indicators: RSI, MACD, SMA.
  - Trains on historical MCX gold data and saves the model.

- **Robust Paper Trading Engine (paper_trading_mcx.py):**
  - Loads the trained PPO model and applies it to live data.
  - Self-repair logic for state file (auto-upgrades old/incomplete state).
  - Sends secure Telegram alerts for buy/sell signals.
  - Maintains trading state (equity, position, trade history) in JSON.

- **Real-Time Dashboard (dashboard.py):**
  - Built with Streamlit and Plotly.
  - Live visualization of price, RSI, equity, and open positions.
  - Auto-refreshes and color-codes RSI danger zones.

- **Professional Hygiene:**
  - .env for secrets, requirements.txt, .gitignore, modular code.
  - All scripts and data organized in a clear directory structure.

---

## Main Scripts & Their Purpose

### 1. train_ppo.py
- Trains the PPO agent using MCX gold data and technical indicators.
- Saves the trained model to `models/ppo_gold_agent`.

### 2. paper_trading_mcx.py
- Loads the PPO model and applies it to the latest market data.
- Maintains and repairs the trading state in `paper_state_mcx.json`.
- Sends Telegram alerts for every trade action.

### 3. dashboard.py
- Streamlit dashboard for real-time monitoring.
- Shows price, RSI, equity, and open positions with interactive charts.

### 4. fix_trader.py
- Force-wipes and rewrites `paper_trading_mcx.py` with the latest robust code.
- Ensures self-repair logic is always present.

---

## Example: Self-Repair Logic (paper_trading_mcx.py)
```python
# ...existing code...
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        # 🛠️ REPAIR: If keys are missing from old versions, add them now
        if 'history' not in state: state['history'] = []
        if 'equity' not in state: state['equity'] = INITIAL_CAPITAL
        if 'position' not in state: state['position'] = 'FLAT'
    except:
        state = {"equity": INITIAL_CAPITAL, "position": "FLAT", "history": []}
else:
    state = {
        "equity": INITIAL_CAPITAL, 
        "position": "FLAT", 
        "history": []
    }
# ...existing code...
```

---

## Directory Structure (Key Files)
```
train_ppo.py
paper_trading_mcx.py
dashboard.py
fix_trader.py
.env
requirements.txt
models/
data/
logs/
results/
```

---

## Security & Hygiene
- All secrets (API keys, tokens) are stored in `.env` and loaded securely.
- No hardcoded credentials in any script.
- All dependencies listed in `requirements.txt`.
- `.gitignore` excludes sensitive and unnecessary files.

---

## How to Run
1. **Train the Model:**
   ```bash
   .venv\Scripts\python.exe train_ppo.py
   ```
2. **Start Paper Trading:**
   ```bash
   .venv\Scripts\python.exe run_loop.py
   ```
3. **Launch Dashboard:**
   ```bash
   .venv\Scripts\python.exe -m streamlit run dashboard.py
   ```
4. **Fix/Upgrade Trader Script:**
   ```bash
   .venv\Scripts\python.exe fix_trader.py
   ```

---

## Full Source Code

### train_ppo.py
```
[See train_ppo.py in the repository for the full code.]
```

### paper_trading_mcx.py
```
[See paper_trading_mcx.py in the repository for the full code.]
```

### dashboard.py
```
[See dashboard.py in the repository for the full code.]
```

### fix_trader.py
```
[See fix_trader.py in the repository for the full code.]
```

---

## Contact & Support
For questions, improvements, or bug reports, please open an issue or contact the repository owner.

---

## Version
- Last major update: January 2026
- Smart Trainer V2, Robust Paper Trader V3, V2 Dashboard

---

## End of Summary
