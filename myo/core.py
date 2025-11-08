"""
myo.core
----------------
The core Myo BLE device manager (Myo) and
a wrapper class (MyoClient) to handle the connection to Myo devices

"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
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
        """
        Initialize the Myo instance with no discovered BLE device.

        The internal `_device` attribute is set to `None`
            and will be populated by discovery helpers when a device is found.
        """
        self._device: Optional[BLEDevice] = None

    @property
    def device(self) -> BLEDevice:
        """
        Get the discovered BLE device.

        Returns:
            BLEDevice: The discovered BLE device.

        Raises:
            ValueError: If no device has been discovered; call `with_mac()` or `with_uuid()` first.
        """
        if self._device is None:
            raise ValueError("Device not discovered. Call with_mac() or with_uuid() first.")
        return self._device

    @classmethod
    async def with_mac(cls, mac: str) -> Optional["Myo"]:
        """
        Discover a Myo device by its Bluetooth MAC address.

        Parameters:
            mac (str): MAC address of the device (e.g., "D2:3B:85:94:32:8E").

        Returns:
            Optional[Myo]: A Myo instance when a device with the specified MAC is found, `None` otherwise.
        """

        def match_myo_mac(device: BLEDevice, _: AdvertisementData) -> bool:
            """
            Determine whether the given BLE device's MAC address matches the target MAC (case-insensitive).

            Parameters:
                device (BLEDevice): The BLE device whose address will be compared.
                _ (AdvertisementData): Unused advertisement data parameter provided by the scanner callback.

            Returns:
                bool: `True` if the device's address equals the target MAC ignoring case, `False` otherwise.
            """
            return mac.lower() == device.address.lower()

        self = cls()
        try:
            self._device = await BleakScanner.find_device_by_filter(match_myo_mac, cb=dict(use_bdaddr=True))
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
        Discover a Myo BLE device by matching its service UUID and return a Myo configured with the found device.

        Returns:
            Optional[Myo]: A Myo instance with its device set if a matching device is found, `None` otherwise.
        """

        def match_myo_uuid(_: BLEDevice, adv: AdvertisementData) -> bool:
            """
            Check whether the advertisement contains the Myo service UUID.

            Parameters:
                adv (AdvertisementData): Advertisement payload whose service UUIDs will be inspected.

            Returns:
                `true` if any service UUID in `adv.service_uuids` matches `GATTProfile.MYO_SERVICE`
                    (comparison is case-insensitive), `false` otherwise.
            """
            uuids = adv.service_uuids or []
            target = str(GATTProfile.MYO_SERVICE).lower()
            return any(target == uuid.lower() for uuid in uuids)

        self = cls()
        self._device = await BleakScanner.find_device_by_filter(match_myo_uuid, cb=dict(use_bdaddr=True))
        if self._device is None:
            logger.error("could not find device with service UUID %s", GATTProfile.MYO_SERVICE)
            return None

        return self

    async def battery_level(self, client: BleakClient) -> int:
        """
        Return the device battery level as a percentage.

        Parameters:
            client (BleakClient): Connected BleakClient used to read the GATT characteristic.

        Returns:
            int: Battery level as an integer percentage from 0 to 100.

        Raises:
            ValueError: If the battery characteristic payload is empty.
        """
        val = await client.read_gatt_char(Handle.BATTERY_LEVEL.value)
        if not val:
            raise ValueError("Empty battery characteristic payload")
        return int.from_bytes(val, "little")

    async def command(self, client: BleakClient, cmd: Command) -> None:
        """
        Send a Command payload to the device's COMMAND GATT characteristic.

        Parameters:
            cmd (Command): Command object whose payload will be written to the COMMAND characteristic
                (performed as a write-with-response).
        """
        await client.write_gatt_char(Handle.COMMAND.value, cmd.data, True)

    async def deep_sleep(self, client: BleakClient) -> None:
        """Put the device into deep sleep mode."""
        await self.command(client, DeepSleep())

    async def led(self, client: BleakClient, logo: list[int], line: list[int]) -> None:
        """
        Set the device's logo and line LEDs to the specified RGB colors.

        Parameters:
            logo (list[int]): Three integers [r, g, b] for the logo LED, each 0–255.
            line (list[int]): Three integers [r, g, b] for the line LED, each 0–255.

        Raises:
            ValueError: If either `logo` or `line` does not have exactly three integers
                or contains values outside 0–255.
        """
        if len(logo) != 3 or len(line) != 3:
            raise ValueError(f"LED data must be [r, g, b] format. Got logo={logo}, line={line}")

        for color_list, name in [(logo, "logo"), (line, "line")]:
            if any(not isinstance(v, int) or v < 0 or v > 255 for v in color_list):
                raise ValueError(f"{name} values must be integers between 0 and 255: {color_list}")

        await self.command(client, LED(logo, line))

    async def set_mode(
        self,
        client: BleakClient,
        classifier_mode: ClassifierMode,
        emg_mode: EMGMode,
        imu_mode: IMUMode,
    ) -> None:
        """
        Configure the device's classifier, EMG, and IMU operating modes.

        Parameters:
            classifier_mode (ClassifierMode): Classifier mode to apply.
            emg_mode (EMGMode): EMG data mode to apply.
            imu_mode (IMUMode): IMU mode to apply.
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
        """
        Set the device's sleep mode.

        Parameters:
            client (BleakClient): Connected BLE client used to send the command.
            sleep_mode (SleepMode): Target sleep mode to apply on the device.
        """
        await self.command(client, SetSleepMode(sleep_mode))

    async def unlock(self, client: BleakClient, unlock_type) -> None:
        """
        Send an unlock command to the device with the specified unlock behavior.

        Parameters:
            unlock_type: Value specifying the unlock behavior
                (typically an enum value understood by the device, e.g., timed or hold).
        """
        await self.command(client, Unlock(unlock_type))

    async def user_action(self, client: BleakClient, user_action_type) -> None:
        """
        Send a user action command to the connected Myo device.

        Parameters:
            user_action_type: The user action identifier (e.g., enum or int)
                specifying which user action the device should perform.
        """
        await self.command(client, UserAction(user_action_type))

    async def vibrate(self, client: BleakClient, vibration_type: VibrationType) -> None:
        """
        Trigger a vibration on the Myo device.

        Sends a vibrate command via the provided BleakClient. If the client lacks the expected connection attribute,
            the method catches the resulting AttributeError and logs debug information instead of raising.
        """
        try:
            await self.command(client, Vibrate(vibration_type))
        except AttributeError:
            logger.debug(
                "Myo.vibrate() raised AttributeError, BleakClient.is_connected: %s",
                getattr(client, "is_connected", None),
            )

    async def vibrate2(self, client: BleakClient, duration: int, strength: int) -> None:
        """
        Trigger a vibration on the device with the specified duration and strength.

        Parameters:
            client (BleakClient): BLE client used to send the vibration command.
            duration (int): Vibration duration in milliseconds (0 for no duration).
            strength (int): Vibration strength from 0 to 255, where 255 is maximum.
        """
        await self.command(client, Vibrate2(duration, strength))

    async def write(self, client: BleakClient, handle: int, value: bytes) -> None:
        """
        Write the given bytes to the GATT characteristic identified by `handle`
            on the provided BLE client using a write-with-response.

        Parameters:
            handle (int): GATT characteristic handle to write to.
            value (bytes): Payload bytes to write.
        """
        await client.write_gatt_char(handle, value, True)


class MyoClient(ABC):
    """High-level client for interacting with Myo devices."""

    def __init__(self, aggregate_all: bool = False, aggregate_emg: bool = False) -> None:
        """
        Create a MyoClient and configure how incoming sensor data should be aggregated.

        Parameters:
            aggregate_all (bool): If True, FV (filtered EMG) and IMU data are buffered and paired
                so they are delivered together as aggregated data.
            aggregate_emg (bool): If True, EMG samples from multiple channels are combined
                into per-sample aggregated EMG events before being forwarded to handlers.
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
        Create a MyoClient configured for a discovered device and establish its BLE connection.

        Parameters:
            mac (Optional[str]): Specific device MAC address to discover;
                if omitted or empty, discovery uses service UUID.
            aggregate_all (bool): When True, aggregate FV and IMU data before delivering to handlers.
            aggregate_emg (bool): When True, aggregate EMG samples into individual aggregated samples.

        Returns:
            MyoClient: A MyoClient instance connected to the discovered device.
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
        """
        Get the underlying discovered BLE device.

        Returns:
            BLEDevice: The discovered BLE device instance.

        Raises:
            ValueError: If no device has been discovered; call with_device() first.
        """
        if self.m is None:
            raise ValueError("Device not initialized. Call with_device() first.")
        return self.m.device

    async def battery_level(self) -> int:
        """
        Retrieve the device's battery level as a percentage.

        Returns:
            int: Battery level from the connected device (0–100).

        Raises:
            ValueError: If the client is not connected (call connect() first).
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        return await self.m.battery_level(self._client)

    async def connect(self) -> None:
        """
        Connect to the discovered Myo device and establish a BLE session.

        Raises:
            ValueError: if no device has been discovered via with_device().
            RuntimeError: if creating the BLE client instance fails.
        """
        if self.m is None:
            raise ValueError("Device not discovered. Call with_device() first.")

        self._client = BleakClient(self.device)
        if self._client is None:
            raise RuntimeError("Failed to create BLE client")

        await self._client.connect()
        logger.info("connected to %s: %s", self.device.name, self.device.address)

    async def deep_sleep(self) -> None:
        """
        Put the connected Myo device into deep sleep mode.

        Raises:
            ValueError: If the client is not connected; call `connect()` first.
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.deep_sleep(self._client)

    async def disconnect(self) -> None:
        """
        Disconnect from the discovered Myo device and clear the internal client state.

        If no active connection exists, the call is a no-op (a warning is logged).
            After completion the internal Bleak client reference is cleared.
        """
        if self._client is None:
            logger.warning("connection is already closed")
            return

        await self._client.disconnect()
        device_name = self.device.name if self.m else "unknown"
        self._client = None
        logger.info("disconnected from %s", device_name)

    async def get_services(self, indent: int = 1) -> str:
        """
        Return a JSON string describing discovered GATT services and their characteristics.

        Only services whose handle can be mapped to a known Handle name are included.
        Each service is keyed by its hex handle and contains "name", "uuid", and "chars";
        characteristics are keyed by their hex handles
        and include the dictionary produced for each characteristic when available.

        Parameters:
            indent (int): JSON indentation level used when serializing the result.

        Returns:
            str: JSON string with the structure {"services": { "<service_handle_hex>":
                {"name": str, "uuid": str, "chars": { "<char_handle_hex>": {...} } } } }.

        Raises:
            ValueError: If no BLE client connection exists (call connect() first).
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
        Set both logo and line LEDs to the same RGB color.

        Parameters:
            color (list[int]): RGB triplet [r, g, b] with each component in 0-255.

        Raises:
            ValueError: if not connected (call connect() first).
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.led(self._client, color, color)

    @abstractmethod
    async def on_classifier_event(self, ce: ClassifierEvent) -> None:
        """
        Handle a classifier event dispatched by the device.

        Parameters:
            ce (ClassifierEvent): Classifier event payload received from the Myo device.
        """
        raise NotImplementedError()

    async def on_data(self, data: Union[FVData, IMUData]) -> None:
        """
        Aggregate incoming FVData and IMUData until a matching pair is available,
            then deliver them as an AggregatedData to on_aggregated_data.

        This method stores the latest FVData or IMUData sample and, when both types are present,
        calls on_aggregated_data(...) with an AggregatedData combining them and then resets the stored samples.
        Operation is synchronized using the client's internal lock to ensure safe concurrent updates.

        Parameters:
            data (Union[FVData, IMUData]): A single incoming FV or IMU data sample.
        """
        async with self._lock:
            if isinstance(data, FVData):
                self.fv_aggregated = data
            elif isinstance(data, IMUData):
                self.imu_aggregated = data
            # trigger on_aggregated_data when both FVData and IMUData are ready
            if all(d is not None for d in (self.fv_aggregated, self.imu_aggregated)):
                await self.on_aggregated_data(AggregatedData(self.fv_aggregated, self.imu_aggregated))
                self.fv_aggregated = None
                self.imu_aggregated = None

    @abstractmethod
    async def on_aggregated_data(self, ad: AggregatedData) -> None:
        """
        Handle aggregated FV and IMU measurements and deliver them to the client.

        Called when both FV and IMU samples are available; EMG data is not included
        because it is produced at a different rate (200 Hz vs 50 Hz).

        Parameters:
            ad (AggregatedData): Aggregated structure containing the paired FV and IMU samples.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_emg_data(self, emg: EMGData) -> None:
        """
        Handle an incoming EMG data packet.

        Parameters:
            emg (EMGData): EMG data containing two sequential samples, each with eight channel values.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_emg_data_aggregated(self, eds: EMGDataSingle) -> None:
        """
        Handle a single aggregated EMG data sample.

        Parameters:
            eds (EMGDataSingle): The EMG sample to process; subclasses implement how the sample is consumed.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_fv_data(self, fvd: FVData) -> None:
        """
        Handle an incoming filtered-value (FV) sensor sample.

        Subclasses must implement this to process or forward the provided FVData.

        Parameters:
            fvd (FVData): The filtered-value data payload received from the device.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_imu_data(self, imu: IMUData) -> None:
        """
        Handle incoming IMU data events.

        Called when a parsed IMUData sample is received; implement to process orientation, accelerometer,
        and gyroscope values carried by `imu`.

        Parameters:
            imu (IMUData): Parsed IMU sample containing orientation, acceleration, and angular velocity.
        """
        raise NotImplementedError()

    @abstractmethod
    async def on_motion_event(self, me: MotionEvent) -> None:
        """
        Handle an incoming motion event.

        Parameters:
            me (MotionEvent): Motion event information (e.g., tap, orientation change) to be handled by the client.
        """
        raise NotImplementedError()

    async def notify_callback(self, sender: BleakGATTCharacteristic, data: bytearray) -> None:
        """
        Route an incoming GATT notification to the appropriate event handler based on its characteristic handle.

        When the characteristic corresponds to FV or IMU data and `aggregate_all` is enabled,
        forwards the parsed data to the aggregation path; otherwise dispatches to the FV/IMU handlers.
        For EMG characteristics, if `aggregate_emg` is enabled, forwards each parsed single EMG sample
        to the aggregated-EMG handler; otherwise dispatches the full EMG frame to the EMG handler.
        Classifier and motion events are parsed and dispatched to their respective handlers.

        Parameters:
            sender (BleakGATTCharacteristic): Characteristic that produced the notification
                (used to determine the handle).
            data (bytearray): Raw notification payload to be parsed and dispatched.
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
        Configure the device's classifier, EMG, and IMU operating modes.

        Parameters:
            classifier_mode (ClassifierMode): Desired classifier mode.
            emg_mode (EMGMode): Desired EMG data mode.
            imu_mode (IMUMode): Desired IMU data mode.

        Raises:
            ValueError: If the client is not connected (call connect() first).
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
        """
        Configure the device sleep mode.

        Parameters:
            sleep_mode (SleepMode): Desired sleep mode to apply to the device.

        Raises:
            ValueError: If the client is not connected (call connect() first).
        """
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
        Configure the connected Myo device for operation and apply initial runtime settings.

        Performs an initial setup sequence on the already-connected device: indicates status with LEDs,
        reads and logs battery level, vibrates briefly, disables automatic sleep, and applies the requested classifier,
        EMG, and IMU modes.
        If `aggregate_all` was enabled on this client, mode values are overridden to the values
        required for aggregation.

        Parameters:
            classifier_mode (ClassifierMode): Desired classifier mode to apply
                (ignored if aggregation forces a different mode).
            emg_mode (EMGMode): Desired EMG data mode to apply (ignored if aggregation forces a different mode).
            imu_mode (IMUMode): Desired IMU data mode to apply (ignored if aggregation forces a different mode).
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
        """
        Put the connected Myo device into normal sleep mode and disconnect it.

        This sets the device LED to pink, applies the normal sleep mode,
        waits 0.5 seconds to allow the device to enter sleep, and then disconnects the BLE client.
        """
        logger.info("sleep %s", self.device.name)
        await self.led(RGB_PINK)
        await self.set_sleep_mode(SleepMode.NORMAL)
        await asyncio.sleep(0.5)
        await self.disconnect()

    def _get_emg_handles(self) -> list[int]:
        """
        Return EMG-related GATT characteristic handles for the current EMG mode.

        Returns:
            list[int]: Handles to subscribe to — four EMG channel handles when `emg_mode` is `SEND_EMG` or `SEND_RAW`,
                the filtered FV handle when `emg_mode` is `SEND_FILT`, or an empty list otherwise.
        """
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
        """
        Determine which IMU-related GATT characteristic handles should be subscribed to based on the current IMU mode.

        Returns:
            list[int]: A list of integer GATT handles to subscribe for IMU data.
                May include the `IMU_DATA` handle when IMU mode is neither `NONE` nor `SEND_EVENTS`,
                and the `MOTION_EVENT` handle when IMU mode is `SEND_EVENTS` or `SEND_ALL`.
        """
        handles = []
        if self.imu_mode not in [IMUMode.NONE, IMUMode.SEND_EVENTS]:
            handles.append(Handle.IMU_DATA.value)
        if self.imu_mode in [IMUMode.SEND_EVENTS, IMUMode.SEND_ALL]:
            handles.append(Handle.MOTION_EVENT.value)
        return handles

    def _get_classifier_handles(self) -> list[int]:
        """
        Return the list of GATT characteristic handles used for classifier events when the classifier is enabled.

        Returns:
            list[int]: A list containing the classifier event handle, or an empty list if the classifier is not enabled.
        """
        if self.classifier_mode == ClassifierMode.ENABLED:
            return [Handle.CLASSIFIER_EVENT.value]
        return []

    async def start(self) -> None:
        """
        Start notification streaming from the connected device and enable device indicators.

        Subscribes to EMG, IMU, and classifier notification handles, triggers a short vibration,
        and sets the LED to cyan.

        Raises:
            ValueError: If not connected or device modes have not been configured via setup().
        """
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
        """
        Start notifications for the given GATT characteristic handle.

        Parameters:
            handle (int): GATT characteristic handle to subscribe to.
            callback (callable): Notification callback receiving (sender, data).

        Raises:
            ValueError: If no BLE client is connected (call connect() first).
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self._client.start_notify(handle, callback)

    async def stop(self) -> None:
        """
        Stop all active data notifications and indicate idle state on the device.

        Unsubscribes from EMG, IMU, and classifier notification handles, attempts two short vibrations,
        and sets the LED to green.

        Raises:
            ValueError: If not connected (call connect()) or if modes are not set (call setup()).
        """
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
        """
        Stop notifications for the given GATT characteristic handle.

        Parameters:
            handle (int): GATT characteristic handle whose notifications should be stopped.

        Raises:
            ValueError: If the client is not connected.
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self._client.stop_notify(handle)

    async def unlock(self, unlock_type) -> None:
        """
        Send an unlock command to the connected Myo device using the specified unlock type.

        Parameters:
            unlock_type: Unlock command type that specifies the unlock behavior.

        Raises:
            ValueError: If the client is not connected (call connect() first).
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.unlock(self._client, unlock_type)

    async def user_action(self, user_action_type) -> None:
        """
        Send a user action command to the connected Myo device.

        Parameters:
            user_action_type: The user action identifier to send (device-specific enum or value).

        Raises:
            ValueError: If the client is not connected (call connect() first).
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.user_action(self._client, user_action_type)

    async def vibrate(self, vibration_type: VibrationType) -> None:
        """
        Trigger a vibration on the connected Myo device.

        Parameters:
            vibration_type (VibrationType): The vibration pattern/strength to send to the device.

        Raises:
            ValueError: If the client is not connected (call connect() first).
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.vibrate(self._client, vibration_type)

    async def vibrate2(self, duration: int, strength: int) -> None:
        """
        Trigger a vibration on the device using the specified duration and strength.

        Parameters:
            duration (int): Vibration duration (device-specific units).
            strength (int): Vibration intensity (device-specific range).

        Raises:
            ValueError: If no BLE connection is established (call connect() first).
        """
        if self._client is None:
            raise ValueError("Not connected. Call connect() first.")
        await self.m.vibrate2(self._client, duration, strength)
