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
    date_list = []
    tradeable_list = []
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
            print('no \'SPY\' data in file: {}'.format(filepath))
            continue

        clock_list = []
        market_hours_list = []
        for i, t in enumerate(time_data):
            # gm_time = tm.gmtime(t * 1e-3)
            utc_time = arrow.get(t * 1e-3).to('utc')
            utc_time = utc_time.shift(hours=-4)  # must explicitely shift time for numpy to recognize
            market_open = utc_time.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = utc_time.replace(hour=16, minute=0, second=0, microsecond=0)
            open_delta = utc_time - market_open
            close_delta = market_close - utc_time
            # nyt_time = utc_time.to('America/New_York')

            clock_list.append(open_delta.total_seconds())

            if open_delta.total_seconds() >= 0 and close_delta.total_seconds() >= 0:
                market_hours_list.append(True)
            else:
                market_hours_list.append(False)

            if i == time_data.shape[0] // 2:
                date_list.append(utc_time.date())

            # print(clock_list)
        clocktime_list.append(np.array(clock_list))
        tradeable_list.append(np.array(market_hours_list, dtype=np.bool))

        open_data = datafile['SPY']['open'][...]
        high_data = datafile['SPY']['high'][...]
        low_data = datafile['SPY']['low'][...]
        candle_average_list.append(Analytics.candle_avg(open=open_data, high=high_data, low=low_data))

        datafile.close()

    print('number of \'SPY\' days found: {}'.format(len(clocktime_list)))

    print(str(date_list[0]))

    fig, axs = plt.subplots(nrows=len(clocktime_list), ncols=1, figsize=(10, 20), sharex=True)

    for i, date, clocktime, candle_average in zip(np.arange(len(clocktime_list)), date_list, clocktime_list,
                                                  candle_average_list):
        axs[i].plot(clocktime, candle_average, label=str(date))
        axs[i].legend()
        # axs[i].set_xlim(left=(9 * 3600 + 30 * 60), right=(16 * 3600))
        axs[i].set_xlim(left=(-30*60), right=(6 * 3600 + 30 * 60))
        #axs[i].set_xticks(np.arange(8)*3600)
        #axs[i].set_xticklabels(map(str, np.arange(8)+9))

    #plt.figure(figsize=(10, 10))
    #for i, clocktime, candle_average in zip(np.arange(len(clocktime_list)), clocktime_list, candle_average_list):
    #    plt.plot(clocktime, candle_average / np.max(np.abs(candle_average)))


    return

if __name__ == '__main__':
    DataStack(filedirectory='../StockData/')
