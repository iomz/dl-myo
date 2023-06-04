import argparse
import asyncio
import logging

from bleak import BleakClient

from myo import *


async def main(args: argparse.Namespace):
    logger.info("starting scan...")

    m = await Myo.with_uuid()
    logger.info(f"{m.name}: {m.device.address} ({m.firmware})")
    async with BleakClient(m.device) as client:
        await m.vibrate(client, 3)

    logger.info("warmup complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--address",
        metavar="<address>",
        help="the address of the bluetooth device to connect to",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="sets the log level to debug",
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )
    logging.getLogger("myo").setLevel(level=log_level)
    asyncio.run(main(args))
