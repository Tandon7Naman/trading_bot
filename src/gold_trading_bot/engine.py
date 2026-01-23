import os

import MetaTrader5 as mt5

# Load expected account ID from environment or config
expected_account_id = int(os.getenv("MT5_ACCOUNT_ID", "12345678"))  # Set this in your .env or config

current_account_id = mt5.account_info().login

if current_account_id != expected_account_id:
    raise PermissionError(f"SECURITY ALERT: Attempted to trade on unauthorized account {current_account_id}!")

# ...rest of your engine logic...
