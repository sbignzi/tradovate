import json
import requests
import asyncio
import websockets
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Tradovate API Credentials
USERNAME = os.getenv("TRADOVATE_USERNAME")
PASSWORD = os.getenv("TRADOVATE_PASSWORD")
CLIENT_ID = os.getenv("TRADOVATE_CLIENT_ID")
CLIENT_SECRET = os.getenv("TRADOVATE_CLIENT_SECRET")
DEVICE_ID = os.getenv("TRADOVATE_DEVICE_ID")
APP_ID = os.getenv("TRADOVATE_APP_ID")
APP_VERSION = os.getenv("TRADOVATE_APP_VERSION")

# API Endpoints
AUTH_URL = "https://demo.tradovateapi.com/v1/auth/accesstokenrequest"
WS_URL = "wss://demo.tradovateapi.com/v1/websocket"

# Contract Symbol & Timeframe
SYMBOL = "MNQZ1"  # Example contract
ELEMENT_SIZE = 5  # 5-minute bars
NUM_BARS = 500    # Number of historical bars to fetch

# Get timestamp for 3 days ago
three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat() + "Z"

# Store historical and real-time subscription IDs
subscription_ids = {"historicalId": None, "realtimeId": None}


### Step 1: Authenticate & Get Access Token
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
        return response.json().get("accessToken")
    else:
        print("Authentication Failed:", response.status_code, response.text)
        return None


### Step 2: WebSocket Handling
async def on_message(message):
    """Handles incoming WebSocket messages"""
    data = json.loads(message)

    if "e" in data and data["e"] == "chart":
        for chart in data["d"]["charts"]:
            if chart["id"] == subscription_ids["historicalId"]:  # Match historical data
                bars = chart["bars"]
                print(f"📊 Received {len(bars)} historical bars")
                print(bars[:20])  # Print first 20 bars for preview
                return  # Exit after receiving data

async def fetch_chart_data():
    """Connects to WebSocket and subscribes to chart data"""
    access_token = authenticate()
    if not access_token:
        return

    async with websockets.connect(WS_URL) as ws:
        print("✅ WebSocket Connected!")

        # Send Authentication
        auth_request = {
            "op": "authorize",
            "token": access_token
        }
        await ws.send(json.dumps(auth_request))

        # Request Historical Chart Data
        chart_request = {
            "op": "subscribe",
            "args": {
                "url": "md/getchart",
                "body": {
                    "symbol": SYMBOL,
                    "chartDescription": {
                        "underlyingType": "MinuteBar",
                        "elementSize": ELEMENT_SIZE,
                        "elementSizeUnit": "UnderlyingUnits",
                        "withHistogram": False
                    },
                    "timeRange": {
                        "asFarAsTimestamp": three_days_ago,
                        "asMuchAsElements": NUM_BARS
                    }
                }
            }
        }
        await ws.send(json.dumps(chart_request))

        # Listen for messages using on_message
        async for message in ws:
            await on_message(message)

        print("✅ WebSocket Closed")


# Run the WebSocket function
asyncio.run(fetch_chart_data())