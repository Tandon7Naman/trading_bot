# Gold Trading Bot: Deployment Checklist

This checklist outlines the steps to deploy and run the gold trading bot in a production environment on a Windows machine.

---

### 1. Environment Setup

- [ ] **Install Python**: Ensure Python 3.10+ is installed and added to the system's PATH.
- [ ] **Create Virtual Environment**:
  ```bash
  python -m venv .venv
  ```
- [ ] **Activate Virtual Environment**:
  ```bash
  .venv\Scripts\activate
  ```
- [ ] **Install Dependencies**: Install the exact required versions for stability.
  ```bash
  pip install -r requirements.txt
  ```

---

### 2. Configuration

- [ ] **API Keys**: Open `config.json`.
- [ ] **Alpaca**: Fill in your `paper_api_key` and `paper_api_secret` for paper trading.
- [ ] **Telegram**: Fill in your `telegram_token` and `telegram_chat_id` to enable alerts.
- [ ] **Trading Parameters**: Review and adjust `trade_parameters` in `config.json` if needed (e.g., `trade_risk_per_trade`, `atr_multiplier`).

---

### 3. Initial Data & Model

- [ ] **Run Initial Download**: Execute the main bot script once manually to ensure it downloads the initial historical data (`gld_data.csv`) and creates the necessary log files (`audit_log.csv`, `paper_equity.csv`).
  ```bash
  python main_bot.py
  ```
- [ ] **Verify Files**: Check that `data/gld_data.csv`, `logs/audit_log.csv`, and `logs/paper_equity.csv` have been created.

---

### 4. Production Deployment (Windows Task Scheduler)

- [ ] **Open Task Scheduler**: Search for "Task Scheduler" in the Windows Start Menu.
- [ ] **Create Basic Task**:
    - In the right-hand pane, click "Create Basic Task...".
    - **Name**: `Gold Trading Bot`
    - **Description**: `Runs the automated gold trading bot daily.`
- [ ] **Trigger**:
    - Select "Daily".
    - **Start time**: Set it to a time when the market is closed, e.g., `8:00 PM`. This ensures the bot prepares for the next day's session without interfering with active trading hours.
- [ ] **Action**:
    - Select "Start a program".
    - **Program/script**: Browse to and select the `run_bot.bat` file in your project directory.
    - **Start in (optional)**: Set this to your project's root directory (e.g., `C:\path\to\your\gold-trading-bot`). This is crucial for ensuring the script can find all relative paths (`data`, `logs`, etc.).
- [ ] **Finish**:
    - Review the settings and click "Finish".
- [ ] **Configure for Reliability**:
    - Find the newly created task in the Task Scheduler Library.
    - Right-click it and select "Properties".
    - Go to the "Conditions" tab.
    - **Uncheck** "Start the task only if the computer is on AC power". This is important if you are running on a laptop.
    - Go to the "Settings" tab.
    - **Check** "Run task as soon as possible after a scheduled start is missed".
    - **Check** "If the task fails, restart every:" and set it to `1 hour` with `3` attempts.
    - Click "OK".

---

### 5. Monitoring

- [ ] **Check Logs Daily**:
    - `logs/audit_log.csv`: Review daily for trade decisions, errors, and status updates.
    - `logs/paper_equity.csv`: Monitor the bot's performance over time.
- [ ] **Telegram Alerts**: Ensure you are receiving alerts for trades and potential errors.
- [ ] **Task Scheduler Status**: Periodically check the "Last Run Result" in Task Scheduler to ensure the task is running successfully (status `0x0`).

---
