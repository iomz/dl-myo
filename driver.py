import argparse
import logging

import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from myo import *


async def main(args: argparse.Namespace):
    def match_myo_uuid(device: BLEDevice, adv: AdvertisementData):
        if UUID.MYO_SERVICE.lower() in adv.service_uuids:
            return True

        return False

    def match_myo_mac(device: BLEDevice, adv: AdvertisementData):
        if args.address.lower() == device.address.lower():
            return True

        return False

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected, goodbye.")
        # cancelling all tasks effectively ends the program
        for task in asyncio.all_tasks():
            task.cancel()

    logger.info("starting scan...")

    if args.address and len(args.address) != 0:
        device = await BleakScanner.find_device_by_filter(match_myo_mac, cb=dict(use_bdaddr=True))
        if device is None:
            logger.error(f"could not find device with address {args.address}")
            return
    else:
        device = await BleakScanner.find_device_by_filter(match_myo_uuid, cb=dict(use_bdaddr=True))
        if device is None:
            logger.error(f"could not find device with service UUID {UUID.MYO_SERVICE}")
            return

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        logger.info("connected")

        for service in client.services:
            logger.info("[Service] %s", service)

            for char in service.characteristics:
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        logger.info(
                            "  [Characteristic] %s (%s), Value: %r",
                            char,
                            ",".join(char.properties),
                            value,
                        )
                    except Exception as e:
                        logger.error(
                            "  [Characteristic] %s (%s), Error: %s",
                            char,
                            ",".join(char.properties),
                            e,
                        )

                else:
                    logger.info("  [Characteristic] %s (%s)", char, ",".join(char.properties))

                for descriptor in char.descriptors:
                    try:
                        value = await client.read_gatt_descriptor(descriptor.handle)
                        logger.info("    [Descriptor] %s, Value: %r", descriptor, value)
                    except Exception as e:
                        logger.error("    [Descriptor] %s, Error: %s", descriptor, e)

        logger.info("disconnecting...")


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
    asyncio.run(main(args))
