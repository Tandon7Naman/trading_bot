from datetime import datetime, timezone, time
import pytz

# Configuration: Define your Local Timezone here
LOCAL_TZ = pytz.timezone('Asia/Kolkata')

def get_utc_now():
    """Protocol 4.1: Returns current time in UTC."""
    return datetime.now(timezone.utc)

def to_display_time(utc_dt_input):
    """Converts UTC to Local Time string for logs."""
    if utc_dt_input is None: return "Unknown"
    try:
        if isinstance(utc_dt_input, str):
            if utc_dt_input == "NOW": utc_dt = get_utc_now()
            else: utc_dt = datetime.fromisoformat(utc_dt_input)
        else:
            utc_dt = utc_dt_input
        
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
            
        local_dt = utc_dt.astimezone(LOCAL_TZ)
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return str(utc_dt_input)

# --- PROTOCOL 4.2: MARKET SESSIONS ---
def is_market_open(symbol):
    """
    Determines if the market is currently open for a specific asset.
    Returns: (bool, reason_string)
    """
    now_utc = get_utc_now()
    weekday = now_utc.weekday() # 0=Mon, 6=Sun
    current_time = now_utc.time()

    # --- XAUUSD (Global Spot) ---
    # Opens: Sunday 22:00 UTC -> Friday 22:00 UTC
    # Daily Break: 22:00 - 23:00 UTC (Rollover)
    if 'XAU' in symbol or 'GC=F' in symbol:
        # 1. Weekend Check (Friday 22:00 UTC to Sunday 22:00 UTC)
        if weekday == 4 and current_time >= time(22, 0): # Friday after 10PM UTC
            return False, "Weekend Close"
        if weekday == 5: # Saturday
            return False, "Weekend Close"
        if weekday == 6 and current_time < time(22, 0): # Sunday before 10PM UTC
            return False, "Weekend Close"
            
        # 2. Daily Rollover (22:00 - 23:00 UTC)
        # Note: This is a simplified rollover check.
        if current_time >= time(22, 0) and current_time < time(23, 0):
            return False, "Daily Rollover"
            
        return True, "Open"

    # --- MCX (India Gold) ---
    # Opens: 09:00 IST (03:30 UTC) -> 23:30 IST (18:00 UTC)
    # Weekends: Closed Sat/Sun
    elif 'MCX' in symbol:
        if weekday >= 5: # Sat or Sun
            return False, "Weekend Close"
            
        # UTC Equivalent of 9:00 AM IST - 11:30 PM IST
        start_utc = time(3, 30)
        end_utc = time(18, 0)
        
        if start_utc <= current_time <= end_utc:
            return True, "Open"
        return False, "Market Closed"

    # Default for others (Crypto is 24/7)
    return True, "Always Open"
from datetime import datetime, timezone
import pytz

# Configuration: Define your Local Timezone here (e.g., 'Asia/Kolkata')
LOCAL_TZ = pytz.timezone('Asia/Kolkata')

def get_utc_now():
    """
    Protocol 4.1: Returns the current time in UTC (Offset-Aware).
    ALL internal logic must use this.
    """
    return datetime.now(timezone.utc)

def to_display_time(utc_dt_input):
    """
    Converts a UTC timestamp to Local Time string for logs/console.
    Input can be a datetime object or an ISO string.
    """
    if utc_dt_input is None:
        return "Unknown"
        
    try:
        # If input is string (from JSON), parse it first
        if isinstance(utc_dt_input, str):
            if utc_dt_input == "NOW": 
                utc_dt = get_utc_now()
            else:
                utc_dt = datetime.fromisoformat(utc_dt_input)
        else:
            utc_dt = utc_dt_input

        # Ensure source is UTC
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
            
        # Convert to Local
        local_dt = utc_dt.astimezone(LOCAL_TZ)
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception:
        return str(utc_dt_input)
