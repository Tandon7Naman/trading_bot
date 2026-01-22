from datetime import UTC, datetime

import pytz

from config.settings import ASSET_CONFIG


def get_utc_now():
    """Returns current time in UTC."""
    return datetime.now(UTC)


def to_display_time(dt_obj):
    if isinstance(dt_obj, str):
        return dt_obj
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S")


def is_market_open(symbol):
    """
    Protocol 9.0: Data-Driven Market Schedule.
    Reads opening hours from config.settings instead of hardcoding.
    """
    config = ASSET_CONFIG.get(symbol)
    if not config:
        return False, "Unknown Asset"

    # 1. Weekend Check (Universal)
    now_utc = get_utc_now()
    if now_utc.weekday() == 5:
        return False, "Weekend (Sat)"
    if now_utc.weekday() == 6 and config["type"] == "FUTURES":
        # Complex logic for Sunday Open skipped for brevity
        return False, "Weekend (Sun)"

    # 2. Schedule Check
    schedule = config["schedule"]
    tz_name = schedule["timezone"]

    # Convert UTC now to Target Timezone
    target_tz = pytz.timezone(tz_name)
    now_target = now_utc.astimezone(target_tz).time()

    # Parse Config Times
    open_t = datetime.strptime(schedule["open_time"], "%H:%M").time()
    close_t = datetime.strptime(schedule["close_time"], "%H:%M").time()

    if open_t <= now_target <= close_t:
        return True, "Market Open"
    else:
        return False, f"Closed ({schedule['open_time']}-{schedule['close_time']} {tz_name})"


def get_asset_physics(symbol):
    """Returns physics dict for the requested symbol."""
    return ASSET_CONFIG.get(symbol, {})
