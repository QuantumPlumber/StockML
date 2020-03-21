import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import Analytics
import PutSlinger
import time as tm

import importlib

importlib.reload(Analytics)
importlib.reload(PutSlinger)


def slinger(time,
            sma,
            sma_d,
            candle,
            candle_high,
            candle_low,
            stop_loss,
            profit
            ):
    results_list = PutSlinger.SMA_strat(time=time,
                                        sma=sma,
                                        sma_d=sma_d,
                                        candle=candle,
                                        candle_high=candle_high,
                                        candle_low=candle_low,
                                        stop_loss=stop_loss,
                                        profit=profit)

    put_buy_locs = results_list[0]
    put_buy_price = results_list[1]
    put_buy_option_price = results_list[2]

    put_sell_locs = results_list[3]
    put_sell_price = results_list[4]
    put_sell_option_price = results_list[5]

    put_profits = (put_buy_option_price - put_sell_option_price)

    put_percent = (put_buy_option_price - put_sell_option_price) / put_buy_option_price
    put_percent_avg = np.sum(put_percent) / put_percent.shape[0]

    return put_percent_avg


if __name__ == "__main__":

    '''File Handling'''
    filedirectory = '../StockData/'
    filename = 'S&P_500_2020-03-16'
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
    datafile.close()

    data = Analytics.candle_avg(open=data_open, high=data_high, low=data_low)
    candle_low_bollinger, candle_high_bollinger = Analytics.candle_bollinger_bands(open=data_open,
                                                                                   high=data_high,
                                                                                   low=data_low,
                                                                                   average=data,
                                                                                   period=30)
    period = 60
    sma = Analytics.moving_average(data=data, period=period)
    # sma = Analytics.exp_moving_average(data=data, alpha=.1, period=30)
    sma_low_bollinger, sma_high_bollinger = Analytics.bollinger_bands(data=data, average=sma)
    sma_d = Analytics.derivative(data, period=period)
    #sma_d = Analytics.second_derivative(data, period=period)

    stop_loss = np.linspace(.5, .95, 10)
    profit = np.linspace(1.2, 2., 10)
    slsl, prpr = np.meshgrid(stop_loss, profit)

    percent_avg_profit = np.zeros_like(slsl)
    for i in np.arange(stop_loss.shape[0]):
        for j in np.arange(profit.shape[0]):
            #print('{},{}'.format(i, j))
            percent_avg_profit[i, j] = slinger(time=time,
                                               sma=sma,
                                               sma_d=sma_d,
                                               candle=data,
                                               candle_high=candle_low_bollinger,
                                               candle_low=candle_high_bollinger,
                                               stop_loss=slsl[i, j],
                                               profit=prpr[i, j])

    plt.pcolormesh(stop_loss, profit, percent_avg_profit)
    plt.colorbar()
