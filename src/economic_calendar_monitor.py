import requests
import logging
from datetime import datetime, timedelta

class EconomicCalendarMonitor:
    """Monitor economic calendar for high-impact events."""
    def __init__(self):
        self.events = []
        self.high_impact_keywords = [
            'NFP', 'CPI', 'FOMC', 'ECB', 'RBI', 'GDP', 'ISM', 'PMI', 'Jobless Claims'
        ]
        self.last_fetch = None

    def fetch_calendar(self, days_ahead=2):
        try:
            # Placeholder API, replace with real calendar API
            url = "https://api.example.com/economic-calendar"
            params = {
                'date_from': datetime.now().date(),
                'date_to': (datetime.now() + timedelta(days=days_ahead)).date()
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                self.events = response.json()
                self.last_fetch = datetime.now()
                return self.events
        except Exception as e:
            logging.warning(f"Calendar fetch failed: {str(e)}")
        return []

    def get_next_high_impact_event(self, within_hours=4):
        now = datetime.now()
        for event in self.events:
            event_time = datetime.fromisoformat(event['date'])
            hours_until = (event_time - now).total_seconds() / 3600
            is_high_impact = any(kw in event['title'] for kw in self.high_impact_keywords)
            if 0 <= hours_until <= within_hours and is_high_impact:
                return {
                    'title': event['title'],
                    'time': event_time,
                    'hours_until': hours_until,
                    'impact': event.get('impact', 'MEDIUM')
                }
        return None

    def should_pause_trading(self):
        next_event = self.get_next_high_impact_event(within_hours=0.5)
        if next_event and next_event['impact'] in ['HIGH', 'VERY HIGH']:
            logging.warning(f"HIGH-IMPACT event in {next_event['hours_until']:.1f}h: {next_event['title']}")
            return True
        return False

if __name__ == "__main__":
    monitor = EconomicCalendarMonitor()
    monitor.fetch_calendar()
    if monitor.should_pause_trading():
        print("Trading paused due to high-impact event.")
    else:
        print("No imminent high-impact events.")
