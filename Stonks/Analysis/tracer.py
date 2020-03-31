import script_context

import numpy as np
import h5py
import matplotlib.pyplot as plt
import os
import importlib
from Stonks.Analytics import Analytics

importlib.reload(Analytics)


def trace_oscillations(data, volume, threshold_down, threshold_up):
    threshold_distance = 0
    reversion_distance = 0
    average_volume = 0

    trigger_down = False
    trigger_up = False
    reversion_trigger = False

    threshold_record = []
    reversion_record = []
    volume_record = []

    for i in np.arange(data.shape[0]):
        # print('loop')
        ##################################################################
        if data[i] > threshold_up:
            # print('triggered')
            trigger_up = True
            threshold_distance += 1.
            average_volume = average_volume * (threshold_distance - 1) / threshold_distance + volume[
                i] / threshold_distance

        if data[i] < threshold_up and trigger_up:
            # print('triggered')
            trigger_up = False
            threshold_record.append(threshold_distance)
            volume_record.append(average_volume)
            threshold_distance = 0
            average_volume = 0

        ##################################################################
        if threshold_down < data[i] < threshold_up:
            reversion_trigger = True
            reversion_distance += 1
            average_volume = average_volume * (threshold_distance - 1) / threshold_distance + volume[
                i] / threshold_distance

        if (data[i] > threshold_up or data[i] < threshold_down) and reversion_trigger:
            reversion_trigger = False
            reversion_record.append(reversion_distance)
            volume_record.append(average_volume)
            reversion_distance = 0
            average_volume = 0

        ##################################################################
        if data[i] < threshold_down:
            trigger_down = True
            threshold_distance += 1
            average_volume = average_volume * (threshold_distance - 1) / threshold_distance + volume[
                i] / threshold_distance

        if data[i] > threshold_down and trigger_down:
            trigger_down = False
            threshold_record.append(threshold_distance)
            volume_record.append(average_volume)
            threshold_distance = 0
            average_volume = 0

    return np.array(threshold_record), np.array(reversion_record), np.array(volume_record)


if __name__ == "__main__":
    '''File Handling'''
    filedirectory = '../../StockData/'
    filename = 'S&P_500_2020-03-16'
    filepath = filedirectory + filename
    if os.path.exists(filepath):
        datafile = h5py.File(filepath)
    else:
        print('Data file does not exist!')

    '''
    for group_key in datafile.keys():
        group = datafile[group_key]
        print(group_key)

        for data_key in group.keys():
            dataset = group[data_key]
            print(dataset.name)
            print(dataset.shape)
    '''

    group_choice = np.random.choice(list(datafile.keys()))
    group_choice = 'SPY'

    time = datafile[group_choice]['datetime'][...]
    data_open = datafile[group_choice]['open'][...]
    data_high = datafile[group_choice]['high'][...]
    data_low = datafile[group_choice]['low'][...]
    data_volume = datafile[group_choice]['volume'][...]
    datafile.close()

    candle_data = Analytics.candle_avg(open=data_open, high=data_high, low=data_low)
    candle_sma = Analytics.moving_average(data=candle_data, period=20)
    candle_rail, _, candle_volume = trace_oscillations(data=candle_data - candle_sma,
                                                       volume=data_volume,
                                                       threshold_down=0,
                                                       threshold_up=0)

    plt.scatter(candle_rail, candle_volume)

    plt.figure()
    plt.hist(candle_rail, bins=100)
    plt.figure()
    plt.hist(candle_volume, bins=100)
