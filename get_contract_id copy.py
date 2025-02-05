import requests
import os  # Import the os module to access environment variables
from os.path import join, dirname
from dotenv import load_dotenv
# Step 1: Get Access Token using OAuth2

# Define your Tradovate credentials (replace with your own)

username = os.getenv("TRADOVATE_USERNAME")           # Replace with your Tradovate username
password = os.getenv("TRADOVATE_PASSWORD")                  # Replace with your Tradovate password
client_id = os.getenv("TRADOVATE_CLIENT_ID")                         # Replace with your client ID
client_secret = os.getenv("TRADOVATE_CLIENT_SECRET")                # Replace with your client secret


# Token URL for Tradovate OAuth2
token_url = "https://api.tradovate.com/v1/auth/token"

# Request body for the token (OAuth2 password grant flow)
payload = {
    "client_id": client_id,
    "client_secret": client_secret,
    "grant_type": "password",  # Grant type for username/password OAuth flow
    "username": username,
    "password": password
}

# Send POST request to get access token
response = requests.post(token_url, data=payload)

# Check if the token request was successful
if response.status_code == 200:
    access_token = response.json().get('access_token')
    print("Access Token:", access_token)
else:
    # If the response is not JSON, print the raw response for debugging
    try:
        print("Failed to get access token:", response.json())  # Try to parse as JSON
    except requests.exceptions.JSONDecodeError:
        print("Failed to get access token. Raw response:", response.text)
    exit()  # Exit the script if the token request fails

# Step 2: Query the Tradovate API to get the contract ID for NQH5

# Set the API endpoint for instruments
instrument_url = "https://api.tradovate.com/v1/instruments"

# Headers with Authorization (Bearer token)
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Define the parameters for querying `NQ` contracts with expiration in March 2025 (NQH5)
params = {
    "symbol": "NQ",  # Symbol for E-mini Nasdaq
    "expiration": "2025-03-01"  # Expiration date for NQH5
}

# Send GET request to fetch instruments
response = requests.get(instrument_url, headers=headers, params=params)

# Check if the request was successful
if response.status_code == 200:
    contracts = response.json()

    # Loop through the contracts and find the one with the specific expiration (March 2025)
    for contract in contracts:
        if contract.get("expiration") == "2025-03-01":
            print(f"Contract ID for NQH5: {contract['contractId']}")
else:
    # If the response is not JSON, print the raw response for debugging
    try:
        print("Failed to fetch contract details:", response.json())  # Try to parse as JSON
    except requests.exceptions.JSONDecodeError:
        print("Failed to fetch contract details. Raw response:", response.text)