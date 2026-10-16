import asyncio
import json
from urllib.parse import quote

import websockets


async def test_websocket():
    ticket_id = input("Enter your ticket ID: ").strip()
    token = input("Paste your access token: ").strip()

    if not ticket_id.isdigit() or not token:
        print("Please enter a valid ticket ID and access token.")
        return

    url = (
        f"ws://127.0.0.1:8000/ws/tickets/{ticket_id}"
        f"?token={quote(token, safe='')}"
    )

    try:
        async with websockets.connect(url) as websocket:
            print(f"Authenticated and connected to ticket {ticket_id}!")
            print("Waiting for real-time messages...")
            print("Press Ctrl+C to stop.\n")

            while True:
                message = await websocket.recv()

                try:
                    data = json.loads(message)
                    print("\nNew ticket message received:")
                    print(json.dumps(data, indent=4))
                except json.JSONDecodeError:
                    print("Received:", message)

    except websockets.exceptions.ConnectionClosed as error:
        print(f"WebSocket connection closed: {error}")
    except OSError as error:
        print(f"Connection error: {error}")
    except Exception as error:
        print(f"WebSocket error: {error}")


if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\nWebSocket test stopped.")