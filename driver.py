import argparse
import asyncio
import json
import logging

from bleak import BleakClient

import myo


async def main(args: argparse.Namespace):
    logging.info("starting scan...")

    if args.mac and len(args.mac) != 0:
        m = await myo.Device.with_mac(args.mac)
    else:
        m = await myo.Device.with_uuid()

    if m.device is None:
        return

    logging.info(f"{m.name}: {m.device.address} ({m.firmware})")
    async with BleakClient(m.device) as client:
        info = await m.get_services(client)
        print(json.dumps(info, indent=2))
        await m.vibrate(client, 3)

    logging.info("warmup complete.")


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
