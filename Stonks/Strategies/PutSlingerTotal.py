import script_context

import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
from Stonks.Analytics import Analytics
import time as tm

import importlib

importlib.reload(Analytics)


def instrument_price(sell_price, buy_price, base_price=6, delta=.5):
    delta_price = -(buy_price - sell_price) * delta + base_price
    return delta_price


def SMA_strat(time, sma, sma_d, sma_dd, candle, candle_high, candle_low, stop_loss=.8, profit=1.2):
    put_thresholds = {'buy': 5, 'stop_loss': stop_loss, 'profit': profit}

    open_position_list = np.array([], dtype=np.bool)
    put_buy_locs = np.array([], dtype=np.int)
    put_buy_price = np.array([])
    put_buy_option_price = np.array([])
    put_max_option_price = np.array([])

    put_sell_locs = np.array([], dtype=np.int)
    put_sell_price = np.array([])
    put_sell_option_price = np.array([])

    put_price = 0
    for i in np.arange(sma.shape[0]):
        gm_time = tm.gmtime(time[i] * 1e-3)
        if (gm_time[3] - 4 > 9) and (gm_time[3] - 4 < 16):

            rand = np.random.random(1)
            if rand > .5:
                delta = True
            else:
                delta = True
            # if sma_d[i] < 0.0 and sma_d[i] > -0.03 and delta and not open_put_position:  # open put options
            if sma_d[i] < 0.0 and sma_dd[i] < 0.0 and delta:  # open put options
                open_position_list = np.append(open_position_list, True)
                put_buy_locs = np.append(put_buy_locs, i)
                put_price = instrument_price(candle[i], candle[i], base_price=3, delta=.5)
                # print(put_price)
                put_buy_option_price = np.append(put_buy_option_price, put_price)
                put_max_option_price = np.append(put_max_option_price, put_price)
                put_buy_price = np.append(put_buy_price, candle[i])

                put_sell_locs = np.append(put_sell_locs, int(0))  # placeholder values to be replaced later
                put_sell_price = np.append(put_sell_price, np.nan)
                put_sell_option_price = np.append(put_sell_option_price, np.nan)

            if open_position_list.shape[0] > 0:
                # print(open_position_list.dtype)
                for open_index in np.arange(put_buy_option_price.shape[0])[open_position_list]:
                    put_price = instrument_price(candle[i], put_buy_price[open_index], base_price=3, delta=.5)

                    if put_price >= put_max_option_price[open_index]:
                        put_max_option_price[open_index] = put_price
                    # print(put_price)
                    if put_price < put_thresholds['stop_loss'] * put_max_option_price[open_index] or \
                            put_price > put_thresholds['profit'] * put_buy_option_price[
                        open_index]:  # close put options
                        # print('#############################################')
                        put_sell_locs[open_index] = i
                        put_sell_price[open_index] = candle[i]
                        put_sell_option_price[open_index] = put_price
                        open_position_list[open_index] = False

        if gm_time[3] - 4 > 15 and gm_time[4] > 58 and open_position_list.shape[0] > 0:
            for open_index in np.arange(put_buy_option_price.shape[0])[open_position_list]:
                put_sell_locs[open_index] = int(i)
                put_sell_price[open_index] = candle[i]
                put_sell_option_price[open_index] = put_price
                open_position_list[open_index] = False

    return [open_position_list, put_buy_locs, put_buy_price, put_buy_option_price, put_sell_locs, put_sell_price,
            put_sell_option_price]


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
    sma_dd = Analytics.derivative(data, period=period // 4)

    results_list = SMA_strat(time=time,
                             sma=sma,
                             sma_d=sma_d,
                             sma_dd=sma_dd,
                             candle=data,
                             candle_high=candle_low_bollinger,
                             candle_low=candle_high_bollinger,
                             stop_loss=.5,
                             profit=30.0)

    open_position_list = results_list[0]
    put_buy_locs = results_list[1]
    put_buy_price = results_list[2]
    put_buy_option_price = results_list[3]

    put_sell_locs = results_list[4]
    put_sell_price = results_list[5]
    put_sell_option_price = results_list[6]

    '''
    plt.figure(figsize=(20, 10))
    plt.suptitle('second derivative SMA movement')
    # plt.hist((sma[:-1] - sma[1:]) / (sma_high_bollinger[1:] - sma_low_bollinger[1:]), bins=100)
    plt.hist((sma[0:-1:10][:-2] - 2 * sma[10:-1:10][:-1] + sma[20:-1:10]) / 2., bins=100)

    plt.figure(figsize=(20, 10))
    plt.suptitle('derivative SMA movement')
    plt.hist((sma[:-1] - sma[1:]) / (sma_high_bollinger[1:] - sma_low_bollinger[1:]), bins=100)

    plt.figure(figsize=(20, 10))
    plt.suptitle('Bollinger Band normalized SMA movement')
    plt.plot((sma[:-1] - sma[1:]) / (sma_high_bollinger[1:] - sma_low_bollinger[1:]))
    '''

    print('number of put purchases: {}'.format(put_buy_option_price.shape[0]))
    put_profits = (put_buy_option_price - put_sell_option_price)
    print('put_profits: {}'.format(np.sum(put_profits)))
    put_percent = (put_buy_option_price - put_sell_option_price) / put_buy_option_price
    print('put_percent: {}'.format(np.sum(put_percent) / put_percent.shape[0]))

    plt.figure(figsize=(20, 10))
    plt.hist(put_profits, bins=100)

    plt.figure(figsize=(20, 10))
    plt.plot(put_profits)

    focus_top = time.shape[0] - 60 * 8
    focus_bot = time.shape[0] + 1
    focus_top = 2400
    focus_bot = 2900
    time = np.arange(time.shape[0])

    #################################################################################
    plt.figure(figsize=(20, 10))
    plt.suptitle('profitable trades')
    plt.plot(time[focus_top:focus_bot], data[focus_top:focus_bot], '.')
    plt.plot(time[focus_top:focus_bot], sma[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma_low_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma_high_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], candle_low_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], candle_high_bollinger[focus_top:focus_bot])

    profit_put_buy_locs = put_buy_locs[put_profits > 0]
    profit_put_buy_locs = profit_put_buy_locs[np.logical_and(profit_put_buy_locs > focus_top, profit_put_buy_locs < focus_bot)]
    put_cut = profit_put_buy_locs
    plt.plot(time[put_cut], data[put_cut], '>', color='r')
    # plt.plot(put_cut - focus_top, sma[put_cut], '>', color='r')
    sma_d_buy = sma_d[put_cut]

    profit_put_sell_locs = put_sell_locs[put_profits > 0]
    profit_put_sell_locs = profit_put_sell_locs[np.logical_and(profit_put_sell_locs > focus_top, profit_put_sell_locs < focus_bot)]
    put_cut = profit_put_sell_locs
    plt.plot(time[put_cut], data[put_cut], '<', color='g')
    # plt.plot(put_cut - focus_top, sma[put_cut], '<', color='g')
    plt.xlim((np.min(profit_put_buy_locs), np.max(profit_put_buy_locs)))
    plt.xlim((focus_top, focus_bot))

    plt.figure(figsize=(20, 10))
    plt.xlim((focus_top, focus_bot))
    plt.plot(time[profit_put_buy_locs], sma_d_buy, '.')

    #plt.figure(figsize=(20, 10))
    #plt.plot(time[put_cut], np.cumsum(put_profits[put_profits > 0]), '.')

    #################################################################################
    plt.figure(figsize=(20, 10))
    plt.suptitle('loss trades')
    plt.plot(time[focus_top:focus_bot], data[focus_top:focus_bot], '.')
    plt.plot(time[focus_top:focus_bot], sma[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma_low_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma_high_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], candle_low_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], candle_high_bollinger[focus_top:focus_bot])

    loss_put_buy_locs = put_buy_locs[put_profits < 0]
    loss_put_buy_locs = loss_put_buy_locs[np.logical_and(loss_put_buy_locs > focus_top, loss_put_buy_locs < focus_bot)]
    put_cut = loss_put_buy_locs
    plt.plot(time[put_cut], data[put_cut], '>', color='r')
    # plt.plot(put_cut - focus_top, sma[put_cut], '>', color='r')
    sma_d_buy = sma_d[put_cut]

    loss_put_sell_locs = put_sell_locs[put_profits < 0]
    loss_put_sell_locs = loss_put_sell_locs[np.logical_and(loss_put_sell_locs > focus_top, loss_put_sell_locs < focus_bot)]
    put_cut = loss_put_sell_locs
    plt.plot(time[put_cut], data[put_cut], '<', color='g')
    # plt.plot(put_cut - focus_top, sma[put_cut], '<', color='g')
    plt.xlim((focus_top, focus_bot))

    plt.figure(figsize=(20, 10))
    plt.xlim((focus_top, focus_bot))
    plt.plot(time[loss_put_buy_locs], sma_d_buy, '.')

    #plt.figure(figsize=(20, 10))
    #plt.plot(time[put_cut], np.cumsum(put_profits[put_profits < 0]), '.')

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
