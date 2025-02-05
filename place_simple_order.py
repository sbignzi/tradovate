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
def get_account_id(token):
    account_list_url = f"{API_BASE_URL}/account/list"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(account_list_url, headers=headers)
    response.raise_for_status()
    accounts = response.json()
    if accounts:
        return accounts[0]["id"]
    raise ValueError("No accounts found for the authenticated user.")
def place_market_order(token):
    account_id = get_account_id(token)  # Dynamically fetch account ID
    order_url = f"{API_BASE_URL}/order/placeorder"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    order_data = {
        "accountSpec": USERNAME,
        "accountId": account_id,
        "action": "Sell",
        "symbol": CONTRACT_SYMBOL,
        "orderQty": ORDER_SIZE,
        "orderType": "Market",
        "isAutomated": True
    }
    print("Placing order with data:", order_data)
    response = requests.post(order_url, headers=headers, json=order_data)
    response.raise_for_status()
    order_id = response.json()["orderId"]
    entry_price = response.json().get("price", 0.0)
    print(f"Order placed with Order ID: {order_id}, Entry Price: {entry_price}")
    return order_id, entry_price
# Function to monitor position and exit on profit/loss targets
def monitor_position(token, entry_price, order_id):
    while True:
        # Check current price
        price_url = f"{API_BASE_URL}/market/price/{CONTRACT_SYMBOL}"
        headers = {"Authorization": f"Bearer {token}"}
        price_response = requests.get(price_url, headers=headers)
        price_response.raise_for_status()
        current_price = price_response.json()["price"]
        # Calculate profit or loss
        profit_loss = current_price - entry_price * ORDER_SIZE
        print(f"Current P/L: ${profit_loss:.2f}")
        # Exit on target profit or max loss
        if profit_loss >= TARGET_PROFIT or profit_loss <= MAX_LOSS:
            exit_position(token, order_id)
            print(f"Exited position with P/L: ${profit_loss:.2f}")
            break
        time.sleep(5)  # Check every 5 seconds
# Function to exit the position
def exit_position(token, order_id):
    close_url = f"{API_BASE_URL}/order/cancelorder"
    headers = {"Authorization": f"Bearer {token}"}
    close_data = {
        "orderId": order_id
    }
    requests.post(close_url, headers=headers, json=close_data)
# Schedule the order for 10 AM AEST
def place_order():
    token = authenticate()
    place_market_order(token)
# Schedule job for 10:00 AM AEST (convert to UTC)
# aest_time = datetime.now() + timedelta(hours=10)  # Convert to AEST
# target_time = aest_time.replace(hour=8, minute=51, second=0, microsecond=0)
# schedule.every().day.at(target_time.strftime("%H:%M")).do(schedule_order)
# while True:
#     schedule.run_pending()
#     time.sleep(1)

place_order()