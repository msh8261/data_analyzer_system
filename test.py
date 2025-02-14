import websocket


def on_message(ws, message):
    print("Received message:", message)


def on_error(ws, error):
    print("Error:", error)


def on_close(ws, close_status_code, close_msg):
    print("Closed")


def on_open(ws):
    print("Opened connection")
    ws.send("Hello, server!")


ws_url = "ws://localhost:8001/ws?token=your_token_here"
ws = websocket.WebSocketApp(
    ws_url, on_message=on_message, on_error=on_error, on_close=on_close
)
ws.on_open = on_open
ws.run_forever()
