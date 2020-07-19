import script_context

import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
from Stonks.Analytics import Analytics
import time as tm
import arrow
import importlib
from Stonks.Positions import position_class

importlib.reload(Analytics)
importlib.reload(position_class)


def instrument_price(sell_price, buy_price, base_price=6, delta=.5):
    delta_price = -(sell_price - buy_price) * delta + base_price
    return delta_price


def Bollinger_strat(time,
                    sma, sma_short,
                    bollinger_up, bollinger_down,
                    sma_d,
                    candle, candle_high, candle_low,
                    parameters):
    print(parameters)

    blocked = False

    initial_capital = 1.
    used_capital = 0
    working_capital = initial_capital
    min_trade_capital = .10

    put_buy_locs = []
    put_buy_price = []
    put_buy_option_price = []
    put_strike_price = []

    put_sell_locs = []
    put_sell_price = []
    put_sell_option_price = []

    position_value = []

    positions_list = []

    start_of_trading_minute = 9 * 60 + 30
    end_of_trading_minute = 16 * 60

    open_put_position = False
    put_price = 0
    max_put_price = 0
    buy_armed = False
    buy_trigger = False
    sell_armed = False
    sell_trigger = False
    for i in np.arange(1, sma.shape[0]):
        trade_time = arrow.get(time[i] * 1e-3).to('America/New_York')
        current_minute = trade_time.hour * 60 + trade_time.minute  # in minutes from open
        time_from_open = current_minute - start_of_trading_minute
        #print(time_to_expiry)

        working_capital = initial_capital * (current_minute - start_of_trading_minute) / (
                end_of_trading_minute - start_of_trading_minute)

        trade_capital = working_capital - used_capital

        if trade_capital < min_trade_capital:
            trade_capital = min_trade_capital

        if start_of_trading_minute < current_minute < end_of_trading_minute:
            # current_time = ((gm_time[3] - 4) * 60 + gm_time[4]) - (9 * 60)  # in minutes from open

            # print(used_capital)

            ############### Toggle buy ###########################

            threshold = 2 * (sma_short[i-1] - sma[i-1]) / np.absolute(bollinger_up[i-1] - bollinger_down[i-1]) * parameters[
                'flip']

            if threshold > parameters['Bollinger_top']:
                buy_armed = True

            buy_trigger = False
            if buy_armed and threshold <= parameters['Bollinger_top']:
                # print(threshold)
                buy_trigger = True

            if threshold < parameters['Bollinger_top']:
                buy_armed = False

            ############### Toggle Sell ###########################

            if threshold < parameters['Bollinger_bot']:
                sell_armed = True

            sell_trigger = False
            if sell_armed and threshold >= parameters['Bollinger_bot']:
                sell_trigger = True

            if threshold > parameters['Bollinger_bot']:
                sell_armed = False

            ############### implement buy & sell ###########################

            if buy_trigger and not open_put_position:  # open put options

                # strike_price = (candle[i] + bollinger_down[i]) / 2.

                strike_delta = 2 * (candle[i] - bollinger_down[i])
                if strike_delta >= 6:
                    strike_delta = 6

                #strike_price = candle[i] - strike_delta * parameters['flip']
                strike_price = (candle[i]) // 1

                #print('trade_capital: {}'.format(trade_capital))
                new_put = position_class.position(strike_price=strike_price,
                                                  volatility=1.,
                                                  # volatility=parameters['VIX'],
                                                  t=time_from_open,
                                                  stock_price=candle[i],
                                                  expiration=60 * (6) + 30,
                                                  stop_loss=parameters['stop_loss'],
                                                  stop_profit=parameters['profit'],
                                                  option_type=parameters['option_type'],
                                                  capital=trade_capital)

                used_capital += trade_capital
                #print('used_capital: {}'.format(used_capital))

                positions_list.append(new_put)
                put_buy_locs.append(i)
                open_put_position = True

            if open_put_position:
                positions_list[-1].compute_price(t=time_from_open, stock_price=candle[i])
                positions_list[-1].compute_value()
                # print(put_price)
                # print(put_price)
                '''
                if (put_price < put_thresholds['stop_loss'] * max_put_price
                    and put_price <= put_buy_option_price[-1]) \
                        or \
                        (put_price > put_thresholds['profit'] * put_buy_option_price[-1]
                         or sell_trigger):  # close put options
                '''
                '''
                if (put_price < parameters['stop_loss'] * max_put_price
                    and put_price <= put_buy_option_price[-1]) \
                        or \
                        (put_price > parameters['profit'] * max_put_price
                         and put_price > put_buy_option_price[-1]
                         and sma_d[i] >= 0.0):  # close put options
                    # print('#############################################')
                    put_sell_locs.append(i)
                    put_sell_price.append(candle[i])
                    put_sell_option_price.append(put_price)
                    # print(put_price)
                    open_put_position = False
                '''

                if positions_list[-1].check_stop_loss() or positions_list[-1].check_stop_profit() or (
                        sell_trigger):  # close put options
                    # print('#############################################')
                    positions_list[-1].close_position(candle[i])
                    put_sell_locs.append(i)
                    # print(put_price)
                    open_put_position = False
                    # print('closed')
                    # print(positions_list[-1].quantity_at_buy_or_add)

        if (current_minute >= end_of_trading_minute) and open_put_position:
            put_sell_locs.append(i)
            positions_list[-1].close_position(candle[i])
            open_put_position = False
            #print('closed')
            #print(positions_list[-1].quantity_at_buy_or_add)

    print('number of positions: {}'.format(len(positions_list)))

    for pos in positions_list:
        if pos.position_closed == False:
            print('position not closed.')
        put_buy_price.append(pos.stock_price_at_open)
        put_buy_option_price.append(pos.value_history[0])
        put_sell_price.append(pos.stock_price_at_close)
        put_sell_option_price.append(pos.value_history[-1])
        put_strike_price.append(pos.strike_price)
        position_value.append(pos.value_history[-1])

    position_value.append(initial_capital - used_capital)

    return [np.array(put_buy_locs),
            np.array(put_buy_price),
            np.array(put_buy_option_price),
            np.array(put_sell_locs),
            np.array(put_sell_price),
            np.array(put_sell_option_price),
            np.array(put_strike_price),
            np.array(position_value)]


if __name__ == "__main__":

    '''File Handling'''
    filedirectory = 'D:/StockData/'
    filename = 'S&P_500_2020-05-08'
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

    tradeable = Analytics.market_hours(t=time)
    print(np.sum(tradeable))
    candle = Analytics.candle_avg(open=data_open, high=data_high, low=data_low)
    candle_low_bollinger, candle_high_bollinger = Analytics.candle_bollinger_bands(open=data_open,
                                                                                   high=data_high,
                                                                                   low=data_low,
                                                                                   average=candle,
                                                                                   period=30)
    period = 30
    sma = Analytics.moving_average(data=candle, period=period)
    sma_short = Analytics.moving_average(data=candle, period=period // 3)
    sma_low_bollinger, sma_high_bollinger = Analytics.bollinger_bands(data=sma_short, average=sma)
    sma_d = Analytics.derivative(sma, period=period // 6)
    # sma_d = Analytics.moving_average(sma_d, period=period // 6)
    sma_dd = Analytics.second_derivative(sma, period=period)

    parameter = {'Bollinger_top': .0,
                  'Bollinger_bot': -2.0,
                  'stop_loss': .8,
                  'profit': .8,
                  'flip': 1,
                  'option_type': position_class.OptionType.CALL}

    results_list = Bollinger_strat(time=time,
                                   sma=sma,
                                   sma_short=sma_short,
                                   bollinger_up=sma_high_bollinger,
                                   bollinger_down=sma_low_bollinger,
                                   sma_d=sma_d,
                                   candle=candle,
                                   candle_high=candle_high_bollinger,
                                   candle_low=candle_low_bollinger,
                                   parameters=parameter)

    put_buy_locs = results_list[0]
    put_buy_price = results_list[1]
    put_buy_option_price = results_list[2]

    put_sell_locs = results_list[3]
    put_sell_price = results_list[4]
    put_sell_option_price = results_list[5]

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

    print('put buy option price: {}'.format(put_buy_option_price))
    print('put sell option price: {}'.format(put_sell_option_price))

    put_profits = (put_sell_option_price - put_buy_option_price)
    print('put profits: {}'.format(put_profits))
    print('total put profits: {}'.format(np.sum(put_profits)))

    put_percent = (put_sell_option_price - put_buy_option_price) / put_buy_option_price
    print('put percents: {}'.format(put_percent))
    print('total put percent: {}'.format(np.sum(put_percent) / put_percent.shape[0]))

    focus_top = 0
    focus_bot = time.shape[0] + 1

    candle_rescaled = candle - np.sum(candle) / sma.shape[0]
    candle_rescaled = candle_rescaled / np.abs(candle_rescaled).max()
    sma_rescaled = sma - np.sum(sma) / sma.shape[0]
    sma_rescaled = sma_rescaled / np.abs(sma_rescaled).max()
    Bollinger_oscillator = 2 * (sma_short - sma) / np.absolute(sma_high_bollinger - sma_low_bollinger)

    minute_time = Analytics.minute_time(time)
    print('put buy locs: {}'.format(minute_time[put_buy_locs]))
    print('put sell locs: {}'.format(minute_time[put_sell_locs]))
    #print(minute_time)

    #################################################################################
    # plt.figure(figsize=(20, 10))
    # plt.suptitle('profitable trades')
    # ax[0].plot(time[tradeable], data_volume[tradeable], '.')

    fig, ax = plt.subplots(nrows=1, ncols=2, sharex=False, figsize=(20, 8))

    ax_twin = ax[0].twinx()
    ax_twin.plot(minute_time[tradeable], Bollinger_oscillator[tradeable])
    ax_twin.plot(minute_time[tradeable], np.ones_like(minute_time[tradeable]) * parameter['Bollinger_top'], color='k')
    ax_twin.plot(minute_time[tradeable], np.ones_like(minute_time[tradeable]) * parameter['Bollinger_bot'], color='k')

    ax[0].plot(minute_time[tradeable], candle[tradeable], '.')
    ax[0].plot(minute_time[tradeable], sma[tradeable])
    ax[0].plot(minute_time[tradeable], sma_low_bollinger[tradeable])
    ax[0].plot(minute_time[tradeable], sma_high_bollinger[tradeable])
    ax[0].plot(minute_time[tradeable], candle_low_bollinger[tradeable])
    ax[0].plot(minute_time[tradeable], candle_high_bollinger[tradeable])

    profit_put_buy_locs = put_buy_locs[put_profits >= 0]
    put_cut = profit_put_buy_locs[profit_put_buy_locs > focus_top]
    ax[0].plot(minute_time[put_cut], candle[put_cut], '>', color='k')

    profit_put_sell_locs = put_sell_locs[put_profits >= 0]
    put_cut = profit_put_sell_locs[profit_put_sell_locs > focus_top]
    ax[0].plot(minute_time[put_cut], candle[put_cut], '<', color='k')

    #################################################################################
    # plt.figure(figsize=(20, 10))
    # plt.suptitle('loss trades')
    # ax[1].plot(minute_time, data_volume, '.')

    ax_twin = ax[1].twinx()
    ax_twin.plot(minute_time[tradeable], Bollinger_oscillator[tradeable])
    ax_twin.plot(minute_time[tradeable], np.ones_like(minute_time[tradeable]) * parameter['Bollinger_top'], color='k')
    ax_twin.plot(minute_time[tradeable], np.ones_like(minute_time[tradeable]) * parameter['Bollinger_bot'], color='k')

    ax[1].plot(minute_time[tradeable], candle[tradeable], '.')
    ax[1].plot(minute_time[tradeable], sma[tradeable])
    ax[1].plot(minute_time[tradeable], sma_low_bollinger[tradeable])
    ax[1].plot(minute_time[tradeable], sma_high_bollinger[tradeable])
    ax[1].plot(minute_time[tradeable], candle_low_bollinger[tradeable])
    ax[1].plot(minute_time[tradeable], candle_high_bollinger[tradeable])

    loss_put_buy_locs = put_buy_locs[put_profits < 0]
    put_cut = loss_put_buy_locs[loss_put_buy_locs > focus_top]
    ax[1].plot(minute_time[put_cut], candle[put_cut], '>', color='k')

    loss_put_sell_locs = put_sell_locs[put_profits < 0]
    put_cut = loss_put_sell_locs[loss_put_sell_locs > focus_top]
    ax[1].plot(minute_time[put_cut], candle[put_cut], '<', color='k')

