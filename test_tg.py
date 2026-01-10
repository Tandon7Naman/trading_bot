from telegram_alerts import TelegramAlerts

# Get these from your config.json
bot_token = "8514442345:AAF5Yg0HD2gwgkICtZDu1EVwHW3fCI6rdX0"
chat_id = "8410246010"

alerts = TelegramAlerts(bot_token, chat_id)

print("[*] Sending test message to Telegram...")
if alerts.send_message("✅ Gold Trading Bot is configured and online!"):
    print("[+] SUCCESS! Check your Telegram")
else:
    print("[-] FAILED - Check bot token and chat ID")
