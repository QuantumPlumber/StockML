import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import Analytics
import time as tm

import importlib

importlib.reload(Analytics)


def instrument_price(sell_price, buy_price, base_price=6, delta=.5):
    delta_price = (sell_price - buy_price) * delta
    return (delta_price / buy_price)


def SMA_strat(time, sma, sma_d, sma_dd, bollinger_down, bollinger_up, candle, candle_down, candle_up):
    crossover_threshold = .0
    stop_loss_fraction = .02

    buy_call_threshold = 10
    sell_call_thershold = -.005
    buy_put_threshold = -10
    sell_put_thershold = .005

    call_thresholds = {'d_buy': 10, 'dd_buy': 0.05, 'd_sell': 10, 'dd_sell': -0.02}
    put_thresholds = {'d_buy': 10, 'dd_buy': -0.03, 'd_sell': 10, 'dd_sell': 0.02}

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
    open_put_position = False
    start_offset = 20
    for i in np.arange(sma.shape[0])[start_offset:]:
        gm_time = tm.gmtime(time[i] * 1e-3)
        if (gm_time[3] - 4 > 9) and (gm_time[3] - 4 < 16):

            threshold = np.absolute(sma_d[i]/sma_dd[i])

            if threshold < call_thresholds['d_buy'] and sma_d[i] < 0 and sma_dd[i] > 0 and not open_call_position:  # open call options
                call_buy_locs.append(i)
                call_buy_price.append(candle[i])
                open_call_position = True

            if threshold < call_thresholds['d_sell'] and sma_d[i] > 0 and sma_dd[i] < 0 and open_call_position:  # close call options if the sma falls below threshold
                call_sell_locs.append(i)
                call_sell_price.append(candle[i])
                open_call_position = False

            if threshold < put_thresholds['d_buy'] and sma_d[i] > 0 and sma_dd[i] < 0 and not open_put_position:  # open put options
                put_buy_locs.append(i)
                put_buy_price.append(candle[i])
                open_put_position = True

            if threshold < put_thresholds['d_sell'] and sma_d[i] < 0 and sma_dd[i] > 0 and open_put_position:  # close put options
                put_sell_locs.append(i)
                put_sell_price.append(candle[i])
                open_put_position = False

        if (gm_time[3] - 4 > 15 and gm_time[4] > 58) and open_call_position:
            call_sell_locs.append(i)
            call_sell_price.append(candle[i])
            open_call_position = False

        if (gm_time[3] - 4 > 15 and gm_time[4] > 58) and open_put_position:
            put_sell_locs.append(i)
            put_sell_price.append(candle[i])
            open_put_position = False

    return [np.array(call_buy_locs), np.array(call_buy_price),
            np.array(call_sell_locs), np.array(call_sell_price),
            np.array(put_buy_locs), np.array(put_buy_price),
            np.array(put_sell_locs), np.array(put_sell_price),
            np.array(local_minimums), np.array(local_minimums_loc),
            np.array(local_maximums), np.array(local_maximums_loc)]


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

    period = 30
    data = Analytics.candle_avg(open=data_open, high=data_high, low=data_low)
    candle_low_bollinger, candle_high_bollinger = Analytics.candle_bollinger_bands(open=data_open,
                                                                                   high=data_high,
                                                                                   low=data_low,
                                                                                   average=data,
                                                                                   period=period)

    sma = Analytics.moving_average(data=data, period=period)
    sma_d = Analytics.derivative(data=sma, period=period)
    sma_dd = Analytics.second_derivative(data=sma, period=period)
    # sma = Analytics.exp_moving_average(data=data, alpha=.1, period=30)
    sma_low_bollinger, sma_high_bollinger = Analytics.bollinger_bands(data=data, average=sma)

    results_list = SMA_strat(time=time,
                             sma=sma,
                             sma_d=sma_d,
                             sma_dd=sma_dd,
                             bollinger_down=sma_low_bollinger,
                             bollinger_up=sma_high_bollinger,
                             candle=data,
                             candle_down=candle_low_bollinger,
                             candle_up=candle_high_bollinger)
    call_buy_locs = results_list[0]
    call_buy_price = results_list[1]
    call_sell_locs = results_list[2]
    call_sell_price = results_list[3]
    put_buy_locs = results_list[4]
    put_buy_price = results_list[5]
    put_sell_locs = results_list[6]
    put_sell_price = results_list[7]
    local_minimums = results_list[8]
    local_minimums_loc = results_list[9]
    local_maximums = results_list[10]
    local_maximums_loc = results_list[11]

    plt.figure(figsize=(20, 10))
    plt.suptitle('second derivative SMA movement')
    # plt.hist((sma[:-1] - sma[1:]) / (sma_high_bollinger[1:] - sma_low_bollinger[1:]), bins=100)
    plt.hist(np.absolute(sma_d/sma_dd), bins=100)

    plt.figure(figsize=(20, 10))
    plt.suptitle('second derivative SMA movement')
    # plt.hist((sma[:-1] - sma[1:]) / (sma_high_bollinger[1:] - sma_low_bollinger[1:]), bins=100)
    plt.plot(sma_d)
    plt.plot(sma_dd)

    plt.figure(figsize=(20, 10))
    plt.suptitle('second derivative SMA movement')
    # plt.hist((sma[:-1] - sma[1:]) / (sma_high_bollinger[1:] - sma_low_bollinger[1:]), bins=100)
    plt.plot(sma_d/sma_dd)
    plt.ylim((-30,30))

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

    cut = np.min((call_buy_price.shape[0], call_sell_price.shape[0]))
    print('number of call purchases: {}'.format(cut))
    call_profits = (call_sell_price[:cut] - call_buy_price[:cut])
    print('call_profits: {}'.format(np.sum(call_profits)))
    call_percent = instrument_price(call_sell_price[:cut], call_buy_price[:cut])
    print('call_percent: {}'.format(np.sum(call_percent)))

    cut = np.min((put_buy_price.shape[0], put_sell_price.shape[0]))
    print('number of put purchases: {}'.format(cut))
    put_profits = (put_buy_price[:cut] - put_sell_price[:cut])
    print('put_profits: {}'.format(np.sum(put_profits)))
    put_percent = -instrument_price(put_sell_price[:cut], put_buy_price[:cut])
    print('put_percent: {}'.format(np.sum(put_percent)))

    plt.figure(figsize=(20, 10))
    plt.hist(call_profits, bins=100)
    plt.hist(put_profits, bins=100)

    plt.figure(figsize=(20, 10))
    plt.plot(call_profits)
    plt.plot(put_profits)




    focus_top = time.shape[0] - 60*8
    focus_bot = time.shape[0]+1
    plt.figure(figsize=(20, 10))
    plt.suptitle(group_choice + ' ' + 'open sma' + 'Calls')
    plt.plot(time[focus_top:focus_bot], data[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma_low_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma_high_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], candle_low_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], candle_high_bollinger[focus_top:focus_bot])
    call_cut = call_buy_locs[call_buy_locs > focus_top]
    plt.plot(time[call_cut], sma[call_cut], '>', color='k')
    call_cut = call_sell_locs[call_sell_locs > focus_top]
    plt.plot(time[call_cut], sma[call_cut], '<', color='b')

    plt.figure(figsize=(20, 10))
    plt.suptitle(group_choice + ' ' + 'open sma' + 'Puts')
    plt.plot(time[focus_top:focus_bot], data[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma_low_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], sma_high_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], candle_low_bollinger[focus_top:focus_bot])
    plt.plot(time[focus_top:focus_bot], candle_high_bollinger[focus_top:focus_bot])

    put_cut = put_buy_locs[put_buy_locs > focus_top]
    plt.plot(time[put_cut], sma[put_cut], '>', color='r')
    # plt.plot(put_cut - focus_top, sma[put_cut], '>', color='r')
    put_cut = put_sell_locs[put_sell_locs > focus_top]
    plt.plot(time[put_cut], sma[put_cut], '<', color='g')
    # plt.plot(put_cut - focus_top, sma[put_cut], '<', color='g')

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
