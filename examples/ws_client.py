#!/usr/bin/env python3
"""dl-myo example ws_client.py"""

import argparse
import asyncio
import json
import readline  # pyright: ignore

import websockets


async def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="connect to the Myo band websocket server",
    )
    parser.add_argument("--address", "-a", help="the host IP address for msgpack server", default="127.0.0.1")
    parser.add_argument("--port", "-p", help="the port for msgpack listener", default=8765)

    args = parser.parse_args()

    uri = f"ws://{args.address}:{args.port}"
    async with websockets.connect(uri) as websocket:  # pyright: ignore
        while True:
            action = input("[start|warmup|quit]: ")
            if action == "quit":
                break
            payload = json.dumps({"action": action})

            print(f"<<< {action}")
            await websocket.send(payload)

            if action == "start":
                while True:
                    res = await websocket.recv()
                    print(res)


if __name__ == "__main__":
    asyncio.run(main())
