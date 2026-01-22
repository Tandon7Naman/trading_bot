"""Quick Alpaca Connection Test"""

import os

from alpaca.trading.client import TradingClient
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get credentials
api_key = os.getenv("ALPACA_API_KEY", "")
api_secret = os.getenv("ALPACA_API_SECRET", "")

print("=" * 60)
print("ALPACA CONNECTION TEST")
print("=" * 60)

# Check if keys exist
if not api_key:
    print("❌ ALPACA_API_KEY not found in .env")
    print("✅ Add it to your .env file")
    exit()

if not api_secret:
    print("❌ ALPACA_API_SECRET not found in .env")
    print("✅ Add it to your .env file")
    exit()

# Show key info (first 15 chars only for security)
print(f"Key ID:  {api_key[:15]}...")
print(f"Secret:  {api_secret[:15]}...")
print(f"Key length:    {len(api_key)} chars")
print(f"Secret length: {len(api_secret)} chars")
print("=" * 60)

# Check if they're the same (common mistake)
if api_key == api_secret:
    print("\n❌ ERROR: Key and Secret are IDENTICAL!")
    print("They should be TWO DIFFERENT values from Alpaca")
    print("\n📋 Fix this:")
    print("1. Go to: https://app.alpaca.markets/paper/dashboard/api-keys")
    print("2. Generate NEW keys")
    print("3. Copy BOTH the Key ID AND Secret Key")
    print("4. Update your .env with both values")
    exit()

# Check if key starts with PK (paper trading)
if not api_key.startswith("PK"):
    print("\n⚠️  WARNING: Key doesn't start with 'PK'")
    print("Make sure you're using PAPER trading keys!")

print("\n🔄 Connecting to Alpaca...\n")

# Try to connect
try:
    client = TradingClient(api_key=api_key, secret_key=api_secret, paper=True)

    # Get account info
    account = client.get_account()

    print("✅ CONNECTION SUCCESSFUL!")
    print("=" * 60)
    print(f"Account Number: {account.account_number}")
    print(f"Status:         {account.status}")
    print(f"Balance:        ${float(account.equity):,.2f}")
    print(f"Buying Power:   ${float(account.buying_power):,.2f}")
    print("=" * 60)
    print("\n🎉 Your Alpaca setup is working perfectly!")
    print("✅ Ready for paper trading!\n")

except Exception as e:
    print("❌ CONNECTION FAILED!")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print("=" * 60)

    if "unauthorized" in str(e).lower():
        print("\n📋 This usually means:")
        print("   1. Wrong API key or secret")
        print("   2. Using Live keys instead of Paper keys")
        print("   3. Keys were regenerated (old ones expired)")

        print("\n✅ Solution:")
        print("   1. Go to: https://app.alpaca.markets/")
        print("   2. Make sure 'Paper Trading' is selected at top")
        print("   3. Go to 'API Keys' in left sidebar")
        print("   4. Delete existing keys")
        print("   5. Click 'Generate New Keys'")
        print("   6. Copy BOTH Key ID and Secret Key")
        print("   7. Update your .env file with both values\n")
