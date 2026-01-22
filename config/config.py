import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    ALGO_ID = os.getenv("ALGO_ID", "TEST_BOT")
    STATIC_IP = os.getenv("STATIC_IP", "0.0.0.0")
    MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "5000"))
    CAPITAL = float(os.getenv("CAPITAL", "100000"))
    IS_PAPER_TRADING = os.getenv("TRADING_MODE", "0") != "1"
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    AUDIT_FILE = os.path.join(BASE_DIR, "audit_log.csv")

    @classmethod
    def print_config(cls):
        print("\n" + "=" * 50)
        print("⚙️  BOT CONFIGURATION")
        print("=" * 50)
        print(f"Bot ID:           {cls.ALGO_ID}")
        print(
            f"Mode:             {'📄 PAPER TRADING' if cls.IS_PAPER_TRADING else '💰 LIVE TRADING'}"
        )
        print(f"Capital:          ₹{cls.CAPITAL:,.0f}")
        print(f"Max Daily Loss:   ₹{cls.MAX_DAILY_LOSS:,.0f}")
        print(f"Static IP:        {cls.STATIC_IP}")
        print("=" * 50 + "\n")


if __name__ == "__main__":
    Config.print_config()
