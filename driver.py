import argparse
import asyncio
import json
import logging

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

import myo


def callback(sender: BleakGATTCharacteristic, data: bytearray):
    print(f"{sender}: {data}")


async def main(args: argparse.Namespace):
    logging.info("starting scan...")

    if args.mac and len(args.mac) != 0:
        m = await myo.Device.with_mac(args.mac)
    else:
        m = await myo.Device.with_uuid()

    if m.device is None:
        return

    logging.info(f"{m.name}: {m.device.address}")
    async with BleakClient(m.device) as client:
        logging.info(f"connected to device {m.device.address}")
        await m.set_sleep_mode(client, myo.SleepMode.NORMAL)
        # led red
        await m.led(client, [255, 0, 0], [255, 0, 0])
        await m.vibrate(client, myo.VibrationType.SHORT)
        # await m.vibrate2(client, 10, 255)
        logging.info("sleep 0.5")
        await asyncio.sleep(0.5)
        # led green
        await m.led(client, [0, 255, 0], [0, 255, 0])
        await m.vibrate(client, myo.VibrationType.SHORT)
        # await m.vibrate2(client, 10, 255)
        logging.info("sleep 0.5")
        await asyncio.sleep(0.5)
        # led cyan
        await m.led(client, [0, 255, 255], [0, 255, 255])
        await m.vibrate(client, myo.VibrationType.MEDIUM)

        # info = await m.get_services(client)
        # logging.info(json.dumps(info, indent=2))

        logging.info("sleep 2")
        await asyncio.sleep(2)
        await m.led(client, [100, 100, 100], [100, 100, 100])
        await m.vibrate(client, myo.VibrationType.LONG)
        # await m.vibrate2(client, 100, 255)

    logging.info("bye bye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="sets the log level to debug",
    )
    parser.add_argument(
        "-m",
        "--mac",
        default="",
        help="the mac address to connect to",
        metavar="<mac-address>",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )
    logging.getLogger("myo").setLevel(level=log_level)
    asyncio.run(main(args))
