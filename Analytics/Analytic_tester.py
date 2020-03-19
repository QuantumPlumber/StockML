import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import Analytics

import importlib

importlib.reload(Analytics)

'''File Handling'''
filedirectory = '../StockData/'
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

time = datafile[group_choice]['datetime'][...]
data_open = datafile[group_choice]['open'][...]
data_high = datafile[group_choice]['high'][...]
data_low = datafile[group_choice]['low'][...]
data = Analytics.candle_avg(open=data_open, high=data_high, low=data_low)
candle_low_bollinger, candle_high_bollinger = Analytics.candle_bollinger_bands(open=data_open,
                                                                               high=data_high,
                                                                               low=data_low,
                                                                               average=data,
                                                                               period=30)

sma = Analytics.moving_average(data=data, period=20)
sma_low_bollinger, sma_high_bollinger = Analytics.bollinger_bands(data=data, average=sma)

ema = Analytics.exp_moving_average(data=data, alpha=.1, period=30)
ema_low_bollinger, ema_high_bollinger = Analytics.bollinger_bands(data=data, average=ema)

focus_top = 3000
focus_bot = 35000
plt.figure(figsize=(20, 10))
plt.suptitle(group_choice + ' ' + 'open sma')
plt.plot(data[focus_top:focus_bot])
plt.plot(sma[focus_top:focus_bot])
plt.plot(sma_low_bollinger[focus_top:focus_bot])
plt.plot(sma_high_bollinger[focus_top:focus_bot])
plt.plot(candle_low_bollinger[focus_top:focus_bot])
plt.plot(candle_high_bollinger[focus_top:focus_bot])

plt.figure(figsize=(20, 10))
plt.suptitle(group_choice + ' ' + 'open ema')
plt.plot(data[focus_top:focus_bot])
plt.plot(ema[focus_top:focus_bot])
plt.plot(ema_low_bollinger[focus_top:focus_bot])
plt.plot(ema_high_bollinger[focus_top:focus_bot])

datafile.close()
