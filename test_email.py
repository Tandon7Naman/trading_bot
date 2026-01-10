from email_alerts import EmailAlerts

# Get these from your config.json
sender_email = "tandonnaman4@gmail.com"
app_password = "pfld mdhg lqkc oknl"
recipient_email = "tandonnaman4l@gmail.com"

email = EmailAlerts(sender_email, app_password, recipient_email)

print("[*] Sending test email...")
if email.send_email("Gold Trading Bot Test", "Your bot is configured and ready!"):
    print("[+] SUCCESS! Check your email inbox")
else:
    print("[-] FAILED - Check email and password in config.json")
