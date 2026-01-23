import logging
import os
import sys
import traceback
from datetime import datetime
from functools import wraps


def setup_institutional_logger():
    """Sets up a split-stream logger: Detailed File / Clean Console"""

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger("GoldBotInstitutional")
    logger.setLevel(logging.INFO)

    # Clear existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. SECURE FILE HANDLER (Detailed JSON-like structure)
    # Stores full stack traces, timestamps, and debug info.
    file_handler = logging.FileHandler("logs/audit_trace.log")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "loc": "%(filename)s:%(lineno)d", "msg": "%(message)s"}'
    )
    file_handler.setFormatter(file_fmt)

    # 2. SANITIZED CONSOLE HANDLER (User Friendly)
    # Only shows high-level info. No stack traces.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter('blaack_box_ai ➤ %(levelname)s: %(message)s')
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Singleton Logger Instance
logger = setup_institutional_logger()

def safe_execute(func):
    """Decorator: Catches crashes, logs detailed trace to file, shows simple error to user."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 1. Log the ugly details to the hidden file
            logger.error(f"CRITICAL FAULT in {func.__name__}: {str(e)}\n{traceback.format_exc()}")

            # 2. Show a polite message to the user
            print(f"\n⚠️  System Alert: The process '{func.__name__}' encountered an error.")
            print(f"    Reference ID: {int(datetime.now().timestamp())}")
            print("    Check logs/audit_trace.log for diagnostic details.\n")
            return None
    return wrapper
