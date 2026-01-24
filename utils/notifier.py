from telegram import Bot

from config.settings import TELEGRAM_CONFIG


class TelegramNotifier:

        @staticmethod
        def send_message_sync(text):
            import asyncio
            try:
                asyncio.run(TelegramNotifier.send_message(text))
            except RuntimeError:
                # If already in an event loop, schedule as a task
                loop = asyncio.get_event_loop()
                loop.create_task(TelegramNotifier.send_message(text))

        @staticmethod
        def notify_trade_sync(trade_type, price, size, sl, tp, sentiment):
            import asyncio
            try:
                asyncio.run(TelegramNotifier.notify_trade(trade_type, price, size, sl, tp, sentiment))
            except RuntimeError:
                loop = asyncio.get_event_loop()
                loop.create_task(TelegramNotifier.notify_trade(trade_type, price, size, sl, tp, sentiment))
    """Protocol 5.3: Real-time trade and system alerts."""

    _bot = None

    @staticmethod
    def get_bot():
        if TelegramNotifier._bot is None and TELEGRAM_CONFIG["enabled"]:
            # Using the token from your .env via settings
            TelegramNotifier._bot = Bot(token=TELEGRAM_CONFIG["bot_token"])
        return TelegramNotifier._bot

    @staticmethod
    async def send_message(text):
        bot = TelegramNotifier.get_bot()
        if bot:
            try:
                await bot.send_message(
                    chat_id=TELEGRAM_CONFIG["chat_id"], text=text, parse_mode="Markdown"
                )
            except Exception as e:
                print(f"   ⚠️ TELEGRAM ERROR: {e}")

    @staticmethod
    async def notify_trade(trade_type, price, size, sl, tp, sentiment):
        msg = (
            f"🔔 *TRADE EXECUTED: {trade_type}*\n"
            f"💰 *Price:* ${price:,.2f} | *Size:* {size}\n"
            f"🧠 *Sentiment:* {sentiment}\n"
            f"🛡️ *SL:* ${sl:,.2f} | 🎯 *TP:* ${tp:,.2f}"
        )
        await TelegramNotifier.send_message(msg)
