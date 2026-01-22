from utils.exceptions import NewsEventError
from utils.time_utils import get_utc_now


class NewsFilter:
    """
    Protocol 4.2: Economic Calendar Filter.
    Blocks trading during High-Impact News (NFP, CPI, FOMC).
    """

    # Example Blocklist (UTC Times)
    # Format: "YYYY-MM-DD": [("HH:MM", "HH:MM")]
    BLOCKED_WINDOWS = {
        "2026-01-20": [("13:30", "15:00")],  # Example: CPI Data Release
        "2026-02-06": [("13:30", "16:00")],  # Example: NFP Friday
    }

    @staticmethod
    def can_trade(symbol="XAUUSD"):
        """
        Checks if the current time is inside a 'No Trade Zone'.
        Returns: True (Safe) or False (Danger).
        """
        now_utc = get_utc_now()
        date_str = now_utc.strftime("%Y-%m-%d")

        # Check if today has news
        if date_str in NewsFilter.BLOCKED_WINDOWS:
            ranges = NewsFilter.BLOCKED_WINDOWS[date_str]
            current_time_str = now_utc.strftime("%H:%M")

            for start, end in ranges:
                if start <= current_time_str <= end:
                    raise NewsEventError(f"High Impact News Event ({start}-{end} UTC)")

        return True
