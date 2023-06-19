#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging

from myo import (
    FVData,
    Handle,
    MyoClient,
    VibrationType,
)
from myo.constants import RGB_BLACK


class SampleClient(MyoClient):
    def on_fv_data(self, fvd: FVData):
        logging.info(f"{Handle.FV_DATA.name}: {fvd.json()}")


async def main(args: argparse.Namespace):
    logging.info("scanning for a Myo device...")

    sc = await SampleClient.with_device(mac=args.mac)

    # get the available services on the myo device
    info = await sc.get_services()
    logging.info(info)

    # setup the MyoClient
    await sc.setup()

    # start the indicate/notify
    await sc.start()

    # receive notifications for 5 seconds
    await asyncio.sleep(5)

    # stop the indicate/notify
    await sc.stop()

    logging.info("bye bye!")
    await sc.vibrate(VibrationType.LONG)
    await sc.led(RGB_BLACK)
    await sc.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="sets the log level to debug",
    )
    parser.add_argument(
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
