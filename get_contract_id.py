import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Step 1: Get Access Token using OAuth2

# Define your Tradovate credentials from environment variables
username = os.getenv("TRADOVATE_USERNAME")
password = os.getenv("TRADOVATE_PASSWORD")
client_id = os.getenv("TRADOVATE_CLIENT_ID")
client_secret = os.getenv("TRADOVATE_CLIENT_SECRET")
DEVICE_ID = os.getenv("TRADOVATE_DEVICE_ID")
APP_ID = os.getenv("TRADOVATE_APP_ID")
APP_VERSION = os.getenv("TRADOVATE_APP_VERSION")

# Token URL for Tradovate OAuth2 (Demo environment URL)
AUTH_URL = "https://demo.tradovateapi.com/v1/auth/accesstokenrequest"

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

# Send POST request to get access token
response = requests.post(AUTH_URL, headers=headers, json=data)

# Check if the token request was successful
if response.status_code == 200:
    # Get access token
    if 'accessToken' in response.json():
        access_token = response.json().get("accessToken")
        print(f"Access Token: {access_token}")
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        exit()  # Exit the script if authentication fails
else:
    print(f"Authentication failed: {response.status_code}")
    print(response.text)
    exit()

# Step 2: Query the Tradovate API to get the contract ID for NQH5

# Base URL for the demo API
API_BASE_URL = "https://demo.tradovateapi.com/v1"  # Using demo environment URL
instrument_url = f"{API_BASE_URL}/instruments"

# Headers for the instrument request
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Send GET request to fetch all instruments (no filters)
response = requests.get(instrument_url, headers=headers)

if response.status_code == 200:
    contracts = response.json()

    # Print all available instruments for debugging
    print("Available Contracts:")
    for contract in contracts:
        print(contract)
else:
    print(f"Failed to fetch contract details: {response.status_code}")
    print("Raw response:", response.text)  # Print the raw response for debugging
