from datetime import datetime

import requests


class GeopoliticalRiskMonitor:
    RISK_EVENTS = [
        "US-China tensions",
        "Middle East conflict",
        "Russia-Ukraine",
        "Israel-Palestine",
        "Taiwan strait",
        "North Korea",
    ]

    @staticmethod
    def fetch_risk_sentiment():
        try:
            url = "https://newsapi.org/v2/everything?q=geopolitical+risk&sortBy=publishedAt"
            # You must provide your own API key for NewsAPI or similar
            headers = {"Authorization": "Bearer YOUR_API_KEY"}
            response = requests.get(url, headers=headers, timeout=5)
            articles = response.json().get("articles", [])
            risk_score = 0
            for article in articles[:10]:
                pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                if (datetime.now(pub_date.tzinfo) - pub_date).total_seconds() < 86400:
                    for risk_event in GeopoliticalRiskMonitor.RISK_EVENTS:
                        if risk_event.lower() in article["title"].lower():
                            risk_score += 1
            if risk_score > 5:
                return "HIGH"
            elif risk_score > 2:
                return "MEDIUM"
            else:
                return "LOW"
        except Exception as e:
            print(f"Operation failed: {e}")
            return "UNKNOWN"


if __name__ == "__main__":
    print("Geopolitical Risk:", GeopoliticalRiskMonitor.fetch_risk_sentiment())
