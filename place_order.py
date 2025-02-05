import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Step 1: Get Access Token using OAuth2
username = os.getenv("TRADOVATE_USERNAME")
password = os.getenv("TRADOVATE_PASSWORD")
client_id = os.getenv("TRADOVATE_CLIENT_ID")
client_secret = os.getenv("TRADOVATE_CLIENT_SECRET")
DEVICE_ID = os.getenv("TRADOVATE_DEVICE_ID")
APP_ID = os.getenv("TRADOVATE_APP_ID")
APP_VERSION = os.getenv("TRADOVATE_APP_VERSION")

# Auth URL for Tradovate OAuth2 (Demo environment URL)
AUTH_URL = "https://demo.tradovateapi.com/v1/auth/accesstokenrequest"
API_BASE_URL = "https://demo.tradovateapi.com/v1" 

CONTRACT_SYMBOL = "NQH5"  # Example contract symbol (Gold Futures)
# CONTRACT_SYMBOL = "@NQ" 
ORDER_SIZE = 1   
# Headers for the authentication request
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

# Authentication data
data = {
    "name": username,
    "password": password,
    "appId": APP_ID,
    "appVersion": APP_VERSION,
    "deviceId": DEVICE_ID,
    "cid": client_id,
    "sec": client_secret
}

# Get Access Token
response = requests.post(AUTH_URL, headers=headers, json=data)

if response.status_code == 200:
    access_token = response.json().get("accessToken")
    print(f"Access Token: {access_token}")
else:
    print(f"Authentication failed: {response.status_code}")
    print(response.text)
    exit()

# Step 2: Place Entry Order (Market Order)

# URL to place entry order (Market Order)
ENTRY_URL = "https://demo.tradovateapi.com/v1/order/placeorder"

def get_account_id(token):
    account_list_url = f"{API_BASE_URL}/account/list"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(account_list_url, headers=headers)
    response.raise_for_status()
    accounts = response.json()
    if accounts:
        return accounts[0]["id"]
    raise ValueError("No accounts found for the authenticated user.")

account_id = get_account_id(access_token)  # Dynamically fetch account ID
# Create Market order (Entry order)
entry_order = {
    "accountSpec": username,         # Replace with your account username
    "accountId": account_id,                 # Replace with your account ID
    "action": "Buy",                       # Action to buy
    "symbol": CONTRACT_SYMBOL,
    "orderQty": ORDER_SIZE,                       # Quantity of contracts (1)
    "orderType": "Market",                 # Market order for entry
    "isAutomated": True                    # Set as automated order
}

# Place the entry order with a POST request
response = requests.post(ENTRY_URL, headers={
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}, json=entry_order)

# Check if the entry order was placed successfully
if response.status_code == 200:
    # response.raise_for_status()
    print(response.json())
    order_id = response.json()["orderId"]
    entry_price = response.json().get("price", 0.0)
    print(f"Order placed with Order ID: {order_id}, Entry Price: {entry_price}")
    # Now place the OCO order after entry
else:
    print(f"Failed to place entry order: {response.status_code}")
    print(response.text)
    exit()

# Step 3: Place OCO Order with Take Profit (TP) and Stop Loss (SL)

# URL to place OCO order
OCO_URL = "https://demo.tradovateapi.com/v1/order/placeoco"

# Create Limit order (Take Profit)
limit_order = {
    "action": "Sell",         # Sell action for TP
    "orderType": "Limit",     # Take Profit as Limit order
    # "orderType": "Market",     # Take Profit as Limit order
    "price": 22583.5          # Price at which you want to take profit (TP)

    # "orderType": "Stop",      # Stop order type (acts like a market order when triggered)
    # "stopPrice": 22583.5 
}

# Create Stop order (Stop Loss)
oco_order = {
    "accountSpec": username,         # Replace with your account username
    "accountId": account_id,                 # Replace with your account ID
    "action": "Sell",                       # Action to buy
    "symbol": CONTRACT_SYMBOL,
    "orderQty": ORDER_SIZE,                          # Quantity of contracts (1)
    "orderType": "Stop",                   # Stop Loss as Stop order
    # "price": 4100.00,
    "stopPrice": 18583.5,                     # Stop Loss price (SL)
    "isAutomated": True,                   # Set as automated order
    "other": limit_order                   # Linking the TP order to the OCO
}

# Place the OCO order with a POST request
response = requests.post(OCO_URL, headers={
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}, json=oco_order)

# Check if the OCO order was placed successfully
if response.status_code == 200:
    print(response.json())
    json_response = response.json()
    order_id = response.json()["ocoId"]
    # entry_price = response.json().get("price", 0.0)
    # print(f"Order placed with Order ID: {order_id}, Entry Price: {entry_price}")
    print(f"Order placed with Order ID: {order_id}")
else:
    print(f"Failed to place OCO order: {response.status_code}")
    print(response.text)
