import script_context

import os
import h5py
import time
import matplotlib.pyplot as plt
import numpy as np
from Stonks.Analytics import Analytics
from Stonks.Strategies import PutSlingerBollinger
from Stonks.DataGrubbing import DailyGenerator
from Stonks.Positions import position_class

import importlib

importlib.reload(Analytics)
importlib.reload(PutSlingerBollinger)
importlib.reload(DailyGenerator)
importlib.reload(position_class)


def slinger(ax, datafile, ticker, parameters):
    time = datafile[ticker]['datetime'][...]
    data_open = datafile[ticker]['open'][...]
    data_high = datafile[ticker]['high'][...]
    data_low = datafile[ticker]['low'][...]
    data_volume = datafile[ticker]['volume'][...]
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
    day_volatility = Analytics.day_volatility(data=candle, tradeable=tradeable)
    print('day volatility: {}'.format(day_volatility))

    # find the best strategy of given strategies:

    performance_list = []
    # parameters['option_type'] = position_class.OptionType.PUT
    for parameter in parameters:
        parameter['VIX'] = day_volatility
        results_list = PutSlingerBollinger.Bollinger_strat(time=time,
                                                           sma=sma,
                                                           sma_short=sma_short,
                                                           bollinger_up=sma_high_bollinger,
                                                           bollinger_down=sma_low_bollinger,
                                                           sma_d=sma_d,
                                                           candle=candle,
                                                           candle_high=candle_high_bollinger,
                                                           candle_low=candle_low_bollinger,
                                                           parameters=parameter)

        put_buy_option_price = results_list[2]

        put_sell_option_price = results_list[5]

        put_percent = (put_sell_option_price - put_buy_option_price) / put_buy_option_price

        put_percent[put_percent > 5] = 5  # put an upper bound on the option returns.

        put_percent_avg = np.sum(put_percent) / put_percent.shape[0]

        performance_list.append(put_percent_avg)

    performance_array = np.array(performance_list)
    print('performance_array: {}'.format(performance_array))
    best_perf_loc = np.where(performance_array == performance_array.max())[0][0]

    # hack the parameters to be the best choice for the rest of the function, this keeps recoding to a minimum:
    parameter = parameters[best_perf_loc]

    results_list = PutSlingerBollinger.Bollinger_strat(time=time,
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

    position_value = results_list[7]

    print('stock price at open: {}'.format(put_buy_price))
    print('strike price: {}'.format(results_list[6]))
    print('stock price at close: {}'.format(put_sell_price))

    print('option cost at open: {}'.format(put_buy_option_price))
    print('option cost at close: {}'.format(put_sell_option_price))

    put_profits = (put_sell_option_price - put_buy_option_price)

    put_percent = (put_sell_option_price - put_buy_option_price) / put_buy_option_price
    print('option % gain: {}'.format(put_percent))

    put_percent[put_percent > 5] = 5  # put an upper bound on the option returns.

    print('position values: {}'.format(position_value))
    account_value = np.sum(position_value)
    print('account value ate EOD: {}'.format(account_value))

    # put_percent_avg = np.sum(put_percent) / put_percent.shape[0]

    put_percent_avg = np.sum(account_value) - 1
    print('average option % gain: {}'.format(put_percent_avg))

    results_list.append(put_percent)
    results_list.append(put_percent_avg)

    focus_top = time.shape[0] - 60 * 48
    focus_bot = time.shape[0] + 1
    focus_top = 0
    focus_bot = time.shape[0] + 1

    candle_rescaled = candle - np.sum(candle) / sma.shape[0]
    candle_rescaled = candle_rescaled / np.abs(candle_rescaled).max()
    sma_rescaled = sma - np.sum(sma) / sma.shape[0]
    sma_rescaled = sma_rescaled / np.abs(sma_rescaled).max()
    Bollinger_oscillator = 2 * (sma_short - sma) / np.absolute(sma_high_bollinger - sma_low_bollinger)

    minute_time = Analytics.minute_time(time)
    # print(minute_time)

    '''
    ax[0].plot(time[focus_top:focus_bot], candle_rescaled, label='candle')
    ax[0].plot(time[focus_top:focus_bot], sma_rescaled, label='sma')
    ax[0].plot(time[focus_top:focus_bot], sma_d[focus_top:focus_bot] / np.abs(sma_d).max(), label='sma_d')
    ax[0].plot(time[focus_top:focus_bot], sma_dd[focus_top:focus_bot] / np.abs(sma_dd).max(), label='sma_dd')
    ax[0].legend()
    '''

    #################################################################################
    # plt.figure(figsize=(20, 10))
    # plt.suptitle('profitable trades')
    # ax[0].plot(time[tradeable], data_volume[tradeable], '.')

    ax_twin = ax[0].twinx()
    ax_twin.plot(minute_time[tradeable], Bollinger_oscillator[tradeable])
    ax_twin.plot(minute_time[tradeable], np.ones_like(minute_time[tradeable]) * parameter['Bollinger_top'], color='k')
    ax_twin.plot(minute_time[tradeable], np.ones_like(minute_time[tradeable]) * parameter['Bollinger_bot'], color='k')

    ax[0].plot(minute_time[tradeable], candle[tradeable], '.', label=str(put_percent_avg))
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

    ax[0].legend()

    #################################################################################
    # plt.figure(figsize=(20, 10))
    # plt.suptitle('loss trades')
    # ax[1].plot(minute_time, data_volume, '.')

    ax_twin = ax[1].twinx()
    ax_twin.plot(minute_time[tradeable], Bollinger_oscillator[tradeable])
    ax_twin.plot(minute_time[tradeable], np.ones_like(minute_time[tradeable]) * parameter['Bollinger_top'], color='k')
    ax_twin.plot(minute_time[tradeable], np.ones_like(minute_time[tradeable]) * parameter['Bollinger_bot'], color='k')

    ax[1].plot(minute_time[tradeable], candle[tradeable], '.', label=str(put_percent_avg))
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

    ax[1].legend()

    return put_percent_avg, performance_array


if __name__ == "__main__":

    '''File Handling'''
    filedirectory = 'D:/StockData/'
    ticker = 'SPY'
    # group_choice = np.random.choice(list(datafile.keys()))

    parameters = []
    # parameters = {'Bollinger_top': .0, 'Bollinger_bot': -.8, 'stop_loss': .8, 'profit': 1.8}
    parameters.append({'Bollinger_top': .0,
                       'Bollinger_bot': -2.0,
                       'stop_loss': .8,
                       'profit': .8,
                       'flip': 1,
                       'option_type': position_class.OptionType.PUT,
                       'VIX': 24}
                      )

    parameters.append({'Bollinger_top': .0,
                       'Bollinger_bot': -2.0,
                       'stop_loss': .5,
                       'profit': .8,
                       'flip': 1,
                       'option_type': position_class.OptionType.PUT,
                       'VIX': 24}
                      )
    '''
    parameters = []
    # parameters = {'Bollinger_top': .0, 'Bollinger_bot': -.8, 'stop_loss': .8, 'profit': 1.8}
    parameters.append({'Bollinger_top': .80,
                       'Bollinger_bot': 0.,
                       'stop_loss': .8,
                       'profit': 1.3,
                       'flip': 1,
                       'option_type': position_class.OptionType.PUT,
                       'VIX': 24}
                      )

    parameters.append({'Bollinger_top': .80,
                       'Bollinger_bot': .0,
                       'stop_loss': .8,
                       'profit': 1.3,
                       'flip': -1,
                       'option_type': position_class.OptionType.CALL,
                       'VIX': 24}
                      )
    '''

    days_in_directory, unique_dates = DailyGenerator.days_in_directory(filedirectory='D:/StockData/', ticker=ticker)
    print('days in directory: {}'.format(days_in_directory))
    fig, axs = plt.subplots(nrows=days_in_directory, ncols=2, sharex=False, figsize=(30, int(4 * days_in_directory)))

    daily_percent_gain = []
    all_strats_percent_gain = []
    for ax_row, [datafile, date, VIX] in zip(axs,
                                        DailyGenerator.data_file_generator(filedirectory=filedirectory, ticker=ticker)):
        print('Date: {}'.format(date))

        for param in parameters:
            param['VIX'] = VIX

        print('VIX: {}'.format(VIX))

        start_time = time.perf_counter()
        put_percent_avg, performance_array = slinger(ax=ax_row, datafile=datafile, ticker=ticker, parameters=parameters)
        daily_percent_gain.append(put_percent_avg)
        all_strats_percent_gain.append(performance_array)
        duration = time.perf_counter() - start_time
        print('time for strategy run on this day: {}'.format(duration))

    print(daily_percent_gain)
    array_profit = np.array(daily_percent_gain)
    array_profit[np.isnan(array_profit)] = 0

    all_strats_percent_gain = np.stack(all_strats_percent_gain, axis=0)
    all_strats_percent_gain[np.isnan(all_strats_percent_gain)] = 0

    plt.figure(figsize=(10, 10))
    plt.suptitle('Daily percent gain')
    plt.plot(all_strats_percent_gain[:, 0], '.', color='r')
    plt.plot(all_strats_percent_gain[:, 1], '.', color='b')

    total_profit = np.product(1 + array_profit)
    print('total value over {}-day period is : {}'.format(len(daily_percent_gain), total_profit))

    plt.figure(figsize=(10, 10))
    plt.suptitle('Daily Cumulative Gain')
    plt.plot(np.cumprod(1 + array_profit), '.')

    # assume random choice for strategies:

    random_strat = np.random.randint(low=0, high=2, size=all_strats_percent_gain.shape[0])
    rand_all_strat = all_strats_percent_gain[np.arange(all_strats_percent_gain.shape[0]), random_strat]

    plt.figure(figsize=(10, 10))
    plt.suptitle('Daily percent gain, Random Strategy')
    plt.plot(rand_all_strat, '.', color='r')

    plt.figure(figsize=(10, 10))
    plt.suptitle('Daily Cumulative Gain, Random Strategy')
    plt.plot(np.cumprod(1 + rand_all_strat), '.')
