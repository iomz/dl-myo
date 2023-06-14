#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging

from bleak.backends.characteristic import BleakGATTCharacteristic

from myo import Myo
from myo.handle import Handle
from myo.types import (
    ClassifierEvent,
    ClassifierMode,
    EMGData,
    EMGMode,
    FVData,
    IMUData,
    IMUMode,
    MotionEvent,
    SleepMode,
    VibrationType,
)


def callback(sender: BleakGATTCharacteristic, data: bytearray):
    handle = Handle(sender.handle)
    if handle == Handle.IMU_DATA:
        logging.info(f"{handle.name}: {IMUData(data).json()}")
    elif handle == Handle.FV_DATA:
        logging.info(f"{handle.name}: {FVData(data).json()}")
    elif handle == Handle.CLASSIFIER_EVENT:
        logging.info(f"{handle.name}: {ClassifierEvent(data).json()}")
    elif handle == Handle.MOTION_EVENT:
        logging.info(f"{handle.name}: {MotionEvent(data).json()}")
    else:
        logging.info(f"{handle.name}: {EMGData(data).json()}")


async def main(args: argparse.Namespace):
    logging.info("scanning for a Myo device...")

    m = None
    while m is None:
        if args.mac and len(args.mac) != 0:
            m = await Myo.with_mac(args.mac)
        else:
            m = await Myo.with_uuid()

    logging.info(f"{m.device.name}: {m.device.address}")
    await m.set_sleep_mode(SleepMode.NORMAL)
    # led red
    await m.led([255, 0, 0], [255, 0, 0])
    await m.vibrate(VibrationType.SHORT)
    # led green
    await m.led([0, 255, 0], [0, 255, 0])
    await m.vibrate(VibrationType.SHORT)
    # led cyan
    await m.led([0, 255, 255], [0, 255, 255])

    # enable emg and imu
    await m.set_mode(
        EMGMode.SEND_FILT,
        IMUMode.SEND_ALL,
        ClassifierMode.ENABLED,
    )

    await m.vibrate(VibrationType.MEDIUM)

    await m.client.start_notify(Handle.FV_DATA.value, callback)
    await m.client.start_notify(Handle.IMU_DATA.value, callback)
    await m.client.start_notify(Handle.MOTION_EVENT.value, callback)
    await m.client.start_notify(Handle.CLASSIFIER_EVENT.value, callback)

    # receive notifications for 5 seconds
    await asyncio.sleep(5)

    # disable emg and imu
    await m.set_mode(
        EMGMode.NONE,
        IMUMode.NONE,
        ClassifierMode.DISABLED,
    )

    # get the available services on the myo device
    info = await m.get_services()
    logging.info(info)

    logging.info("bye bye!")
    # led purple
    await m.led([100, 100, 100], [100, 100, 100])
    await m.vibrate(VibrationType.LONG)
    await m.disconnect()


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
