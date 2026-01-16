# 🤖 AI-Powered Gold Trading Bot (MCX India)

An automated algorithmic trading bot designed for the Indian Multi Commodity Exchange (MCX). This project uses Deep Learning (LSTM) and Reinforcement Learning (PPO) to predict Gold prices and execute trades autonomously.

![Status](https://img.shields.io/badge/Status-Active-green) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Market](https://img.shields.io/badge/Market-MCX%20India-orange)

## 🚀 Key Features

* **Dual-Brain Architecture**:
    * **Analyst (LSTM)**: Predicts future price trends based on historical data.
    * **Trader (PPO)**: Reinforcement Learning agent that decides whether to Buy, Sell, or Hold based on the Analyst's data and current profit/loss.
* **Live Paper Trading**: Runs in a loop, simulating real-time trading with live data updates.
* **Smart Backtesting**: Validates strategies against historical data (2021-2025) with realistic commission/slippage simulations.
* **Instant Alerts**: Sends real-time notifications via **Telegram** whenever a trade is executed.
* **Robust Data Handling**: Automatically updates dataset using global Gold proxies (`GC=F`) to estimate live Indian market movement.

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/Tandon7Naman/trading_bot.git](https://github.com/Tandon7Naman/trading_bot.git)
    cd trading_bot
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment**
    Create a `.env` file (or set environment variables) for your Telegram keys:
    ```
    TELEGRAM_BOT_TOKEN=your_token_here
    TELEGRAM_CHAT_ID=your_chat_id_here
    ```

## 🖥️ Usage

### 1. Train the Agent
To teach the bot from scratch using historical data:
```bash
python train_ppo.py
```

### 2. Run Paper Trading
To simulate live trading with the latest data:
```bash
python run_loop.py
```

### 3. Backtest Strategies
To evaluate performance on historical data:
```bash
python backtest_mcx.py
```

## 📊 Project Structure

- `train_ppo.py` — Train the PPO agent
- `lstm_model.py` — LSTM price prediction
- `backtest_mcx.py` — Backtesting engine
- `feed_live_data.py` — Simulate live MCX data
- `run_loop.py` — Automated trading loop
- `telegram_alerts.py` — Telegram notification system
- `paper_trading_mcx.py` — Paper trading logic
- `data/` — Market data files
- `models/` — Saved models and scalers

## ⚠️ Disclaimer
This project is for educational and research purposes only. It is **not** financial advice. Use at your own risk.

---

Made with ❤️ by Naman Tandon
