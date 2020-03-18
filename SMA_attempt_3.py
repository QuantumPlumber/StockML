import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import Analytics

import importlib

importlib.reload(Analytics)


def SMA_strat(sma, bollinger_down, bollinger_up, candle, candle_down, candle_up):
    crossover_threshold = .02
    stop_loss_fraction = .02

    call_buy_locs = []
    call_buy_price = []

    call_sell_locs = []
    call_sell_price = []

    put_buy_locs = []
    put_buy_price = []

    put_sell_locs = []
    put_sell_price = []

    local_minimums = []
    local_minimums_loc = []
    local_maximums = []
    local_maximums_loc = []

    open_call_position = False
    max_call_price = 0
    open_put_position = False
    current_put_price = 0
    position_price = 0
    stop_loss = 0
    local_maximum = -1e5
    local_minimum = 1e5

    start_offset = 2
    look_back = start_offset - 1
    for i in np.arange(sma.shape[0])[start_offset:]:

        delta_up = (sma[i] - sma[i-1])/(bollinger_up[i]-bollinger_down[i])
        # print('delta_up: {}'.format(delta_up))
        crossover_up = crossover_threshold
        # print('crossover_up: {}'.format(crossover_up))
        delta_down = (sma[i] - sma[i-1])/(bollinger_up[i]-bollinger_down[i])
        # print('delta_down: {}'.format(delta_down))
        crossover_down = -crossover_threshold
        # print('crossover_down: {}'.format(crossover_down))

        if delta_up > crossover_up and not open_call_position:  # open call options
            call_buy_locs.append(i)
            call_buy_price.append(candle_up[i])
            open_call_position = True

        if delta_up < crossover_up and open_call_position:  # close call options if the sma falls below threshold
            call_sell_locs.append(i)
            call_sell_price.append(candle_down[i])
            open_call_position = False

        if delta_down < crossover_down and not open_put_position:  # open put options
            call_buy_locs.append(i)
            call_buy_price.append(candle_down[i])
            open_put_position = True

        if delta_down > -crossover_down and open_put_position:  # close put options
            call_sell_locs.append(i)
            call_sell_price.append(candle_up[i])
            open_put_position = False

    return np.array(call_buy_locs), np.array(call_buy_price), \
           np.array(call_sell_locs), np.array(call_sell_price), \
           np.array(put_buy_locs), np.array(put_buy_price), \
           np.array(put_sell_locs), np.array(put_sell_price), \
           np.array(local_minimums), np.array(local_minimums_loc), \
           np.array(local_maximums), np.array(local_maximums_loc)


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
    put_sell_locs, put_sell_price, \
    local_minimums, local_minimums_loc, \
    local_maximums, local_maximums_loc = SMA_strat(sma=sma,
                                                   bollinger_down=sma_low_bollinger,
                                                   bollinger_up=sma_high_bollinger,
                                                   candle=data,
                                                   candle_down=candle_low_bollinger,
                                                   candle_up=candle_high_bollinger)


    plt.figure(figsize=(20, 10))
    plt.suptitle('Bollinger Band normalized SMA movement')
    plt.hist((sma[:-1]-sma[1:])/(sma_high_bollinger[1:]-sma_low_bollinger[1:]), bins=100)

    plt.figure(figsize=(20, 10))
    plt.suptitle('Bollinger Band normalized SMA movement')
    plt.plot((sma[:-1]-sma[1:])/(sma_high_bollinger[1:]-sma_low_bollinger[1:]))


    cut = np.min((call_buy_price.shape[0], call_sell_price.shape[0]))
    call_profits = (call_buy_price[:cut] - call_sell_price[:cut])
    print('call_profits: {}'.format(np.sum(call_profits)))
    cut = np.min((put_buy_price.shape[0], put_sell_price.shape[0]))
    sell_profits = (-put_buy_price[:cut] + put_sell_price[:cut])
    print('sell_profits: {}'.format(np.sum(sell_profits)))

    plt.figure(figsize=(20, 10))
    plt.hist(call_profits, bins=100)
    plt.hist(sell_profits, bins=100)

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
    plt.plot(call_cut - focus_top, sma[call_cut], '>', color='k')
    call_cut = call_sell_locs[call_sell_locs > focus_top]
    plt.plot(call_cut - focus_top, sma[call_cut], '<', color='b')


    '''
    focus_top = 3000
    focus_bot = 35000
    plt.figure(figsize=(20, 10))
    plt.suptitle(group_choice + ' ' + 'open sma')
    plt.plot(sma[focus_top:focus_bot])
    plt.plot(sma_low_bollinger[focus_top:focus_bot])
    plt.plot(sma_high_bollinger[focus_top:focus_bot])

    peak_cut = local_minimums_loc[local_minimums_loc > focus_top]
    plt.plot(peak_cut - focus_top, sma[peak_cut], '.', color='k')

    #peak_cut = local_maximums_loc[local_maximums_loc > focus_top]
    #plt.plot(peak_cut - focus_top, sma[peak_cut], '.', color='b')
    '''