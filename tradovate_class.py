import requests
import json
import websocket
import os  # Import the os module to access environment variables
from os.path import join, dirname
from dotenv import load_dotenv
import csv
import time
from datetime import datetime
import threading
# Load the environment variables
# load_dotenv()

dotenv_path = join(dirname(__file__), '.env')
load_dotenv()

class TradovateAPI:
    def __init__(self, contract_symbol):
        self.username = os.getenv("TRADOVATE_USERNAME")
        self.password = os.getenv("TRADOVATE_PASSWORD")
        self.app_id = os.getenv("TRADOVATE_APP_ID")
        self.app_version = os.getenv("TRADOVATE_APP_VERSION")
        self.device_id = os.getenv("TRADOVATE_DEVICE_ID")
        self.client_id = os.getenv("TRADOVATE_CLIENT_ID")
        self.client_secret = os.getenv("TRADOVATE_CLIENT_SECRET")
        self.contract_symbol = contract_symbol
        self.token = None
        self.receive_data = True
        self.socket_url = 'wss://md.tradovateapi.com/v1/websocket'

        # CSV file to save OHLC data
        self.csv_file = 'ohlc_data.csv'

        self.last_heartbeat_time = None
        self.heartbeat_interval = 5  # seconds   

        # print("username", self.username)
        # print("self.password", self.password)
    
    def authenticate(self):
        """Authenticate and get access token"""
        auth_url = "https://demo.tradovateapi.com/v1/auth/accessTokenRequest"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "name": self.username,
            "password": self.password,
            "appId": self.app_id,
            "appVersion": self.app_version,
            "deviceId": self.device_id,
            "cid": self.client_id,
            "sec": self.client_secret
        }
        response = requests.post(auth_url, json=payload, headers=headers)
        response.raise_for_status()  # Check for errors
        response_data = response.json()
        # print(f"Authentication Response: {response_data}")  # Debugging the response
        self.token = response_data.get('mdAccessToken')
        print(f"Access Token: {self.token}")

    def save_to_csv(self, timestamp, open_price, high_price, low_price, close_price):
        """Append the extracted data to the CSV file"""
           # Initialize CSV with headers if the file doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Open', 'High', 'Low', 'Close'])

        with open(self.csv_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, open_price, high_price, low_price, close_price])
   
    def send_heartbeat(self, ws):
        # global last_heartbeat_time

        # while True:
        #     # Wait for 5 seconds before sending the next heartbeat
        #     time.sleep(self.heartbeat_interval)
        # print("aaammmm heeeeeeeeere")
        # Only send a heartbeat if it's been 5 seconds since the last one
        if self.last_heartbeat_time is None or (time.time() - self.last_heartbeat_time >= self.heartbeat_interval):
            print("Sending heartbeat...")
            ws.send('h')  # Send heartbeat ('h' frame)
            # print("Heartbeat sent.")
            self.last_heartbeat_time = time.time()  # Update the last heartbeat time
    
    def heartbeat_loop(self, ws):
        """This loop runs in a separate thread to send heartbeats periodically"""
        while True:
            self.send_heartbeat(ws)
            time.sleep(1)

    def prepare_msg(self, raw):
        """Parse the raw message into a frame type and payload"""
        # T = raw[0]  # The first character represents the frame type
        # payload = None
        # if len(raw) > 1:
        #     payload = json.loads(raw[1:])  # Parse the payload (JSON data)
        # return T, 

        try:
            T = raw[0]  # The first character represents the frame type
            payload = None
            if len(raw) > 1:
                payload = json.loads(raw[1:])  # Parse the payload (JSON data)
            return T, payload
        except json.JSONDecodeError as e:
            # print(f"JSON decoding error: {e} for message: {raw}")
            return None, None  # Return None if the message can't be parsed

   
    def on_message(self, ws, message):
        # time.sleep(1)
        """Handle WebSocket frames"""
        # print("<== message", message)
        frame_type, payload = self.prepare_msg(message)
        # message to websocket to say we are here (to not disconnect)
        # self.send_heartbeat(ws)

        if frame_type == 'o':
            print("Open frame received. Connection established.")
            # auth_message = f"authorize\n2\n\n{self.token}"
            # print(f"==> '{auth_message}'")
            # ws.send(auth_message)
            time.sleep(1)
        
        elif frame_type == 'h':
            print("Heartbeat frame received. Responding with heartbeat.")
            # self.send_heartbeat(ws)

        elif frame_type == 'a':
            # print(f"Data frame received: {payload}")
            if payload:
                if 's' in payload[0] and payload[0]['s'] == 401:
                    print(f"Access denied: {payload}")
                else:
                    # print(f"Received regular data: {json.dumps(payload, indent=2)}")
                    # print(payload[0].get('d', {}).get('quotes', []))
                    for quote in payload[0].get('d', {}).get('quotes', []):
                        # Extract the necessary OHLC fields from the quote
                        timestamp = quote.get('timestamp')
                        opening_price = quote.get('entries', {}).get('OpeningPrice', {}).get('price')
                        high_price = quote.get('entries', {}).get('HighPrice', {}).get('price')
                        low_price = quote.get('entries', {}).get('LowPrice', {}).get('price')
                        close_price = quote.get('entries', {}).get('Trade', {}).get('price')
                        
                        # Convert timestamp to datetime format
                        timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')

                        # Save the extracted data to CSV
                        self.save_to_csv(timestamp_dt, opening_price, high_price, low_price, close_price)
                        # print(f"Saved data: {timestamp_dt}, Open: {opening_price}, High: {high_price}, Low: {low_price}, Close: {close_price}")
        
        elif frame_type == 'c':
            print(f"Connection closed: {payload}")

        # self.send_heartbeat(ws)

    def on_error(self, ws, error):
        print(f"Error: {error}")

    def on_close(self, ws, status_code, status_message):
        print(f"Connection closed: {status_code} {status_message}")
        print("Reconnecting in 0.5 seconds...")
        # Optionally retry after a delay
        time.sleep(5)
        ws.run_forever(ping_interval=60, ping_timeout=30)



    def on_open(self, ws):
        print("WebSocket connected.")
    
        auth_message = f"authorize\n2\n\n{self.token}"
        print(f"==> '{auth_message}'")
        ws.send(auth_message)
        print("requesting data ...")

        chart_subscription_message = {
        "symbol": self.contract_symbol,
        "chartDescription": {
            "underlyingType": "MinuteBar",
            "elementSize": 60,  # 30 seconds per bar
            "elementSizeUnit": "UnderlyingUnits",
            "withHistogram": False,
        },
        "timeRange": {
            "liveUpdate": True  # Assuming 'liveUpdate' or equivalent keeps data flowing continuously
        }
    }

        subscription_message = {
        "symbol": self.contract_symbol
    }
        # Start the heartbeat loop in a separate thread to run concurrently
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, args=(ws,))
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        # print(f"Subscribing to chart data: {json.dumps(chart_subscription_message)}")
        # ws.send(f"md/getChart\n4\n\n{json.dumps(chart_subscription_message)}")
        print(f"Subscribing to quote data: {json.dumps(subscription_message)}")
        ws.send(f"md/subscribeQuote\n4\n\n{json.dumps(subscription_message)}")

    def run_websocket(self):
        ws = websocket.WebSocketApp(
            self.socket_url, 
            on_message=self.on_message, 
            on_error=self.on_error, 
            on_close=self.on_close, 
            on_open=self.on_open
        )
        
        # ws.run_forever()
        ws.run_forever(ping_interval=60, ping_timeout=30)
        

# API Credentials
CONTRACT_SYMBOL = "@NQ"  # Example contract symbol (Gold Futures)

# Create instance of TradovateAPI class
tradovate_api = TradovateAPI(CONTRACT_SYMBOL)

# Authenticate and get token
tradovate_api.authenticate()

# Run WebSocket
tradovate_api.run_websocket()
