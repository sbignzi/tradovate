import requests
import json
import websocket
import os  # Import the os module to access environment variables
from os.path import join, dirname
from dotenv import load_dotenv
import csv
import time
from datetime import datetime, timedelta
import threading

# Load the environment variables
# load_dotenv()

dotenv_path = join(dirname(__file__), ".env")
load_dotenv()


class TradovateAPI:
    def __init__(self):
        self.username = os.getenv("TRADOVATE_USERNAME")
        self.password = os.getenv("TRADOVATE_PASSWORD")
        self.app_id = os.getenv("TRADOVATE_APP_ID")
        self.app_version = os.getenv("TRADOVATE_APP_VERSION")
        self.device_id = os.getenv("TRADOVATE_DEVICE_ID")
        self.client_id = os.getenv("TRADOVATE_CLIENT_ID")
        self.client_secret = os.getenv("TRADOVATE_CLIENT_SECRET")
        self.contract_symbol = "@NQ"
        self.token = None
        self.receive_data = True
        self.socket_url = "wss://md.tradovateapi.com/v1/websocket"

        # CSV file to save OHLC data
        self.quote_file = "data/ohlc_data.csv"
        self.chart_file = "data/bar.csv"
        self.sorted_chart_file = "data/sorted_bar.csv"

        self.last_heartbeat_time = None
        self.heartbeat_interval = 10  # seconds
        self.check_timing = False
        self.subscription = None
        self.subscriptionToGetHistoricalChart = None
        self.subscriptionToGetLiveChart = None
        self.subscriptionToGetQuotes = None

        # CONTRACT_SYMBOL = "@NQ"  # Example contract symbol (Gold Futures)

        # print("username", self.username)
        # print("self.password", self.password)

    def authenticate(self):
        """Authenticate and get access token"""
        auth_url = "https://demo.tradovateapi.com/v1/auth/accessTokenRequest"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "name": self.username,
            "password": self.password,
            "appId": self.app_id,
            "appVersion": self.app_version,
            "deviceId": self.device_id,
            "cid": self.client_id,
            "sec": self.client_secret,
        }
        response = requests.post(auth_url, json=payload, headers=headers)
        response.raise_for_status()  # Check for errors
        response_data = response.json()
        # print(f"Authentication Response: {response_data}")  # Debugging the response
        self.token = response_data.get("mdAccessToken")
        print(f"Access Token: {self.token}")

    # Function to reorder the CSV by the Timestamp
    def reorder_csv_by_timestamp(self, input_file, output_file):
        # Ensure the folder exists
        input_folder = os.path.dirname(input_file)
        output_folder = os.path.dirname(output_file)

        if input_folder and not os.path.exists(input_folder):
            os.makedirs(input_folder)  # Create folder if missing
            print(f"Created missing folder: {input_folder}")

        if output_folder and not os.path.exists(output_folder):
            os.makedirs(output_folder)  # Create folder if missing
            print(f"Created missing folder: {output_folder}")

        # Ensure the input file exists, otherwise create it with headers
        if not os.path.exists(input_file):
            print(f"{input_file} not found. Creating a new file...")
            with open(input_file, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Timestamp", "Open", "High", "Low", "Close"]
                )  # Default headers
            return  # Exit function as no data to sort yet

        # Read the CSV file and store all rows in a list
        with open(input_file, mode="r", newline="") as infile:
            reader = csv.reader(infile)
            # Skip the header row
            header = next(reader)
            # Read the rest of the data
            rows = [row for row in reader]

        # Sort the rows based on the Timestamp column (first column, index 0)
        rows.sort(key=lambda x: datetime.strptime(x[0], "%Y-%m-%d %H:%M:%S"))

        # Write the sorted data to the output CSV file
        with open(output_file, mode="w", newline="") as outfile:
            writer = csv.writer(outfile)
            # Write the header
            writer.writerow(header)
            # Write the sorted rows
            writer.writerows(rows)

    def get_last_5min_bar_time():
        """Calculate the last 5-minute bar timestamp before the current UTC time."""
        # Get the current UTC time
        now = datetime.utcnow()

        # Round down to the nearest 5-minute mark
        minutes = now.minute // 5 * 5  # Round down to the nearest 5-minute interval
        last_5min_time = now.replace(minute=minutes, second=0, microsecond=0)

        # Convert to the required format (YYYY-MM-DD HH:MM:SS)
        last_5min_time_str = last_5min_time.strftime("%Y-%m-%d %H:%M:%S")

        return last_5min_time_str

    # Get the last 5-minute bar time
    # global desired_time
    # desired_time = get_last_5min_bar_time()
    # print(f"Desired time for the last 5-minute bar: {desired_time}")

    def get_end_of_first_day():
        """Calculate the end of the first trading day (23:59:59 UTC)"""
        now = datetime.utcnow()
        first_day = now - timedelta(days=3)  # Assuming you're pulling 3 days of data
        end_of_first_day = first_day.replace(
            hour=23, minute=59, second=59, microsecond=0
        )

        # Convert to the required format (YYYY-MM-DD HH:MM:SS)
        return end_of_first_day.strftime("%Y-%m-%d %H:%M:%S")

    # Set the desired time to the end of the first day
    global desired_time
    desired_time = get_end_of_first_day()
    print(f"Desired time for the end of the first trading day: {desired_time}")

    def save_to_csv(
        self, output_file, timestamp, open_price, high_price, low_price, close_price
    ):
        """Append the extracted data to the CSV file"""

        # Ensure the folder exists
        # input_folder = os.path.dirname(input_file)
        output_folder = os.path.dirname(output_file)

        # if input_folder and not os.path.exists(input_folder):
        #     os.makedirs(input_folder)  # Create folder if missing
        #     print(f"Created missing folder: {input_folder}")

        if output_folder and not os.path.exists(output_folder):
            os.makedirs(output_folder)  # Create folder if missing
            print(f"Created missing folder: {output_folder}")

        if not os.path.exists(output_file):
            print(f"{output_file} not found. Creating a new file...")
            with open(output_file, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Timestamp", "Open", "High", "Low", "Close"]
                )  # Default headers
            return  # Exit function as no data to sort yet

        # Initialize CSV with headers if the file doesn't exist
        if not os.path.exists(output_file):
            with open(output_file, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Open", "High", "Low", "Close"])

        with open(output_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, open_price, high_price, low_price, close_price])

    def send_heartbeat(self, ws):
        # Only send a heartbeat if it's been 10 seconds since the last one
        if self.last_heartbeat_time is None or (
            time.time() - self.last_heartbeat_time >= self.heartbeat_interval
        ):
            print("Sending heartbeat...")
            ws.send("h")  # Send heartbeat ('h' frame)
            # print("Heartbeat sent.")
            self.last_heartbeat_time = time.time()  # Update the last heartbeat time

    def heartbeat_loop(self, ws):
        """This loop runs in a separate thread to send heartbeats periodically"""
        while True:
            self.send_heartbeat(ws)
            time.sleep(1)

    def prepare_msg(self, raw):
        """Parse the raw message into a frame type and payload"""
        try:
            T = raw[0]  # The first character represents the frame type
            payload = None
            if len(raw) > 1:
                payload = json.loads(raw[1:])  # Parse the payload (JSON data)
            return T, payload
        except json.JSONDecodeError as e:
            return None, None  # Return None if the message can't be parsed

    def on_message(self, ws, message):
        """Handle WebSocket frames"""
        frame_type, payload = self.prepare_msg(message)

        if frame_type == "o":
            print("Open frame received. Connection established.")
            time.sleep(1)

        # elif frame_type == "h":
        #     print("Heartbeat frame received. Responding with heartbeat.")

        elif frame_type == "a":
            if payload:
                if "s" in payload[0] and payload[0]["s"] == 401:
                    print(f"Access denied: {payload}")

                # print(f"Saved data: {timestamp_dt}, Open: {opening_price}, High: {high_price}, Low: {low_price}, Close: {close_price}")
                else:
                    # Handle quotes
                    if "quotes" in payload[0].get("d", {}):
                        for quote in payload[0]["d"]["quotes"]:
                            timestamp = quote.get("timestamp")
                            opening_price = (
                                quote.get("entries", {})
                                .get("OpeningPrice", {})
                                .get("price")
                            )
                            high_price = (
                                quote.get("entries", {})
                                .get("HighPrice", {})
                                .get("price")
                            )
                            low_price = (
                                quote.get("entries", {})
                                .get("LowPrice", {})
                                .get("price")
                            )
                            close_price = (
                                quote.get("entries", {}).get("Trade", {}).get("price")
                            )

                            # Convert timestamp to datetime format
                            timestamp_dt = datetime.fromisoformat(
                                timestamp.replace("Z", "+00:00")
                            ).strftime("%Y-%m-%d %H:%M:%S")

                            # Save the extracted data to CSV
                            self.save_to_csv(
                                self.quote_file,
                                timestamp_dt,
                                opening_price,
                                high_price,
                                low_price,
                                close_price,
                            )

                    # Handle charts
                    if "charts" in payload[0].get("d", {}):
                        for chart in payload[0]["d"]["charts"]:
                            subscriptionId = chart["id"]
                            for bar in chart.get("bars", []):
                                # print(bar)
                                # subscriptionId = bar.get("id")
                                # print("subscriptionId", subscriptionId)
                                timestamp = bar.get("timestamp")
                                open_price = bar.get("open")
                                high_price = bar.get("high")
                                low_price = bar.get("low")
                                close_price = bar.get("close")

                                timestamp_dt = datetime.fromisoformat(
                                    timestamp.replace("Z", "+00:00")
                                ).strftime("%Y-%m-%d %H:%M:%S")

                                self.save_to_csv(
                                    self.chart_file,
                                    timestamp_dt,
                                    open_price,
                                    high_price,
                                    low_price,
                                    close_price,
                                )
                        try:
                            # Convert timestamp (ISO format) to datetime and extract only the date
                            timestamp_date = datetime.strptime(
                                timestamp[:10], "%Y-%m-%d"
                            ).date()  # Extracts only YYYY-MM-DD

                            # Extract the date part from self.start_time (which is a string)
                            start_date = datetime.strptime(
                                self.start_time[:10], "%Y-%m-%d"
                            ).date()

                            # Compare only the date part
                            if self.subscriptionToGetHistoricalChart:
                                if timestamp_date == start_date:
                                    self.check_timing = True
                                    print(
                                        f"Data is from the first day: {timestamp_date}"
                                    )
                                if self.check_timing == True:
                                    if timestamp_dt >= desired_time:
                                        print(
                                            f"Desired time {desired_time} reached getChart (historical data)."
                                        )
                                        # # Example usage
                                        input_csv = self.chart_file  # Your input file
                                        output_csv = (
                                            self.sorted_chart_file
                                        )  # Your desired output file with sorted data

                                        self.reorder_csv_by_timestamp(
                                            input_csv, output_csv
                                        )
                                        # ws.close()  # Close the WebSocket connection
                                        subscription_message = {
                                            "subscriptionId": subscriptionId
                                        }
                                        ws.send(
                                            f"md/cancelChart\n5\n\n{json.dumps(subscription_message)}"
                                        )
                                        print("Data received, cancelChart.")
                        except:
                            pass

        elif frame_type == "c":
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

        self.start_heartbeat(ws)

        # self.get_historical_chart(ws)
        self.get_live_chart(ws)
        self.get_quotes(ws)

        # print(f"Subscribing to quote data: {json.dumps(subscription_message)}")
        # ws.send(f"md/subscribeQuote\n4\n\n{json.dumps(subscription_message)}")

    def start_heartbeat(self, ws):
        # Start the heartbeat loop in a separate thread to run concurrently
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_loop, args=(ws,))
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def get_historical_chart(self, ws):
        now = datetime.utcnow() - timedelta(days=3)
        self.start_time = (
            now.replace(minute=3, second=0, microsecond=0).isoformat() + "Z"
        )

        print(f"Adjusted start time: {self.start_time}")
        chart_subscription_message = {
            "symbol": self.contract_symbol,
            "chartDescription": {
                "underlyingType": "MinuteBar",
                "elementSize": 1,  # 30 seconds per bar
                "elementSizeUnit": "UnderlyingUnits",
                "withHistogram": False,
            },
            "timeRange": {
                # "liveUpdate": True  # Assuming 'liveUpdate' or equivalent keeps data flowing continuously
                "asFarAsTimestamp": self.start_time,  # Start from 3 days ago
                "asMuchAsElements": 2000,  # Number of bars (adjust based on needs)
            },
        }
        self.subscriptionToGetHistoricalChart = True
        print(f"Subscribing to chart data: {json.dumps(chart_subscription_message)}")
        ws.send(f"md/getChart\n4\n\n{json.dumps(chart_subscription_message)}")

    def get_live_chart(self, ws):
        now = datetime.utcnow()
        self.start_time = now.isoformat() + "Z"

        # print(f"Adjusted start time: {self.start_time}")
        chart_subscription_message = {
            "symbol": self.contract_symbol,
            "chartDescription": {
                "underlyingType": "MinuteBar",
                "elementSize": 1,  # 30 seconds per bar
                "elementSizeUnit": "UnderlyingUnits",
                "withHistogram": False,
            },
            "timeRange": {
                # "liveUpdate": True  # Assuming 'liveUpdate' or equivalent keeps data flowing continuously
                "asFarAsTimestamp": self.start_time,  # Start from 3 days ago
                "asMuchAsElements": 2000,  # Number of bars (adjust based on needs)
            },
        }
        self.subscriptionToGetLiveChart = True
        print(f"Subscribing to chart data: {json.dumps(chart_subscription_message)}")
        ws.send(f"md/getChart\n6\n\n{json.dumps(chart_subscription_message)}")

    def get_quotes(self, ws):
        subscription_message = {"symbol": self.contract_symbol}
        self.subscriptionToGetQuotes = True
        print(f"Subscribing to quote data: {json.dumps(subscription_message)}")
        ws.send(f"md/subscribeQuote\n4\n\n{json.dumps(subscription_message)}")

    def run_websocket(self):
        ws = websocket.WebSocketApp(
            self.socket_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )

        # ws.run_forever()
        ws.run_forever(ping_interval=60, ping_timeout=30)


# Create instance of TradovateAPI class
tradovate_api = TradovateAPI()

# Authenticate and get token
tradovate_api.authenticate()

# Run WebSocket
tradovate_api.run_websocket()
