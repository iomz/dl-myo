#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import asyncio
import logging

from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from myo import MyoClient
from myo.types import (
    ClassifierMode,
    EMGMode,
    FVData,
    IMUData,
    IMUMode,
    VibrationType,
)
from myo.constants import RGB_ORANGE


class InfluxClient(MyoClient):
    def __init__(self):
        super().__init__()
        self.bucket = None
        self.org = None
        self.url = None
        self.token = None
        self.queue = []

    def setup_influxdb(self, url, token, bucket, org):
        self.url = url
        self.token = token
        self.bucket = bucket
        self.org = org

    async def write_point(self, point: Point):
        self.queue.append(point.tag('source', 'dl-myo/examples/influx_client'))
        if len(self.queue) < 50:
            return
        record = self.queue
        self.queue = []
        async with InfluxDBClientAsync(url=self.url, token=self.token, org=self.org) as client:
            write_api = client.write_api()
            await write_api.write(bucket=self.bucket, record=record)

    async def on_emg_data_aggregated(self, emg_data):
        p = Point('emg_data')
        for i, data in enumerate(emg_data):
            p.field(f"emg{i}", data)
        await self.write_point(p)

    async def on_fv_data(self, fvd: FVData):
        p = Point('fv_data')
        for i, data in enumerate(fvd.fv):
            p.field(f"fv{i}", data)
        await self.write_point(p)

    async def on_imu_data(self, imu: IMUData):
        p = Point('imu_data')
        for k, v in imu.to_dict().items():
            if k == 'orientation':
                for kk, vv in v.items():
                    p.field(f"orientation.{kk}", vv)
            else:
                for i, vv in enumerate(v):
                    p.field(f"{k}.{i}", vv)
        await self.write_point(p)


async def main(args: argparse.Namespace):
    logging.info("scanning for a Myo device...")

    ic = await InfluxClient.with_device(mac=args.mac)

    # setup the influxdb client
    ic.setup_influxdb(args.influx_url, args.influx_token, args.influx_bucket, args.influx_org)

    # setup the MyoClient
    emg_mode = EMGMode(int(args.emg_mode))
    await ic.setup(
        classifier_mode=ClassifierMode.DISABLED,
        emg_mode=emg_mode,
        imu_mode=IMUMode.SEND_DATA,
    )
    if emg_mode != EMGMode.SEND_FILT:
        ic.aggregate_emg = True

    # start the indicate/notify
    await ic.start()

    try:
        while True:
            await asyncio.sleep(60)
    except asyncio.exceptions.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        # stop the indicate/notify
        logging.info("bye bye!")
        await ic.stop()
        await ic.vibrate(VibrationType.LONG)
        await ic.led(RGB_ORANGE)
        await ic.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--emg-mode",
        help="the EMGMode (1: SEND_FILT, 2: SEND_EMG, 3: SEND_RAW)",
        choices=['1', '2', '3'],
        default='1',
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="sets the log level to debug",
    )
    parser.add_argument(
        "--influx-url",
        help="the url for influxdb",
        type=str,
        default=u'http://localhost:8086',
    )
    parser.add_argument(
        "--influx-org",
        help="the org for influxdb",
        type=str,
        default='dl-myo',
    )
    parser.add_argument(
        "--influx-token",
        help="the token for influxdb",
        type=str,
        default='super-secret-auth-token',
    )
    parser.add_argument(
        "--influx-bucket",
        help="the bucket for influxdb",
        type=str,
        default='myo',
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

    asyncio.run(main(args))
