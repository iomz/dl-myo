"""
    myo.core
    ----------------
    The core Myo BLE device manager (Myo) and
    a wrapper class (MyoClient) to handle the connection to Myo devices

"""
import asyncio
import json
import logging
from typing import Optional, Union

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .constants import RGB_CYAN, RGB_GREEN, RGB_ORANGE, RGB_PINK
from .commands import (
    Command,
    DeepSleep,
    LED,
    SetMode,
    SetSleepMode,
    Unlock,
    UserAction,
    Vibrate,
    Vibrate2,
)
from .profile import GATTProfile, Handle
from .types import (
    AggregatedData,
    ClassifierEvent,
    ClassifierMode,
    EMGData,
    EMGDataSingle,
    EMGMode,
    FVData,
    IMUData,
    IMUMode,
    MotionEvent,
    SleepMode,
    VibrationType,
)
from .utils import gatt_char_to_dict

logger = logging.getLogger(__name__)


class Myo:
    """Low-level Myo device interface for discovery and command execution."""

    __slots__ = "_device"

    def __init__(self) -> None:
        self._device: Optional[BLEDevice] = None

    @property
    def device(self) -> BLEDevice:
        """Get the discovered BLE device."""
        if self._device is None:
            raise ValueError("Device not discovered. Call with_mac() or with_uuid() first.")
        return self._device

    @classmethod
    async def with_mac(cls, mac: str) -> Optional["Myo"]:
        """
        Discover a Myo device by MAC address.

        Args:
            mac: MAC address of the device (e.g., "D2:3B:85:94:32:8E")

        Returns:
            Myo instance if device is found, None otherwise
        """
        def match_myo_mac(device: BLEDevice, _: AdvertisementData) -> bool:
            return mac.lower() == device.address.lower()

        self = cls()
        try:
            self._device = await BleakScanner.find_device_by_filter(
                match_myo_mac, cb=dict(use_bdaddr=True)
            )
            if self._device is None:
                logger.error("could not find device with address %s", mac)
                return None
        except Exception as e:
            logger.error("the mac address may be invalid: %s", e)
            return None

        return self

    @classmethod
    async def with_uuid(cls) -> Optional["Myo"]:
        """
        Discover a Myo device by service UUID.

        Returns:
            Myo instance if device is found, None otherwise
        """
        def match_myo_uuid(_: BLEDevice, adv: AdvertisementData) -> bool:
            return str(GATTProfile.MYO_SERVICE).lower() in adv.service_uuids

        self = cls()
        self._device = await BleakScanner.find_device_by_filter(
            match_myo_uuid, cb=dict(use_bdaddr=True)
        )
        if self._device is None:
            logger.error(
                "could not find device with service UUID %s", GATTProfile.MYO_SERVICE
            )
            return None

        return self

    async def battery_level(self, client: BleakClient) -> int:
        """
        Read battery level from the device.

        Args:
            client: The BleakClient instance

        Returns:
            Battery level as percentage (0-100)
        """
        val = await client.read_gatt_char(Handle.BATTERY_LEVEL.value)
        return ord(val)

    async def command(self, client: BleakClient, cmd: Command) -> None:
        """
        Send a command to the device.

        Args:
            client: The BleakClient instance
            cmd: Command to send
        """
        await client.write_gatt_char(Handle.COMMAND.value, cmd.data, True)

    async def deep_sleep(self, client: BleakClient) -> None:
        """Put the device into deep sleep mode."""
        await self.command(client, DeepSleep())

    async def led(
        self, client: BleakClient, logo: list[int], line: list[int]
    ) -> None:
        """
        Set LED colors.

        Args:
            client: The BleakClient instance
            logo: RGB values for logo LED [r, g, b] (0-255)
            line: RGB values for line LED [r, g, b] (0-255)

        Raises:
            ValueError: If invalid payload is provided
        """
        if len(logo) != 3 or len(line) != 3:
            raise ValueError(f"LED data must be [r, g, b] format. Got logo={logo}, line={line}")

        for color_list, name in [(logo, "logo"), (line, "line")]:
            if any(not isinstance(v, int) or v < 0 or v > 255 for v in color_list):
                raise ValueError(
                    f"{name} values must be integers between 0 and 255: {color_list}"
                )

        await self.command(client, LED(logo, line))

    async def set_mode(
        self,
        client: BleakClient,
        classifier_mode: ClassifierMode,
        emg_mode: EMGMode,
        imu_mode: IMUMode,
    ) -> None:
        """
        Configure EMG, IMU, and Classifier modes.

        Args:
            client: The BleakClient instance
            classifier_mode: Classifier mode setting
            emg_mode: EMG data mode
            imu_mode: IMU data mode
        """
        await self.command(
            client,
            SetMode(
                classifier_mode=classifier_mode,
                emg_mode=emg_mode,
                imu_mode=imu_mode,
            ),
        )

    async def set_sleep_mode(self, client: BleakClient, sleep_mode: SleepMode) -> None:
        """Set sleep mode."""
        await self.command(client, SetSleepMode(sleep_mode))

    async def unlock(self, client: BleakClient, unlock_type) -> None:
        """Unlock the device."""
        await self.command(client, Unlock(unlock_type))

    async def user_action(self, client: BleakClient, user_action_type) -> None:
        """Send user action command."""
        await self.command(client, UserAction(user_action_type))

    async def vibrate(self, client: BleakClient, vibration_type: VibrationType) -> None:
        """
        Vibrate the device.

        Args:
            client: The BleakClient instance
            vibration_type: Type of vibration to trigger
        """
        try:
            await self.command(client, Vibrate(vibration_type))
        except AttributeError:
            logger.debug(
                "Myo.vibrate() raised AttributeError, BleakClient.is_connected: %s",
                client.is_connected,
            )

    async def vibrate2(self, client: BleakClient, duration: int, strength: int) -> None:
        """
        Vibrate with custom duration and strength.

        Args:
            client: The BleakClient instance
            duration: Duration in milliseconds
            strength: Strength (0-255, where 255 is full speed)
        """
        await self.command(client, Vibrate2(duration, strength))

    async def write(self, client: BleakClient, handle: int, value: bytes) -> None:
        """Write to a GATT characteristic."""
        await client.write_gatt_char(handle, value, True)


class MyoClient:
    """High-level client for interacting with Myo devices."""

    def __init__(self, aggregate_all: bool = False, aggregate_emg: bool = False) -> None:
        """
        Initialize MyoClient.

        Args:
            aggregate_all: If True, aggregate FV and IMU data together
            aggregate_emg: If True, aggregate EMG samples individually
        """
        self.m: Optional[Myo] = None
        self.aggregate_all = aggregate_all
        self.aggregate_emg = aggregate_emg
        self.classifier_mode: Optional[ClassifierMode] = None
        self.emg_mode: Optional[EMGMode] = None
        self.imu_mode: Optional[IMUMode] = None
        self._client: Optional[BleakClient] = None
        self.fv_aggregated: Optional[FVData] = None  # for aggregate_all
        self.imu_aggregated: Optional[IMUData] = None  # for aggregate_all
        self._lock = asyncio.Lock()  # for aggregate_all

    @classmethod
    async def with_device(
        cls,
        mac: Optional[str] = None,
        aggregate_all: bool = False,
        aggregate_emg: bool = False,
    ) -> "MyoClient":
        """
        Create and connect a MyoClient instance.

        Args:
            mac: Optional MAC address to connect to specific device
            aggregate_all: If True, aggregate FV and IMU data together
            aggregate_emg: If True, aggregate EMG samples individually

        Returns:
            Connected MyoClient instance
        """
        self = cls(aggregate_all=aggregate_all, aggregate_emg=aggregate_emg)
        while self.m is None:
            if mac and mac != "":
                self.m = await Myo.with_mac(mac)
            else:
                self.m = await Myo.with_uuid()

            if self.m is None:
                await asyncio.sleep(1)  # Wait before retrying

        await self.connect()
        return self

    @property
    def device(self) -> BLEDevice:
        """Get the underlying BLE device."""
        if self.m is None:
            raise ValueError("Device not initialized. Call with_device() first.")
        return self.m.device

    async def battery_level(self) -> int:
        """Get battery level from the device."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        return await self.m.battery_level(self._client)

    async def connect(self) -> None:
        """Connect the client to the Myo device."""
        if self.m is None:
            raise ValueError("Device not discovered. Call with_device() first.")

        self._client = BleakClient(self.device)
        if self._client is None:
            raise RuntimeError("Failed to create BLE client")

        await self._client.connect()
        logger.info("connected to %s: %s", self.device.name, self.device.address)

    async def deep_sleep(self) -> None:
        """Put the device into deep sleep mode."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.deep_sleep(self._client)

    async def disconnect(self) -> None:
        """Disconnect the client from the Myo device."""
        if self._client is None:
            logger.warning("connection is already closed")
            return

        await self._client.disconnect()
        device_name = self.device.name if self.m else "unknown"
        self._client = None
        logger.info("disconnected from %s", device_name)

    async def get_services(self, indent: int = 1) -> str:
        """
        Fetch available GATT services and characteristics.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation of services
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")

        sd = {}
        for service in self._client.services:
            try:
                service_name = Handle(service.handle).name
            except Exception as e:
                logger.debug("unknown handle: %s", e)
                continue

            chars = {}
            for char in service.characteristics:
                cd = await gatt_char_to_dict(self._client, char)
                if cd:
                    chars[hex(char.handle)] = cd

            sd[hex(service.handle)] = {
                "name": service_name,
                "uuid": service.uuid,
                "chars": chars,
            }
        return json.dumps({"services": sd}, indent=indent)

    async def led(self, color: list[int]) -> None:
        """
        Set LED color for both logo and line.

        Args:
            color: RGB color values [r, g, b] (0-255)
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.led(self._client, color, color)

    async def on_classifier_event(self, ce: ClassifierEvent) -> None:
        """Handle classifier events. Override in subclasses."""
        raise NotImplementedError()

    async def on_data(self, data: Union[FVData, IMUData]) -> None:
        """
        Internal method for aggregating FV and IMU data.

        Args:
            data: Either FVData or IMUData
        """
        async with self._lock:
            if isinstance(data, FVData):
                self.fv_aggregated = data
            elif isinstance(data, IMUData):
                self.imu_aggregated = data
            # trigger on_aggregated_data when both FVData and IMUData are ready
            if all(d is not None for d in (self.fv_aggregated, self.imu_aggregated)):
                await self.on_aggregated_data(
                    AggregatedData(self.fv_aggregated, self.imu_aggregated)
                )
                self.fv_aggregated = None
                self.imu_aggregated = None

    async def on_aggregated_data(self, ad: AggregatedData) -> None:
        """
        Handle aggregated FV and IMU data.

        This is invoked when both FVData and IMUData are ready.
        Note: EMGData is not included as it is collected at a different
        interval (200Hz instead of 50Hz).

        Args:
            ad: Aggregated data containing FV and IMU data
        """
        raise NotImplementedError()

    async def on_emg_data(self, emg: EMGData) -> None:
        """
        Handle EMG data. Override in subclasses.

        Args:
            emg: EMG data containing two samples of 8 channels each
        """
        raise NotImplementedError()

    async def on_emg_data_aggregated(self, eds: EMGDataSingle) -> None:
        """
        Handle individual EMG data samples. Override in subclasses.

        Args:
            eds: Single EMG data sample
        """
        raise NotImplementedError()

    async def on_fv_data(self, fvd: FVData) -> None:
        """
        Handle filtered value (FV) data. Override in subclasses.

        Args:
            fvd: Filtered value data
        """
        raise NotImplementedError()

    async def on_imu_data(self, imu: IMUData) -> None:
        """
        Handle IMU data. Override in subclasses.

        Args:
            imu: IMU data containing orientation, accelerometer, and gyroscope
        """
        raise NotImplementedError()

    async def on_motion_event(self, me: MotionEvent) -> None:
        """
        Handle motion events. Override in subclasses.

        Args:
            me: Motion event (e.g., tap)
        """
        raise NotImplementedError()

    async def notify_callback(
        self, sender: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """
        Internal callback for handling GATT notifications.

        Routes incoming data to appropriate handler methods based on the
        characteristic handle.

        Args:
            sender: The GATT characteristic that sent the notification
            data: The notification data
        """
        handle = Handle(sender.handle)
        logger.debug("notify_callback (%s): %s", handle, data)

        if handle == Handle.CLASSIFIER_EVENT:
            await self.on_classifier_event(ClassifierEvent(data))
        elif handle == Handle.FV_DATA:
            fv_data = FVData(data)
            if self.aggregate_all:
                await self.on_data(fv_data)
            else:
                await self.on_fv_data(fv_data)
        elif handle == Handle.IMU_DATA:
            imu_data = IMUData(data)
            if self.aggregate_all:
                await self.on_data(imu_data)
            else:
                await self.on_imu_data(imu_data)
        elif handle == Handle.MOTION_EVENT:
            await self.on_motion_event(MotionEvent(data))
        elif handle in [
            Handle.EMG0_DATA,
            Handle.EMG1_DATA,
            Handle.EMG2_DATA,
            Handle.EMG3_DATA,
        ]:
            emg = EMGData(data)
            if self.aggregate_emg:
                await self.on_emg_data_aggregated(EMGDataSingle(emg.sample1))
                await self.on_emg_data_aggregated(EMGDataSingle(emg.sample2))
            else:
                await self.on_emg_data(emg)

    async def set_mode(
        self,
        classifier_mode: ClassifierMode,
        emg_mode: EMGMode,
        imu_mode: IMUMode,
    ) -> None:
        """
        Configure EMG, IMU, and Classifier modes.

        Args:
            classifier_mode: Classifier mode setting
            emg_mode: EMG data mode
            imu_mode: IMU data mode
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.set_mode(
            client=self._client,
            classifier_mode=classifier_mode,
            emg_mode=emg_mode,
            imu_mode=imu_mode,
        )

    async def set_sleep_mode(self, sleep_mode: SleepMode) -> None:
        """Set sleep mode."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.set_sleep_mode(self._client, sleep_mode)

    async def setup(
        self,
        classifier_mode: ClassifierMode = ClassifierMode.DISABLED,
        emg_mode: EMGMode = EMGMode.SEND_FILT,
        imu_mode: IMUMode = IMUMode.NONE,
    ) -> None:
        """
        Setup the Myo device with default configuration.

        Args:
            classifier_mode: Classifier mode (default: DISABLED)
            emg_mode: EMG data mode (default: SEND_FILT)
            imu_mode: IMU data mode (default: NONE)
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")

        await self.led(RGB_ORANGE)
        logger.info("setting up the myo: %s", self.device.name)
        battery = await self.m.battery_level(self._client)
        logger.info("remaining battery: %s %%", battery)

        # Vibrate short *3
        for _ in range(3):
            await self.vibrate(VibrationType.SHORT)

        # Never sleep
        await self.set_sleep_mode(SleepMode.NEVER_SLEEP)

        # Setup modes
        if self.aggregate_all:
            # Enforce the modes when aggregate_all
            self.classifier_mode = ClassifierMode.DISABLED
            self.emg_mode = EMGMode.SEND_FILT
            self.imu_mode = IMUMode.SEND_DATA
        else:
            self.classifier_mode = classifier_mode
            self.emg_mode = emg_mode
            self.imu_mode = imu_mode

        await self.set_mode(
            classifier_mode=self.classifier_mode,
            emg_mode=self.emg_mode,
            imu_mode=self.imu_mode,
        )
        await self.led(RGB_PINK)

    async def sleep(self) -> None:
        """Put the device to sleep and disconnect."""
        logger.info("sleep %s", self.device.name)
        await self.led(RGB_PINK)
        await self.set_sleep_mode(SleepMode.NORMAL)
        await asyncio.sleep(0.5)
        await self.disconnect()

    def _get_emg_handles(self) -> list[int]:
        """Get list of EMG data handles based on current mode."""
        if self.emg_mode in [EMGMode.SEND_EMG, EMGMode.SEND_RAW]:
            return [
                Handle.EMG0_DATA.value,
                Handle.EMG1_DATA.value,
                Handle.EMG2_DATA.value,
                Handle.EMG3_DATA.value,
            ]
        elif self.emg_mode == EMGMode.SEND_FILT:
            return [Handle.FV_DATA.value]
        return []

    def _get_imu_handles(self) -> list[int]:
        """Get list of IMU data handles based on current mode."""
        handles = []
        if self.imu_mode not in [IMUMode.NONE, IMUMode.SEND_EVENTS]:
            handles.append(Handle.IMU_DATA.value)
        if self.imu_mode in [IMUMode.SEND_EVENTS, IMUMode.SEND_ALL]:
            handles.append(Handle.MOTION_EVENT.value)
        return handles

    def _get_classifier_handles(self) -> list[int]:
        """Get list of classifier handles based on current mode."""
        if self.classifier_mode == ClassifierMode.ENABLED:
            return [Handle.CLASSIFIER_EVENT.value]
        return []

    async def start(self) -> None:
        """Start receiving notifications from the device."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        if self.emg_mode is None or self.imu_mode is None:
            raise ValueError("Modes not set. Call setup() first.")

        logger.info("start notifying from %s", self.device.name)
        await self.vibrate(VibrationType.SHORT)

        # Subscribe to EMG data
        for handle in self._get_emg_handles():
            await self.start_notify(handle, self.notify_callback)

        # Subscribe to IMU data
        for handle in self._get_imu_handles():
            await self.start_notify(handle, self.notify_callback)

        # Subscribe to classifier events
        for handle in self._get_classifier_handles():
            await self.start_notify(handle, self.notify_callback)

        await self.led(RGB_CYAN)

    async def start_notify(self, handle: int, callback) -> None:
        """Start notifications for a specific handle."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self._client.start_notify(handle, callback)

    async def stop(self) -> None:
        """Stop receiving notifications from the device."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        if self.emg_mode is None or self.imu_mode is None:
            raise ValueError("Modes not set. Call setup() first.")

        # Unsubscribe from all notifications
        for handle in self._get_emg_handles():
            await self.stop_notify(handle)

        for handle in self._get_imu_handles():
            await self.stop_notify(handle)

        for handle in self._get_classifier_handles():
            await self.stop_notify(handle)

        # Vibrate short*2
        try:
            await self.vibrate(VibrationType.SHORT)
            await self.vibrate(VibrationType.SHORT)
        except AttributeError:
            await asyncio.sleep(0.1)

        await self.led(RGB_GREEN)
        logger.info("stopped notification from %s", self.device.name)

    async def stop_notify(self, handle: int) -> None:
        """Stop notifications for a specific handle."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self._client.stop_notify(handle)

    async def unlock(self, unlock_type) -> None:
        """Unlock the device."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.unlock(self._client, unlock_type)

    async def user_action(self, user_action_type) -> None:
        """Send user action command."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.user_action(self._client, user_action_type)

    async def vibrate(self, vibration_type: VibrationType) -> None:
        """Vibrate the device."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.vibrate(self._client, vibration_type)

    async def vibrate2(self, duration: int, strength: int) -> None:
        """Vibrate with custom duration and strength."""
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.vibrate2(self._client, duration, strength)


