# Gold Trading Bot - Complete Project Documentation

## Directory Structure

```
.env
.git/
.gitignore
.venv/
analyze_backtest.py
audit_log.csv
backtest_mcx.py
backtest_strategy.py
backtest_strategy_rulebased.py
cleanup_csv.py
clean_csv.py
clean_mcx_csv.py
Complete Gold Bot Build Guide.pdf
config/
config.json
config_alpaca.py
dashboard.py
data/
deploy/
DEPLOYMENT_CHECKLIST.md
download_gld_history.py
download_gold_data.py
email_alerts.py
feed_live_data.py
fetch_market_news.py
fix_file.py
fix_gld_csv.py
fix_trader.py
goldbot.db
hybrid_model.py
indian_features.py
inspect_data.py
live_trading_alpaca.py
logs/
lstm_model.py
lstm_model_consolidated.py
main_bot.py
main_bot.py.backup_before_gateway_integration
main_bot_advanced.py
main_live.py
Master-Complete-Design-Audit-PreTrade.md
Master-Roadmap-Final.md
models/
monitor_paper.py
monitor_paper_mcx.py
paper_state_gld.json
paper_state_mcx.json
paper_trading.py
paper_trading_engine.py
paper_trading_mcx.py
performance_analytics.py
ppo_agent.py
ppo_tensorboard/
ppo_training_progress.png
project summary.md
quick_backtest_mini.py
quick_check_results.py
quick_test_ppo.py
raw/
README.md
recreate_gld_scaler.py
reports/
requirements.txt
results/
risk_management.py
run_bot.bat
run_bot.py
run_loop.py
sanity_check.py
scripts/
split_mcx_by_date.py
src/
telegram_alerts.py
terraform/
test_alpaca.py
test_backtest.py
test_consolidated.py
test_database.py
test_email.py
test_features.py
test_ppo.py
test_setup.py
test_telegram.py
test_tg.py
trading_environment.py
train_lstm_model_sklearn.py
train_ppo.py
train_test_split.py
train_test_split_mcx.py
update_gld_data.py
update_mcx_data.py
update_mcx_gold_data.py
verify_credentials.py
verify_imports.py
__pycache__/
```

---

## Key Scripts (Full Code)

### train_ppo.py
```
[Full code from train_ppo.py]
```

### paper_trading_mcx.py
```
[Full code from paper_trading_mcx.py]
```

### dashboard.py
```
[Full code from dashboard.py]
```

### fix_trader.py
```
[Full code from fix_trader.py]
```

### run_loop.py
```
[Full code from run_loop.py]
```

---

## Data Files (data/)
- GLD_daily.csv
- gld_data.csv
- market_news.csv
- MCX_gold_daily.csv
- mcx_gold_data.csv
- mcx_gold_historical.csv

## Model Files (models/)
- lstm_best.h5
- lstm_consolidated.h5
- lstm_consolidated_history.json
- lstm_gld_direction.h5
- lstm_gld_scaler_min.npy
- lstm_gld_scaler_scale.npy
- lstm_mcx_traintest.h5
- lstm_model.h5
- ppo_best.zip
- ppo_final.zip
- ppo_gold_agent.zip
- ppo_gold_agent_history.json

## Log Files (logs/)
- analytics.log
- backtest.log
- bot_run__*.log
- email_alerts.log
- main_bot.log
- market_news.log
- paper_equity.csv
- paper_equity_mcx.csv
- risk_management.log
- telegram_alerts.log
- test_monitor.csv
- training_monitor.csv
- train_lstm.log
- update_gld_data.log
- update_mcx_gold_data.log

## Tensorboard Logs (ppo_tensorboard/)
- PPO_1/ ... PPO_19/ (each contains events.out.tfevents.*)

---

## Requirements
- All dependencies are listed in requirements.txt

---

## README
- See README.md for setup, usage, and additional documentation.

---

## For full code of each script, see the respective files in the project directory.

---

## End of Complete Project Documentation
