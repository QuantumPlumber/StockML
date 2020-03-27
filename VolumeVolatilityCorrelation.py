import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import Analytics
import time as tm

import importlib

importlib.reload(Analytics)

if __name__ == "__main__":
    # File Handling

    filedirectory = '../StockData/'
    filename = 'S&P_500_10Day_2020-03-26'
    filepath = filedirectory + filename
    if os.path.exists(filepath):
        datafile = h5py.File(filepath)
    else:
        print('Data file does not exist!')

    # group_choice = np.random.choice(list(datafile.keys()))
    group_choice = 'SPY'

    time = datafile[group_choice]['datetime'][...]
    data_open = datafile[group_choice]['open'][...]
    data_high = datafile[group_choice]['high'][...]
    data_low = datafile[group_choice]['low'][...]
    data_vol = datafile[group_choice]['volume'][...]
    datafile.close()

    candle_range = np.absolute(data_high - data_low)
    candle_average = Analytics.candle_avg(open=data_open, high=data_high, low=data_low)

    range_average = np.sum(candle_range) / candle_range.shape
    vol_average = np.sum(data_vol) / data_vol.shape

    ####################################################################################################################

    plt.figure(figsize=(10, 10))
    plt.hist(data_vol, range=[0, 1e6], bins=100)

    plt.figure(figsize=(10, 10))
    plt.hist(candle_range, range=[0, 2.5], bins=100)

    # plt.figure(figsize=(10, 10))
    # plt.hist2d(x=data_vol[candle_range > .25], y=candle_range[candle_range > .25], range=[[0, 4e4], [0, 2.5]], bins=50)

    plt.figure(figsize=(10, 10))
    plt.suptitle('volume vs candle range')
    plt.hist2d(x=data_vol[data_vol > 1e5], y=candle_range[data_vol > 1e5], range=[[1e5, 1e6], [0, 2.5]], bins=50)

    plt.figure(figsize=(10, 10))
    plt.suptitle('candle range vs candle range second mode')
    plt.hist2d(x=candle_range[data_vol > 1e5][1:], y=candle_range[data_vol > 1e5][:-1], range=[[0, 2.5], [0, 2.5]],
               bins=50)

    plt.figure(figsize=(10, 10))
    plt.suptitle('volume vs volume first mode')
    plt.hist2d(x=data_vol[data_vol < 1e5][1:], y=data_vol[data_vol < 1e5][:-1], range=[[0, 1e5], [0, 1e5]], bins=50)

    plt.figure(figsize=(10, 10))
    plt.suptitle('volume vs volume second mode')
    plt.hist2d(x=data_vol[data_vol > 1e5][1:], y=data_vol[data_vol > 1e5][:-1], range=[[1e5, 1e6], [1e5, 1e6]], bins=50)

    ####################################################################################################################
    periods = np.arange(start=1, stop=10, step=2)
    fig, axs = plt.subplots(nrows=5, ncols=4, figsize=(20, 20))
    for period, ax_row in zip(periods, np.arange(periods.shape[0])):
        sma_candle_range = Analytics.moving_average(data=candle_range, period=period)
        sma_vol = Analytics.moving_average(data=data_vol, period=period)

        axs[ax_row, 0].set_title('sma volume')
        axs[ax_row, 0].hist(sma_vol[sma_vol > 1.5e5], range=[0, 1e6], bins=100)

        axs[ax_row, 1].set_title('sma candle range')
        axs[ax_row, 1].hist(sma_candle_range[sma_vol > 1.5e5], range=[0, 2.], bins=100)

        axs[ax_row, 2].set_title('sma volume vs sma candle range')
        axs[ax_row, 2].hist2d(x=sma_vol[sma_vol > 1.5e5], y=sma_candle_range[sma_vol > 1.5e5],
                              range=[[1.5e5, 1e6], [0, 1.5]], bins=50)

        axs[ax_row, 3].set_title('sma candle range vs sma candle range')
        axs[ax_row, 3].hist2d(x=sma_candle_range[sma_vol > 1.5e5][1:], y=sma_candle_range[sma_vol > 1.5e5][:-1],
                              range=[[0, 1.5], [0, 1.5]], bins=50)

    ####################################################################################################################
    periods = np.arange(start=1, stop=10, step=2)
    fig, axs = plt.subplots(nrows=5, ncols=2, figsize=(10, 10))
    for i, ax_row in zip(periods, np.arange(periods.shape[0])):
        candle_offset = Analytics.offset_price(data=candle_average, period=i)

        axs[ax_row, 0].hist(candle_offset, bins=100)

        axs[ax_row, 1].hist2d(x=data_vol[data_vol > 1e5], y=candle_offset[data_vol > 1e5],
                              range=[[1.5e5, 1e6], [-2.5, 2.5]],
                              bins=50)

    ####################################################################################################################
