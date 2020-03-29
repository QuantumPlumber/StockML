import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import time
import arrow
import Analytics
import importlib

importlib.reload(Analytics)


def DataStack(filedirectory='../StockData/'):
    clocktime_list = []
    candle_average_list = []
    for direntry in os.scandir(filedirectory):
        if direntry.is_dir():
            continue

        if direntry.is_file():
            filepath = direntry.path
            print(filepath)
            try:
                datafile = h5py.File(filepath)
            except:
                print('could not open file: {}'.format(filepath))
                continue

        time_data = datafile['SPY']['datetime'][...]
        if time_data.shape[0] == 0:
            continue

        clock_list = []
        for i, t in enumerate(time_data):
            # gm_time = tm.gmtime(t * 1e-3)
            utc_time = arrow.get(t * 1e-3).to('utc')
            utc_time = utc_time.shift(hours=-4)  # must explicitely shift time for numpy to recognize
            time_zero = utc_time.replace(hour=0, minute=0, second=0, microsecond=0)
            delta = utc_time - time_zero
            # nyt_time = utc_time.to('America/New_York')

            clock_list.append(delta.total_seconds())

            #clock_list.append(int(utc_time.timetuple()) * 3600 + int(utc_time.time().min) * 60 + float(utc_time.time().second))

        #print(clock_list)
        clocktime_list.append(np.array(clock_list))

        open_data = datafile['SPY']['open'][...]
        high_data = datafile['SPY']['high'][...]
        low_data = datafile['SPY']['low'][...]
        candle_average_list.append(Analytics.candle_avg(open=open_data, high=high_data, low=low_data))

        datafile.close()

    fig, axs = plt.subplots(nrows=len(clocktime_list), ncols=1, figsize=(10, 20), sharex=True)

    for i, clocktime, candle_average in zip(np.arange(len(clocktime_list)), clocktime_list, candle_average_list):
        axs[i].plot(clocktime, candle_average)
        axs[i].set_xlim(left=(9*3600+30*60), right=(16*3600))

    plt.figure(figsize=(10,10))
    for i, clocktime, candle_average in zip(np.arange(len(clocktime_list)), clocktime_list, candle_average_list):
        plt.plot(clocktime, candle_average/np.max(np.abs(candle_average)))


if __name__ == '__main__':
    DataStack(filedirectory='../StockData/')
