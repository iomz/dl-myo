# dl-myo (Dongle-less Myo)

[![build status](https://github.com/iomz/dl-myo/workflows/build/badge.svg)](https://github.com/iomz/dl-myo/actions?query=workflow%3Abuild)
[![image size](https://ghcr-badge.egpl.dev/iomz/dl-myo/size?label=image%20size)](https://github.com/iomz/dl-myo/pkgs/container/dl-myo)
[![codecov](https://codecov.io/gh/iomz/dl-myo/branch/main/graph/badge.svg?token=7bC3Aa1XNN)](https://codecov.io/gh/iomz/dl-myo)
[![python Versions](https://img.shields.io/pypi/pyversions/dl-myo.svg)](https://pypi.python.org/pypi/dl-myo)
[![pypi version](https://img.shields.io/pypi/v/dl-myo.svg)](https://pypi.python.org/pypi/dl-myo)
[![license](https://img.shields.io/pypi/l/dl-myo.svg)](https://pypi.python.org/pypi/dl-myo)

dl-myo is a replacement to MyoConnect for Myo Armband without an official Myo dongle.

If you are fed up with the dongle and still need to use Myo anyway this is the right stuff to grab.

This project is a reimplementation of [Dongleless-myo](https://github.com/iomz/Dongleless-myo) (originally created by [@mamo91](https://github.com/mamo91) and enhanced by [@MyrikLD](https://github.com/MyrikLD)) using [Bleak](https://github.com/hbldh/bleak) instead of [bluepy](https://github.com/IanHarvey/bluepy), and therefore supports asyncio on multiple platforms.

The GATT service naming convention reflects the official BLE specification for Myo (i.e., [myohw.h](https://github.com/iomz/myo-bluetooth/blob/master/myohw.h)); however, some services and characteristics differ for a uniform naming.

See [`myo/handle.py`](https://github.com/iomz/dl-myo/blob/main/myo/handle.py) for more detail.

## Platform Support

| Linux | Raspberry Pi | macOS | Windows |
| :---: | :----------: | :---: | :-----: |
|  ✅   |      ✅      |  ✅   |   ✅    |

## Install

```bash
pip install dl-myo
```

## Example

The script scans a Myo device, connect, set LED colors, vibrates, collect EMG/IMU data for a moment, and then read the avaialable services/characteristics from the device.

Any Myo Armband should have the service UUID `d5060001-a904-deb9-4748-2c7f4a124842`.

```bash
python examples/sample.py
```

Otherwise, you can also bind to a specific MAC address. For example,

```bash
python examples/sample.py --mac D2:3B:85:94:32:8E
```

### Try the example with Docker

```bash
docker compose pull
docker compose run --rm dl-myo
```

## Build (requires [Poetry](https://python-poetry.org/)

```bash
poetry install
poetry build
```

## Author

[@iomz](https://github.com/iomz) (Iori Mizutani)
