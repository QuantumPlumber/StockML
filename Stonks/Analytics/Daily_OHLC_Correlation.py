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

    filedirectory = 'D:/StockData/Daily_History/'
    filename = 'S&P_500_Daily_2020-06-13'
    filepath = filedirectory + filename
    if os.path.exists(filepath):
        datafile = h5py.File(filepath)
    else:
        print('Data file does not exist!')

    # group_choice = np.random.choice(list(datafile.keys()))
    group_choice = 'SPY'

    data_time = datafile[group_choice]['datetime'][...]
    # print(data_time.shape)
    # tradeable = Analytics.market_hours(data_time)

    # [data_vol > 1e5]
    data_vol = datafile[group_choice]['volume'][...]
    data_time = data_time
    data_open = datafile[group_choice]['open'][...]
    data_high = datafile[group_choice]['high'][...]
    data_low = datafile[group_choice]['low'][...]
    data_close = datafile[group_choice]['close'][...]
    # data_vol = data_vol[data_vol > 1e5]
    datafile.close()

    ####################################################################################################################

    inter_day_move = data_close[1:] - data_open[1:]
    intra_day_move = data_close[:-1] - data_open[1:]

    inter_day_range = np.absolute(data_high - data_low)

    range_average = np.sum(inter_day_range) / inter_day_range.shape
    vol_average = np.sum(data_vol) / data_vol.shape

    low_range = -2.5
    high_range = 2.5
    bins = 50

    plt.figure(figsize=(10, 10))
    plt.suptitle('inter_day_move')
    plt.hist(inter_day_move, range=(low_range, high_range), bins=50)

    plt.figure(figsize=(10, 10))
    plt.suptitle('intra_day_move')
    plt.hist(intra_day_move, range=(low_range, high_range), bins=50)

    plt.figure(figsize=(10, 10))
    plt.suptitle('intra_day_move vs inter_day_move')
    plt.hist2d(x=intra_day_move,
               y=inter_day_move,
               range=((low_range, high_range), (low_range, high_range)),
               bins=50)
    #plt.scatter(x=intra_day_move, y=inter_day_move)

    plt.figure(figsize=(10, 10))
    plt.suptitle('intra_day_move 1st moment')
    plt.hist2d(x=intra_day_move[:-1],
               y=intra_day_move[1:],
               range=((low_range, high_range), (low_range, high_range)),
               bins=50)
    #plt.scatter(x=intra_day_move, y=inter_day_move)


    moments = 5
    cut = np.arange(intra_day_move.shape[0]-moments)
    x_moments = np.empty(shape=0)
    y_moments = np.empty(shape=0)
    for m in np.arange(start=1, stop=moments+1):
        x_moments = np.append(x_moments, intra_day_move[cut])
        y_moments = np.append(y_moments, intra_day_move[cut+m])

    plt.figure(figsize=(10, 10))
    plt.suptitle('intra_day_move n moment')
    plt.hist2d(x=x_moments,
               y=y_moments,
               range=((low_range, high_range), (low_range, high_range)),
               bins=50)
    #plt.scatter(x=intra_day_move, y=inter_day_move)