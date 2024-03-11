import time
import websocket
from django.test import TestCase



# Create your tests here.


def on_message(ws, message):
    print(f"Received message: {message}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Connection closed with status code {close_status_code}")

def on_open(ws):
    print("Connection opened")
    # You can send a test message after the connection is opened
    ws.send("Hello, WebSocket server!")

if __name__ == "__main__":
    # ws_url = "wss://enchird.biz/api/chat-messaging/24/9c268136a9ee5f9ec1dd7e674e8ecfb7b9cfb964349439788218162870649218/"
    ws_url = "ws://127.0.0.1:8000/chat/?token=0e14a7bf10f9da28903ab2c9d7aa051f4fbd440eba36f9fe3b0528f7baa5e568/"
    # ws_url = "ws://localhost:8000/your-websocket-endpoint/"
    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
    print(ws)
    ws.on_open = on_open
    
    print(ws.on_open)
    
    