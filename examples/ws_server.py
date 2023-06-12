#!/usr/bin/env python3
"""dl-myo example ws_host.py"""

import argparse
import asyncio
import json
import logging

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from websockets.server import serve

import myo

CONNECTIONS = set()
MS = None


class MyoServer:
    def __init__(self, m):
        self.myo = m
        self.emg0 = None
        self.emg1 = None
        self.emg2 = None
        self.emg3 = None

    async def start(self, c):
        await c.start_notify(myo.Handle.EMG0_DATA.value, self.on_emg)
        await c.start_notify(myo.Handle.EMG1_DATA.value, self.on_emg)
        await c.start_notify(myo.Handle.EMG2_DATA.value, self.on_emg)
        await c.start_notify(myo.Handle.EMG3_DATA.value, self.on_emg)

        await self.myo.vibrate(c, myo.VibrationType.MEDIUM)

        # enable emg and imu
        await self.myo.set_mode(
            c,
            myo.EMGMode.SEND_EMG,
            myo.IMUMode.SEND_ALL,
            myo.ClassifierMode.DISABLED,
        )
        logging.info("EMG notify ON")

    async def stop(self, c):
        await self.myo.set_mode(
            c, myo.EMGMode.NONE, myo.IMUMode.NONE, myo.ClassifierMode.DISABLED
        )
        logging.info("EMG notify OFF")

    async def warmup(self, c):
        logging.info("warming up")
        await self.myo.set_sleep_mode(c, myo.SleepMode.NORMAL)
        # led red
        await self.myo.led(c, [255, 0, 0], [255, 0, 0])
        await self.myo.vibrate(c, myo.VibrationType.SHORT)
        logging.info("sleep 0.25")
        await asyncio.sleep(0.25)
        # led green
        await self.myo.led(c, [0, 255, 0], [0, 255, 0])
        await self.myo.vibrate(c, myo.VibrationType.SHORT)
        logging.info("sleep 0.25")
        await asyncio.sleep(0.25)
        # led cyan
        await self.myo.led(c, [0, 255, 255], [0, 255, 255])

    async def on_emg(self, sender: BleakGATTCharacteristic, data: bytearray):
        name = myo.Handle(sender.handle).name
        if name == myo.Handle.EMG0_DATA.name:
            self.emg0 = myo.EMGData(data).to_dict()
        elif name == myo.Handle.EMG1_DATA.name:
            self.emg1 = myo.EMGData(data).to_dict()
        elif name == myo.Handle.EMG2_DATA.name:
            self.emg2 = myo.EMGData(data).to_dict()
        elif name == myo.Handle.EMG3_DATA.name:
            self.emg3 = myo.EMGData(data).to_dict()
        if self.emg0 and self.emg1 and self.emg2 and self.emg3:
            emg = json.dumps(
                {
                    "emg0": self.emg0,
                    "emg1": self.emg1,
                    "emg2": self.emg2,
                    "emg3": self.emg3,
                }
            )
            global CONNECTIONS
            for ws in CONNECTIONS:
                await ws.send(emg)
            self.emg0 = None
            self.emg1 = None
            self.emg2 = None
            self.emg3 = None


async def register(websocket):
    global CONNECTIONS, MS

    if MS is None:
        logging.info("initializing Myo connection")
        m = await myo.Device.with_uuid()
        if m.device is None:
            return
        logging.info(f"found {m.name}: {m.device.address}")
        MS = MyoServer(m)

    async with BleakClient(MS.myo.device) as c:
        try:
            # Register client
            CONNECTIONS.add(websocket)
            await asyncio.sleep(0.5)
            await MS.warmup(c)
            # Manage state changes
            async for message in websocket:
                event = json.loads(message)
                if event["action"] == "disconnect":
                    await websocket.send("disconnect")
                    break
                elif event["action"] == "start":
                    await MS.start(c)
                    await websocket.send("start")
                    print("start")
                elif event["action"] == "warmup":
                    await MS.warmup(c)
                    await websocket.send("warmup")
                elif event["action"] == "stop":
                    await MS.stop(c)
                    await websocket.send("stop")
                    print("stop")
                else:
                    await websocket.send(f"Unsupported event: {event}")
                    logging.error(f"Unsupported event: {event}")
            await websocket.wait_closed()
        finally:
            # Unregister user
            await MS.stop(c)
            CONNECTIONS.remove(websocket)


async def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="connect to a Myo band and stream via websockets",
    )
    parser.add_argument(
        "-a",
        "--address",
        help="the host IP address for msgpack server",
        default="127.0.0.1",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="sets the log level to debug",
    )
    parser.add_argument(
        "-p", "--port", help="the port for msgpack listener", default=8765
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )
    logging.getLogger("myo").setLevel(level=log_level)
    logging.info(f"listening {args.address}:{args.port} ...")
    async with serve(register, args.address, args.port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
