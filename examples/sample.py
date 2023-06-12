#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

import myo


def callback(sender: BleakGATTCharacteristic, data: bytearray):
    name = myo.Handle(sender.handle).name
    if name == myo.Handle.IMU_DATA.name:
        print(f"{name}: {myo.IMUData(data).json()}")
    else:
        print(f"{name}: {myo.EMGData(data).json()}")


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
        logging.info("sleep 0.25")
        await asyncio.sleep(0.25)
        # led green
        await m.led(client, [0, 255, 0], [0, 255, 0])
        await m.vibrate(client, myo.VibrationType.SHORT)
        logging.info("sleep 0.25")
        await asyncio.sleep(0.25)
        # led cyan
        await m.led(client, [0, 255, 255], [0, 255, 255])

        await client.start_notify(myo.Handle.EMG0_DATA.value, callback)
        await client.start_notify(myo.Handle.EMG1_DATA.value, callback)
        await client.start_notify(myo.Handle.EMG2_DATA.value, callback)
        await client.start_notify(myo.Handle.EMG3_DATA.value, callback)
        await client.start_notify(myo.Handle.IMU_DATA.value, callback)

        await m.vibrate(client, myo.VibrationType.MEDIUM)

        # enable emg and imu
        await m.set_mode(
            client,
            myo.EMGMode.SEND_EMG,
            myo.IMUMode.SEND_ALL,
            myo.ClassifierMode.DISABLED,
        )

        logging.info("sleep 1")
        await asyncio.sleep(0.5)

        # disable emg and imu
        await m.set_mode(
            client,
            myo.EMGMode.NONE,
            myo.IMUMode.NONE,
            myo.ClassifierMode.DISABLED,
        )

        # get the available services on the myo device
        info = await m.get_services(client)
        logging.info(info)

        # led purple
        await m.led(client, [100, 100, 100], [100, 100, 100])
        await m.vibrate(client, myo.VibrationType.LONG)

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
