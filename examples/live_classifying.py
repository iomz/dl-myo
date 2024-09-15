#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging
import serial
import time

from myo import AggregatedData, MyoClient
from myo.types import (
   ClassifierEvent,
   ClassifierMode,
   EMGData,
   EMGMode,
   FVData,
   IMUData,
   IMUMode,
   MotionEvent,
   VibrationType,
)
from myo.constants import RGB_PINK
import pandas as pd
import numpy as np
import ydf
from scipy import stats

global model
model = ydf.load_model("model_03_21_2024") #load RDF model


global df
global classification_arr
classification_arr = np.zeros(25) #keeps array of 25 latest classifications. Mode of array is final output. Helps
                                  #filter out misclassifications.

df = pd.DataFrame(columns=['channel 1', 'channel 2', 'channel 3', 'channel 4', 'channel 5', 'channel 6', 'channel 7',
                           'channel 8', 'channel 9', 'channel 10', 'channel 11', 'channel 12', 'channel 13', 'channel 14', 'channel 15',
                           'channel 16','channel 17','channel 18'])

arduino = serial.Serial(port='COM16',   baudrate=115200, timeout=0.1,write_timeout = 0.0)


class SampleClient(MyoClient):

    # global df
    # df = pd.DataFrame(columns=['channel 1', 'channel 2', 'channel 3', 'channel 4', 'channel 5', 'channel 6', 'channel 7',
    #                        'channel 8', 'channel 9', 'channel 10', 'channel 11', 'channel 12', 'channel 13', 'channel 14', 'channel 15','channel 16'])

    global i
    i = 0

    global array

    async def on_classifier_event(self, ce: ClassifierEvent):
        # logging.info(ce.json())
        print(1)
        pass

    async def on_aggregated_data(self, ad: AggregatedData):
        logging.info(ad)
        global model
        global df
        global classification_arr

        string = str(ad)
        array = string.split(',')
        array = np.array(array).reshape(1, 18)
        df = pd.DataFrame(array,columns=['channel 1', 'channel 2', 'channel 3', 'channel 4', 'channel 5', 'channel 6', 'channel 7',
                           'channel 8', 'channel 9', 'channel 10', 'channel 11', 'channel 12', 'channel 13',
                           'channel 14', 'channel 15',
                           'channel 16', 'channel 17', 'channel 18'])
        df = df.iloc[:, : 8]
        # print(df)
        prediction = model.predict(df)
        # maximum = max(prediction)
        index = prediction.argmax()
        classification_arr = np.roll(classification_arr,-1)
        classification_arr[-1] = index

        # print(prediction)
        # print(index)
        # df.plot()
        # arduino.write(index + 1)
        if (stats.mode(classification_arr)[0] == 1): #use mode to determine output
            # arduino.write(str.encode('1'))
            arduino.write(bytes('1', 'utf-8'))
            # arduino_print = arduino.readline()
            # print(arduino_print)
            print('rest')
            # print(index)

        elif (stats.mode(classification_arr)[0] == 0):
            # arduino.write(str.encode('2'))
            arduino.write(bytes('2', 'utf-8'))
            # arduino_print = arduino.readline()
            # print(arduino_print)
            print('fist')
            # print(index)
        else:
            # arduino.write(str.encode('3'))
            arduino.write(bytes('3', 'utf-8'))
            # arduino_print = arduino.readline()
            # print(arduino_print)
            print('pinch')
            # print(index)
        # try:
        #     if(index == 1):
        #         # arduino.write(str.encode('1'))
        #         arduino.write(bytes('1','utf-8'))
        #         # arduino_print = arduino.readline()
        #         # print(arduino_print)
        #         print('REST')
        #     elif(index == 0):
        #         # arduino.write(str.encode('2'))
        #         arduino.write(bytes('2', 'utf-8'))
        #         # arduino_print = arduino.readline()
        #         # print(arduino_print)
        #         print('FIST')
        #     else:
        #         # arduino.write(str.encode('3'))
        #         arduino.write(bytes('3', 'utf-8'))
        #         # arduino_print = arduino.readline()
        #         # print(arduino_print)/
        #         print('PINCH')
        # except:
        #     waste = 1
        # print("Probabilities: " + prediction + "\n" + "Max: "+ maximum + "\n" + "Index: " + index + "\n")

    async def on_emg_data(self, emg: EMGData):
        # logging.info(emg)
        print(3)
        pass

    async def on_fv_data(self, fvd: FVData):
        # logging.info(fvd.json())
        print(4)
        pass

    async def on_imu_data(self, imu: IMUData):
        # logging.info(imu.json())
        print(5)
        pass

    async def on_motion_event(self, me: MotionEvent):
        # logging.info(me.json())
        print(6)


async def main(args: argparse.Namespace):

    # global df
    #
    # df = pd.DataFrame(columns=['channel 1', 'channel 2', 'channel 3', 'channel 4', 'channel 5', 'channel 6', 'channel 7',
    #                        'channel 8', 'channel 9', 'channel 10', 'channel 11', 'channel 12', 'channel 13', 'channel 14', 'channel 15',
    #                        'channel 16'])


    logging.info("scanning for a Myo device...")

    sc = await SampleClient.with_device(mac=args.mac, aggregate_all=True)

    # get the available services on the myo device
    info = await sc.get_services()
    logging.info(info)

    # setup the MyoClient
    await sc.setup(
        classifier_mode=ClassifierMode.ENABLED,
        emg_mode=EMGMode.SEND_FILT,  # for aggregate_all
        imu_mode=IMUMode.SEND_ALL,  # for aggregate_all
    )

    # start the indicate/notify
    await sc.start()

    # receive notifications for 5 seconds
    # time = 5.0
    # await asyncio.sleep(int(time))
    await asyncio.Future()

    df.to_csv('g_ian_two_pinch_no_wrist.csv')


    # y_1 = df['channel 1'].astype(int).to_numpy()
    # y_2 = df['channel 2'].astype(int).to_numpy()
    # y_3 = df['channel 3'].astype(int).to_numpy()
    # y_4 = df['channel 4'].astype(int).to_numpy()
    # y_5 = df['channel 5'].astype(int).to_numpy()
    # y_6 = df['channel 6'].astype(int).to_numpy()
    # y_7 = df['channel 7'].astype(int).to_numpy()
    # y_8 = df['channel 8'].astype(int).to_numpy()
    # print(y_1)
    # time_plot = np.arange(0,time,time / y_1.size)
    # plt.figure(facecolor = '#cccccc')
    #
    # plt.subplot(4, 2, 1)
    # plt.plot(time_plot, y_1, color='#cc0000')
    # plt.title('Channel 1')
    # plt.xlabel('Time (s)')
    # plt.locator_params(axis='both', nbins=4)
    # plt.subplot(4, 2, 2)
    # plt.plot(time_plot, y_2,color = '#ff9900')
    # plt.title('Channel 2')
    # plt.xlabel('Time (s)')
    # plt.locator_params(axis='both', nbins=4)
    # plt.subplot(4, 2, 3)
    # plt.plot(time_plot, y_3,color = '#cc9900')
    # plt.title('Channel 3')
    # plt.xlabel('Time (s)')
    # plt.locator_params(axis='y', nbins=4)
    # plt.subplot(4, 2, 4)
    # plt.plot(time_plot, y_4,color = '#cccc00')
    # plt.title('Channel 4')
    # plt.xlabel('Time (s)')
    # plt.locator_params(axis='both', nbins=4)
    # plt.subplot(4, 2, 5)
    # plt.plot(time_plot, y_5,color = '#009933')
    # # plt.plot(y_5)
    # plt.title('Channel 5')
    # plt.xlabel('Time (s)')
    # plt.locator_params(axis='both', nbins=4)
    # plt.subplot(4, 2, 6)
    # plt.plot(time_plot, y_6,color = '#006699')
    # # plt.plot(y_6)
    # plt.title('Channel 6')
    # plt.xlabel('Time (s)')
    # plt.locator_params(axis='both', nbins=4)
    # plt.subplot(4, 2, 7)
    # plt.plot(time_plot, y_7,color = '#993366')
    # # plt.plot(y_7)
    # plt.title('Channel 7')
    # plt.xlabel('Time (s)')
    # plt.locator_params(axis='both', nbins=4)
    # plt.subplot(4, 2, 8)
    # plt.plot(time_plot, y_8,color = '#660066')
    # # plt.plot(y_8)
    # plt.title('Channel 8')
    # plt.xlabel('Time (s)')
    # plt.locator_params(axis='both', nbins=4)
    # plt.tight_layout()
    # # plt.set_facecolor('black')
    # # ax = plt.axes()

    # Setting the background color of the plot
    # using set_facecolor() method
    # ax.set_facecolor("#1CC4AF")
    # plt.show()

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
    parser.add_argument(
        "--seconds",
        default=10,
        help="seconds to read data",
        metavar="<seconds>",
        type=int,
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    asyncio.run(main(args))