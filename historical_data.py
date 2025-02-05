import json
import requests
# import schedule
import time
import os  # Import the os module to access environment variables
from os.path import join, dirname
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
# Tradovate API credentials
USERNAME = os.getenv("TRADOVATE_USERNAME")           # Replace with your Tradovate username
PASSWORD = os.getenv("TRADOVATE_PASSWORD")                  # Replace with your Tradovate password
CLIENT_ID = os.getenv("TRADOVATE_CLIENT_ID")                         # Replace with your client ID
CLIENT_SECRET = os.getenv("TRADOVATE_CLIENT_SECRET")                # Replace with your client secret
DEVICE_ID = os.getenv("TRADOVATE_DEVICE_ID")  # Unique device ID (use a generated UUID if needed)
APP_ID = os.getenv("TRADOVATE_APP_ID")                 # Typically "Tradovate Trader"
APP_VERSION = os.getenv("TRADOVATE_APP_VERSION")                      # Application version
# Market order parameters
TARGET_PROFIT = 200   # $200 target profit
MAX_LOSS = -100       # $100 max loss
CONTRACT_SYMBOL = "GCZ4"  # December Gold Futures Contract
CONTRACT_SYMBOL = "NQH5"  # Example contract symbol (Gold Futures)
# CONTRACT_SYMBOL = "@NQ" 
ORDER_SIZE = 1        # Number of contracts to buy/sell
# Define base URLs
AUTH_URL = "https://demo.tradovateapi.com/v1/auth/accesstokenrequest"  # Authentication endpoint
API_BASE_URL = "https://demo.tradovateapi.com/v1"                      # Base URL for demo account actions
# Function to authenticate and obtain an access token
def authenticate():
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "name": USERNAME,
        "password": PASSWORD,
        "appId": APP_ID,
        "appVersion": APP_VERSION,
        "deviceId": DEVICE_ID,
        "cid": CLIENT_ID,
        "sec": CLIENT_SECRET
    }
    response = requests.post(AUTH_URL, headers=headers, json=data)
    if response.status_code == 200:
        access_token = response.json().get("accessToken")
        print(f"Access Token: {access_token}")
        return access_token
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        return None

# Tradovate API credentials (replace these)
# ACCESS_TOKEN = "your_access_token"  # Replace with your actual token
BASE_URL = "https://demo.tradovateapi.com/v1"  # Use live URL if needed

# Contract Symbol (e.g., MNQZ1, MES, NQ, ES, etc.)
SYMBOL = "MNQZ1"  # Replace with your contract symbol

# Calculate the timestamp for 3 days ago
three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z"

# API Request payload
payload = {
    "symbol": SYMBOL,
    "chartDescription": {
        "underlyingType": "MinuteBar",  # Options: "MinuteBar", "DailyBar", "Tick"
        "elementSize": 5,  # 5-minute bars (adjust as needed)
        "elementSizeUnit": "UnderlyingUnits",
        "withHistogram": False
    },
    "timeRange": {
        "asFarAsTimestamp": three_days_ago,  # Start from 3 days ago
        "asMuchAsElements": 500  # Number of bars (adjust based on needs)
    }
}

# Send request to Tradovate API
ACCESS_TOKEN = authenticate()
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

response = requests.post(f"{BASE_URL}/md/getchart", headers=headers, data=json.dumps(payload))

# Parse response
if response.status_code == 200:
    data = response.json()
    print("Historical Chart Data:", data)
else:
    print("Error:", response.status_code, response.text)