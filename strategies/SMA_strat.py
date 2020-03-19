import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import Analytics

import importlib

importlib.reload(Analytics)


def SMA_strat(sma, bollinger_down, bollinger_up, candle, candle_down, candle_up):
    crossover_threshold = .2
    stop_loss_fraction = .2

    call_buy_locs = []
    call_buy_price = []

    call_sell_locs = []
    call_sell_price = []

    put_buy_locs = []
    put_buy_price = []

    put_sell_locs = []
    put_sell_price = []

    open_position = False
    position_price = 0
    stop_loss = 0
    for i in np.arange(sma.shape[0]):
        crossover_up = candle_down[i] - crossover_threshold * (candle[i] - candle_down[i])
        if sma[i] < crossover_up:  # handle call options
            if not open_position:
                call_buy_locs.append(i)
                position_price = candle_up[i]
                position_candle = sma[i]
                # max_increase = candle_up[i]-candle_down[i] #sell if the next candle is not
                call_buy_price.append(position_price)
                open_position = True

            elif (sma[i] - position_candle) < -stop_loss_fraction*(bollinger_up[i]-bollinger_down[i]):  # sell if the average turns around
                call_sell_locs.append(i)
                call_sell_price.append(candle_down[i])
                open_position = False

            if sma[i] > position_candle:
                position_candle = sma[i]

        crossover_down = candle_up[i] + crossover_threshold * (candle_up[i] - candle[i])
        if sma[i] > crossover_down:  # handle put options
            if not open_position:
                put_buy_locs.append(i)
                position_price = candle_down[i]
                position_candle = sma[i]
                # max_increase = candle_up[i]-candle_down[i] #sell if the next candle is not
                put_buy_price.append(position_price)
                open_position = True

            elif (sma[i] - position_candle) < -stop_loss_fraction*(bollinger_up[i]-bollinger_down[i]):  # sell if the average turns around
                put_sell_locs.append(i)
                put_sell_price.append(candle_down[i])
                open_position = False

            if candle[i] < position_candle:
                position_candle = sma[i]

    return np.array(call_buy_locs), np.array(call_buy_price), \
           np.array(call_sell_locs), np.array(call_sell_price), \
           np.array(put_buy_locs), np.array(put_buy_price), \
           np.array(put_sell_locs), np.array(put_sell_price)


if __name__ == "__main__":

    '''File Handling'''
    filedirectory = '../StockData/'
    filename = 'S&P_500_2020-03-16'
    filepath = filedirectory + filename
    if os.path.exists(filepath):
        datafile = h5py.File(filepath)
    else:
        print('Data file does not exist!')

    group_choice = np.random.choice(list(datafile.keys()))

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

    sma = Analytics.moving_average(data=data, period=20)
    sma_low_bollinger, sma_high_bollinger = Analytics.bollinger_bands(data=data, average=sma)

    call_buy_locs, call_buy_price, \
    call_sell_locs, call_sell_price, \
    put_buy_locs, put_buy_price, \
    put_sell_locs, put_sell_price = SMA_strat(sma=sma,
                                              bollinger_down=sma_low_bollinger,
                                              bollinger_up=sma_high_bollinger,
                                              candle=data,
                                              candle_down=candle_low_bollinger,
                                              candle_up=candle_high_bollinger)


    cut = np.min((call_buy_price.shape[0],call_sell_price.shape[0]))
    call_profits = (call_buy_price[:cut] - call_sell_price[:cut])
    cut = np.min((put_buy_price.shape[0], put_sell_price.shape[0]))
    sell_profits = (-put_buy_price[:cut] + put_sell_price[:cut])


    plt.figure(figsize=(20,10))
    plt.plot(call_profits)
    plt.plot(sell_profits)

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
    call_cut = call_buy_locs[call_buy_locs > focus_top]
    plt.plot(call_cut-focus_top, sma[call_cut], '.', color='k')
    call_cut = call_sell_locs[call_sell_locs > focus_top]
    plt.plot(call_cut - focus_top, sma[call_cut], '.', color='b')