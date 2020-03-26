import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import time as tm
import datetime


def market_hours(time):
    tradeable = np.zeros_like(time)

    for i in np.arange(tradeable.shape[0]):
        gm_time = tm.gmtime(time[i] * 1e-3)
        if (gm_time[3] - 4 > 9) and (gm_time[3] - 4 < 16):
            tradeable[i] = True
        else:
            tradeable[i] = False

    return tradeable


'''File Handling'''
filedirectory = '../StockData/'
filename = 'S&P_500_2020-03-16'
filename = 'S&P_500_2020-03-25'
filepath = filedirectory + filename
if os.path.exists(filepath):
    datafile = h5py.File(filepath)
else:
    print('Data file does not exist!')

print('number of tickers in file: {}'.format(len(datafile.keys())))
for group_key in datafile.keys():
    group = datafile[group_key]
    print(group_key)

    for data_key in group.keys():
        dataset = group[data_key]
        print(dataset.name)
        print(dataset.shape)

    break

group_choice = np.random.choice(list(datafile.keys()))
group_choice = 'SPY'
dataset_choice = np.random.choice(list(datafile[group_choice].keys()))

time = datafile[group_choice]['datetime'][...]
data = datafile[group_choice][dataset_choice][...]
market_open = datafile[group_choice]['market_hours']
#market_open = market_hours(time)

gm_time = np.zeros_like(time)
date_list = []
for i, t in enumerate(time):
    gm_time = tm.gmtime(t * 1e-3)
    date_list.append(datetime.datetime(year=gm_time[0],
                                       month=gm_time[1],
                                       day=gm_time[2],
                                       hour=gm_time[3],
                                       minute=gm_time[4],
                                       second=gm_time[5]))
numpy_datetimes = np.array(date_list, dtype='datetime64')

fig, axs = plt.subplots(nrows=2, sharex=True, figsize=(10, 5))
plt.suptitle(group_choice + ' ' + dataset_choice)
axs[0].plot(numpy_datetimes, data, '.')
axs[1].plot(numpy_datetimes, market_open)
plt.xticks(rotation=70)
