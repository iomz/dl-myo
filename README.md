# dl-myo (Dongle-less Myo)

[![PyPI Version](https://badge.fury.io/py/dl-myo.svg)](https://badge.fury.io/py/dl-myo)
[![Build Status](https://github.com/iomz/dl-myo/workflows/Build/badge.svg)](https://github.com/iomz/dl-myo/actions?query=workflow%3ABuild)

dl-myo is a replacement to MyoConnect for Myo Armband without an official Myo dongle.

If you are fed up with the dongle and still need to use Myo anyway this is the right stuff to grab.

This project is a reimplementation of [Dongleless-myo](https://github.com/iomz/Dongleless-myo) (originally created by [@mamo91] and enhanced by [@MyrikLD]) using [Bleak](https://github.com/hbldh/bleak) instead of [bluepy](https://github.com/IanHarvey/bluepy), and therefore supports asyncio on multiple platforms.

## Platform Support

|       Linux        |    Raspberry Pi    |       macOS        |      Windows       |
| :----------------: | :----------------: | :----------------: | :----------------: |
| :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |

## Install

```bash
pip install dl-myo
```

## Example

```bash
python examples/sample.py
```
