# -*- coding: utf-8 -*-
# import binascii
from __future__ import annotations

import asyncio
import binascii
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .constants import *
from .state import *

# from .quaternion import Quaternion

logger = logging.getLogger(__name__)


class Device:
    __slots__ = ("__battery_level", "__device", "__firmware", "__name", "__state")

    def __init__(self):
        self.__state = MyoState()

    @property
    def battery_level(self) -> int:
        return self.__battery_level

    @property
    def device(self) -> BLEDevice:
        return self.__device

    @property
    def firmware(self) -> Firmware:
        return self.__firmware

    @property
    def name(self) -> str:
        return self.__name

    @property
    def state(self) -> MyoState:
        return self.__state

    @classmethod
    async def with_mac(cls, mac: str) -> Device:
        def match_myo_mac(device: BLEDevice, _: AdvertisementData):
            if mac.lower() == device.address.lower():
                return True
            return False

        self = cls()
        try:
            # connect to the device
            self.__device = await BleakScanner.find_device_by_filter(match_myo_mac, cb=dict(use_bdaddr=True))
            if self.device is None:
                logger.error(f"could not find device with address {mac}")
                return self
        except:
            logger.error("the mac address may be invalid")
            return self

        async with BleakClient(self.device) as client:
            logger.info(f"connected to device {self.device.address}")
            await self.startup(client)

        return self

    @classmethod
    async def with_uuid(cls) -> Device:
        def match_myo_uuid(_: BLEDevice, adv: AdvertisementData):
            if str(UUID.MYO_SERVICE).lower() in adv.service_uuids:
                return True
            return False

        self = cls()
        # connect to the device
        self.__device = await BleakScanner.find_device_by_filter(match_myo_uuid, cb=dict(use_bdaddr=True))
        if self.device is None:
            logger.error(f"could not find device with service UUID {UUID.MYO_SERVICE}")
            return self

        async with BleakClient(self.device) as client:
            logger.info(f"connected to device {self.device.address}")
            await self.startup(client)

        return self

    async def battery(self, client):
        # Battery percentage
        val = await client.read_gatt_char(Handle.BATTERY.value)  # pyright: ignore
        self.__battery_level = ord(val)

    async def cmd(self, client, payload):
        """Send command to MYO (see Command class)"""
        await client.write_gatt_char(Handle.COMMAND.value, payload.data, True)  # pyright: ignore

    async def emg_mode(self, client, state=True):
        if state:
            await self.set_mode(client, EMGMode.ON, IMUMode.DATA, ClassifierMode.OFF)
        else:
            await self.set_mode(client, EMGMode.OFF, IMUMode.DATA, ClassifierMode.ON)

    async def get_services(self, client) -> dict:
        sd = {"services": {}}
        for service in client.services:  # BleakGATTServiceCollection
            service_id = service.uuid[4:8]
            service_name = Services.get(int(service_id, base=16))

            if not service_name:  # unknown service
                continue

            sd["services"][service_id] = {
                "name": service_name,
                "handle": service.handle,
                "chars": {},
            }
            for char in service.characteristics:  # List[BleakGATTCharacteristic]
                char_id = char.uuid[4:8]
                char_name = Services.get(int(char_id, base=16))

                if not char_name:  # unknown characteristic
                    continue

                sd["services"][service_id]["chars"][char_id] = {
                    "name": char_name,
                    "handle": char.handle,
                }

                sd["services"][service_id]["chars"][char_id]["properties"] = ",".join(char.properties)
                if "read" in char.properties:
                    blob = await client.read_gatt_char(char.uuid)
                    if char_name == "ManufacturerNameString":
                        value = blob.decode("utf-8")
                    else:
                        value = binascii.b2a_hex(blob).decode("utf-8")
                    sd["services"][service_id]["chars"][char_id]["value"] = value
            # end char
        # end service

        return sd

    async def resync(self, client):
        # Reset classifier
        await self.set_mode(client, EMGMode.OFF, IMUMode.DATA, ClassifierMode.OFF)
        await self.set_mode(client, EMGMode.OFF, IMUMode.DATA, ClassifierMode.ON)

    async def set_leds(self, client, *args):
        """Set leds color
        [logoR, logoG, logoB], [lineR, lineG, lineB] or
        [logoR, logoG, logoB, lineR, lineG, lineB]"""

        if not isinstance(args, tuple) or len(args) != 2:
            raise Exception(f"Unknown payload for LEDs: {args}")

        for l in args:
            if any(not isinstance(v, int) for v in l):
                raise Exception(f"Values must be int 0-255: {l}")

        await self.cmd(client, LED(args[0], args[1]))
        await self.vibrate(client, 1)

    async def set_mode(self, client, emg, imu, classifier):
        # Set mode for EMG, IMU, classifier
        await self.cmd(client, SetMode(emg, imu, classifier))

    async def startup(self, client):
        # get the device name
        self.__name = str(self.device.name)
        # get the firmware version
        fw = await client.read_gatt_char(Handle.FIRMWARE_VERSION.value)  # pyright: ignore
        self.__firmware = Firmware(fw)
        # do the warmup
        await self.warmup(client)
        # reset the emg/imu mode
        await self.resync(client)
        # reset MyoState
        self.state.unsync()

    async def subscribe(self, client):
        # Subscribe to imu notifications
        # await client.write_gatt_char(Handle.IMU.value + 1, b"\x01\x00", True)  # pyright: ignore
        # Subscribe to classifier
        # await client.write_gatt_char(Handle.CLASSIFIER.value + 1, b"\x02\x00", True)  # pyright: ignore
        # Subscribe to emg notifications
        await client.write_gatt_char(Handle.EMG.value + 1, b"\x01\x00", True)  # pyright: ignore

    async def vibrate(self, client, length, strength=None):
        """Vibrate for x ms"""
        await self.cmd(client, Vibration(length, strength))

    async def warmup(self, client):
        await self.cmd(client, SleepMode().never())
        await self.set_leds(client, [255, 0, 0], [255, 0, 0])
        await asyncio.sleep(0.5)
        await self.set_leds(client, [0, 255, 0], [0, 255, 0])
        await asyncio.sleep(0.5)
        await self.set_leds(client, [0, 0, 255], [0, 0, 255])
        await asyncio.sleep(0.5)
        await self.set_leds(client, [255, 255, 255], [255, 255, 255])

    """
    def handleNotification(self, cHandle, data):
        Events = (
            "rest",
            "fist",
            "wave_in",
            "wave_out",
            "wave_left",
            "wave_right",
            "fingers_spread",
            "double_tap",
            "unknown",
            "arm_synced",
            "arm_unsynced",
            "orientation_data",
            "gyroscope_data",
            "accelerometer_data",
            "imu_data",
            "emg_data",
        )
        try:
            handle_enum = Handle(cHandle)
        except:
            raise Exception(f"Unknown data handle + {str(cHandle)}")

        if handle_enum == Handle.CLASSIFIER:
            # sometimes gets the poses mixed up, if this happens, try wearing it in a different orientation.
            data = struct.unpack(">6b", data)
            try:
                ev_type = ClassifierEvent(data[0])
            except:
                raise Exception("Unknown classifier event: " + str(data[0]))
            if ev_type == ClassifierEvent.POSE:
                self.state.pose = Pose(data[1])  # pyright: ignore
                if self.state.pose == Pose.UNSYNC:
                    self.state.synced = False
                    self.state.arm = Arm.UNSYNC
                    self.state.pose = Pose.UNSYNC
                    self.state.x_direction = XDirection.UNSYNC
                    self.state.startq = Quaternion(0, 0, 0, 1)
                else:
                    self.state.napq = self.state.imu.quat.copy()
                    self.on_pose(self.state)

            elif ev_type == ClassifierEvent.SYNC:
                self.state.synced = True
                # rewrite handles
                self.state.arm = Arm(data[1])  # pyright: ignore
                self.state.x_direction = XDirection(data[2])  # pyright: ignore
                self.state.startq = self.state.imu.quat.copy()
                self.on_sync(self.state)

            elif ev_type == ClassifierEvent.UNSYNC:
                self.state.synced = False
                self.state.arm = Arm.UNSYNC
                self.state.x_direction = XDirection.UNSYNC
                self.state.pose = Pose.UNSYNC
                self.state.startq = Quaternion(0, 0, 0, 1)
                self.on_unsync(self.state)

            elif ev_type == ClassifierEvent.UNLOCK:
                self.on_unlock(self.state)

            elif ev_type == ClassifierEvent.LOCK:
                self.on_lock(self.state)

            elif ev_type == ClassifierEvent.SYNCFAIL:
                self.state.synced = False
                self.on_sync_failed(self.state)

            elif ev_type == ClassifierEvent.WARMUP:
                self.on_warmup(self.state)

        elif handle_enum == Handle.IMU:
            self.state.imu = IMU(data)
            self.on_imu(self.state)

        elif handle_enum == Handle.EMG:
            self.state.emg = EMG(data)
            self.on_emg(self.state)

        else:
            logging.error(f"Unknown data handle {cHandle}")
    """
