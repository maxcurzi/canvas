import asyncio
import websockets
import json
import random
import argparse

async def connect_client(client_id, ops_per_second):
    """Simulate a single WebSocket client connection that clicks random pixels"""
    uri = "ws://localhost:8765/"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Client {client_id} connected")
            
            # Send clicks at the specified rate
            click_task = asyncio.create_task(send_random_clicks(websocket, client_id, ops_per_second))
            
            # Listen for messages
            try:
                async for message in websocket:
                    data = json.loads(message)
                    # Silently receive updates, only log occasionally to avoid spam
                    if client_id == 0:  # Only log from first client
                        print(f"Received: pixels={len(data['pixels'])}, owners={len(data['owners'])}")
            except asyncio.CancelledError:
                click_task.cancel()
                raise
    except Exception as e:
        print(f"Client {client_id} error: {e}")

async def send_random_clicks(websocket, client_id, ops_per_second):
    """Send random clicks at the specified rate"""
    interval = 1.0 / ops_per_second
    while True:
        try:
            await asyncio.sleep(interval)
            # Random pixel within 64x64 canvas
            x = random.randint(0, 63)
            y = random.randint(0, 63)
            user = f"LoadTestUser{client_id}"
            
            message = json.dumps({"x": x, "y": y, "user": user})
            await websocket.send(message)
            if client_id == 0:  # Only log from first client
                print(f"Client {client_id} clicked: ({x}, {y})")
        except Exception as e:
            print(f"Client {client_id} click error: {e}")
            break

async def main(num_clients, ops_per_second):
    """Create concurrent client connections"""
    print(f"Starting {num_clients} load test clients, {ops_per_second} operations per second each...")
    tasks = [connect_client(i, ops_per_second) for i in range(num_clients)]
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\nShutting down clients...")
        for task in tasks:
            task.cancel()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load test for Canvas WebSocket server")
    parser.add_argument(
        "-c", "--clients",
        type=int,
        default=100,
        help="Number of concurrent clients (default: 100)"
    )
    parser.add_argument(
        "-o", "--ops-per-second",
        type=float,
        default=1,
        help="Operations (clicks) per second per client (default: 1)"
    )
    
    args = parser.parse_args()
    asyncio.run(main(args.clients, args.ops_per_second))
