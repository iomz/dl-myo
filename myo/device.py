# -*- coding: utf-8 -*-
# import binascii
from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .constants import *
from .state import *

# from .quaternion import Quaternion

logger = logging.getLogger(__name__)


class Myo:
    __slots__ = ("__battery_level", "__device", "__firmware", "__name", "state")

    def __init__(self):
        self.state = MyoState()

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

    @classmethod
    async def with_mac(cls, mac: str) -> Myo:
        def match_myo_mac(device: BLEDevice, _: AdvertisementData):
            if mac.lower() == device.address.lower():
                return True
            return False

        self = cls()
        if mac and len(mac) != 0:
            self.__device = await BleakScanner.find_device_by_filter(match_myo_mac, cb=dict(use_bdaddr=True))
            if self.device is None:
                logger.error(f"could not find device with address {mac}")
                return self
        else:
            logger.error("no mac address was specified")
            return self

        async with BleakClient(self.device) as client:
            logger.info(f"connected to device {self.device.address}")
            await self.startup(client)

        return self

    @classmethod
    async def with_uuid(cls) -> Myo:
        def match_myo_uuid(_: BLEDevice, adv: AdvertisementData):
            if str(UUID.MYO_SERVICE).lower() in adv.service_uuids:
                return True
            return False

        self = cls()
        self.__device = await BleakScanner.find_device_by_filter(match_myo_uuid, cb=dict(use_bdaddr=True))
        if self.device is None:
            logger.error(f"could not find device with service UUID {UUID.MYO_SERVICE}")
            return self

        async with BleakClient(self.device) as client:
            logger.info(f"connected to device {self.device.address}")
            await self.startup(client)

        return self

    async def startup(self, client):
        # get the device name
        self.__name = self.device.name
        # get the firmware version
        fw = await client.read_gatt_char(Handle.FIRMWARE_VERSION.value)  # pyright: ignore
        self.__firmware = Firmware(fw)
        # do the warmup
        await self.warmup(client)
        # reset the emg/imu mode
        await self.resync(client)
        # reset MyoState
        self.state.unsync()

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

    async def info(self, client):
        _ = client
        """
        info_dict = {}
        for service in self.getServices():  # btle.Peripheral
            uuid = binascii.b2a_hex(service.uuid.binVal).decode("utf-8")[4:8]
            service_name = Services.get(int(uuid, base=16), uuid)

            if service_name in ("1801", "0004", "0006"):  # unknown
                continue

            logging.info(str(service_name))

            # constract data for service
            data_dict = {}
            for char in service.getCharacteristics():
                c_uuid = binascii.b2a_hex(char.uuid.binVal).decode("utf-8")[4:8]
                num = int(c_uuid, base=16)
                name = Services.get(num, hex(num))
                if "EmgData" in name:
                    logging.info(name)
                    data_dict.update({name: ""})
                    continue
                if name in ("0x602", "0x104", "Command", "0x2a05"):  # TODO: make this more sense
                    logging.info(name)
                    data_dict.update({name: ""})
                    continue

                if char.supportsRead():
                    b = bytearray(char.read())
                    try:
                        if name in ("Info1", "Info2"):
                            b = list(b)
                        elif name == "FirmwareVersion":
                            b = Firmware(b)
                        elif name == "HardwareInfo":
                            b = HardwareInfo(b)
                        elif name == "BatteryLevel":
                            b = b[0]
                            b = int(b)
                        else:  # if anything else, stringify the bytearray
                            b = str(list(b))
                            logging.debug(f"{name}: {b}")
                    except Exception as e:
                        logging.debug(f"{name}: {b} {e}")
                    logging.info(f"{name} {b}")
                    data_dict.update({name: b})
                    continue

                # TODO
                # not char.supportsRead()
                try:
                    b = bytearray(char.read())
                    if name in ("0x104", "ClassifierEvent"):  # TODO
                        b = list(b)
                    elif name == "IMUData":
                        b = IMU(b)
                    elif name == "MotionEvent":
                        b = MotionEvent(b)
                    else:
                        b = str(list(b))
                except:
                    logging.debug(f"{name}: {char.props}")
                    data_dict.update({name: char})
                    continue
                data_dict.update({name: b})
                # end char
            info_dict.update({service_name: data_dict})
            # end service
        return info_dict
        """

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
