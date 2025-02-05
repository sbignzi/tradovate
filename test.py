import requests
import json
import websocket
import time



# API Credentials
USERNAME = "Mr_rich"
PASSWORD = "Richardson123$"
APP_ID = "wayneDemo"
APP_VERSION = "0.0.1"
DEVICE_ID = "1ac938f4-c2ef-1568-df33-bbe82eb8144a"
CLIENT_ID = 5014
CLIENT_SECRET = "1e581ca3-b8df-4539-b02f-0d0a6e8450f0"
CONTRACT_SYMBOL = "NQH5"  # Example contract symbol (Gold Futures)
# CONTRACT_SYMBOL = "@NQ"  # Example contract symbol (Gold Futures)
CONTRACT_SYMBOL = "ESH5"  # Example contract symbol (Gold Futures)
ORDER_SIZE = 1


# Authenticate and get access token
def authenticate():
    auth_url = "https://demo.tradovateapi.com/v1/auth/accessTokenRequest"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "name": USERNAME,
        "password": PASSWORD,
        "appId": APP_ID,
        "appVersion": APP_VERSION,
        "deviceId": DEVICE_ID,
        "cid": CLIENT_ID,
        "sec": CLIENT_SECRET
    }
    response = requests.post(auth_url, json=payload, headers=headers)
    response.raise_for_status()  # Check for errors
    response_data = response.json()
    print(f"Authentication Response: {response_data}")  # Debugging the response
    return response_data.get('mdAccessToken')

# Get access token
token = authenticate()
print(f"Access Token: {token}")
receive_data = True


# WebSocket URL
socket_url = 'wss://md.tradovateapi.com/v1/websocket'
# socket_url = 'wss://demo.tradovateapi.com/v1/websocket'
# socket_url = 'wss://md-demo.tradovateapi.com/v1/websocket'

# Prepare to decode server frames
def prepareMsg(raw):
    """ Parse the raw message into a frame type and payload """
    T = raw[0]  # The first character represents the frame type
    payload = None
    if len(raw) > 1:
        payload = json.loads(raw[1:])  # Parse the payload (JSON data)
    return T, payload

# Handle WebSocket frames
def on_message(ws, message):
    print("<== message", message)
    frame_type, payload = prepareMsg(message)
    
    if frame_type == 'o':
        print("Open frame received. Connection established.")
        auth_message = f"authorize\n2\n\n{token}"
        print(f"==> '{auth_message}'")
        ws.send(auth_message)
    
    elif frame_type == 'h':

        print("Heartbeat frame received. Responding with heartbeat.")
        global receive_data 
        if receive_data:
            chart_subscription_message = {
                "symbol": CONTRACT_SYMBOL,
                "chartDescription": {
                    "underlyingType": "MinuteBar",
                    "elementSize": 30,
                    "elementSizeUnit": "UnderlyingUnits",
                    "withHistogram": False,
                },
                "timeRange": {
                    "asMuchAsElements": 20
                }
            }

            # chart_subscription_message= {
            #     "symbol": CONTRACT_SYMBOL
            # }

            print(f"Subscribing to chart data: {json.dumps(chart_subscription_message)}")
            ws.send(f"md/getChart\n4\n\n{json.dumps(chart_subscription_message)}")
        # ws.send("[]")  # Send heartbeat response
        receive_data = False
    
    elif frame_type == 'a':
        print(f"Data frame received: {payload}")
        if payload:
            if 's' in payload[0] and payload[0]['s'] == 401:
                print(f"Access denied: {payload}")
            else:
                print(f"Received regular data: {json.dumps(payload, indent=2)}")
    
    elif frame_type == 'c':
        print(f"Connection closed: {payload}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, status_code, status_message):
    print(f"Connection closed: {status_code} {status_message}")
    # Optionally retry after a delay
    print("Reconnecting in 5 seconds...")
    # time.sleep(5)
    # ws.run_forever()

def on_open(ws):
    print("WebSocket connected.")
    
    # Send authorization request with the token
    # auth_message = f"authorize\n2\n\n{token}"
    # print(f"==> '{auth_message}'")
    # ws.send(auth_message)
    # print(f"==> Authentication sent with token: '{token}'")

    # Correct subscription to market data (DOM)
    subscribe_message = {
        "method": "md/subscribeDOM",
        "params": {
            "symbol": CONTRACT_SYMBOL  # Example contract symbol (e.g., "ESM2")
        }
    }

    # print(f"Subscribing to market data with: {json.dumps(subscribe_message)}")  # Log subscription request
    # ws.send(f"md/subscribeDOM\n3\n{json.dumps(subscribe_message)}")  # Send subscription request for DOM data
    # print(f"Subscribed to market data for symbol {CONTRACT_SYMBOL}.")

    # If you're subscribing to chart data (alternative request)
    chart_subscription_message = {
        "symbol": CONTRACT_SYMBOL,
        "chartDescription": {
            "underlyingType": "MinuteBar",
            "elementSize": 30,
            "elementSizeUnit": "UnderlyingUnits",
            "withHistogram": False,
        },
        "timeRange": {
            "asMuchAsElements": 20
        }
    }

    # chart_subscription_message= {
    #     "symbol": CONTRACT_SYMBOL
    # }

    print(f"Subscribing to chart data: {json.dumps(chart_subscription_message)}")
    # ws.send(f"md/getChart\n4\n\n{json.dumps(chart_subscription_message)}")  # Send subscription request for chart data
    # ws.send(f"md/getchart\n3\n{json.dumps(chart_subscription_message)}")
    # ws.send(f"md/subscribeQuote\n3\n{json.dumps(chart_subscription_message)}")
    print(f"Subscribed to chart data for symbol {CONTRACT_SYMBOL}.")

# WebSocket client setup
def run_websocket():
    ws = websocket.WebSocketApp(
        socket_url, 
        on_message=on_message, 
        on_error=on_error, 
        on_close=on_close, 
        on_open=on_open
    )
    
    # Run WebSocket with ping settings
    ws.run_forever()

# Run the WebSocket connection
run_websocket()
