#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging

from myo import MyoClient
from myo.types import (
    ClassifierEvent,
    ClassifierMode,
    EMGMode,
    FVData,
    IMUData,
    IMUMode,
    MotionEvent,
    VibrationType,
)
from myo.constants import RGB_PINK


class SampleClient(MyoClient):
    async def on_classifier_event(self, ce: ClassifierEvent):
        logging.info(ce.json())

    async def on_emg_data(self, emg):  # data: list of 8 8-bit unsigned short
        logging.info(emg)

    async def on_fv_data(self, fvd: FVData):
        logging.info(fvd.json())

    async def on_imu_data(self, imu: IMUData):
        logging.info(imu.json())

    async def on_motion_event(self, me: MotionEvent):
        logging.info(me.json())


async def main(args: argparse.Namespace):
    logging.info("scanning for a Myo device...")

    sc = await SampleClient.with_device(mac=args.mac)

    # get the available services on the myo device
    info = await sc.get_services()
    logging.info(info)

    # setup the MyoClient
    await sc.setup(
        classifier_mode=ClassifierMode.ENABLED,
        emg_mode=EMGMode.SEND_FILT,
        imu_mode=IMUMode.SEND_EVENTS,
    )

    # start the indicate/notify
    await sc.start()

    # receive notifications for 5 seconds
    await asyncio.sleep(5)

    # stop the indicate/notify
    await sc.stop()

    logging.info("bye bye!")
    await sc.vibrate(VibrationType.LONG)
    await sc.led(RGB_PINK)
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
    # logging.getLogger("bleak.*").setLevel(level=log_level)

    asyncio.run(main(args))
