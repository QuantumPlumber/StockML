import script_context

import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
from Stonks.Analytics import Analytics
from Stonks.Strategies import PutSlingerBollinger
from Stonks.DataGrubbing import DailyGenerator

import importlib

importlib.reload(Analytics)
importlib.reload(PutSlingerBollinger)
importlib.reload(DailyGenerator)


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

    results_list = PutSlingerBollinger.Bollinger_strat(time=time,
                                                       sma=sma,
                                                       bollinger_up=sma_high_bollinger,
                                                       bollinger_down=sma_low_bollinger,
                                                       sma_d=sma_d,
                                                       candle=candle,
                                                       candle_high=candle_high_bollinger,
                                                       candle_low=candle_low_bollinger,
                                                       parameters=parameters)

    put_buy_locs = results_list[0]
    put_buy_price = results_list[1]
    # print(put_buy_price)
    put_buy_option_price = results_list[2]
    print(put_buy_option_price)

    put_sell_locs = results_list[3]
    put_sell_price = results_list[4]
    # print(put_sell_price)
    put_sell_option_price = results_list[5]
    print(put_sell_option_price)

    put_profits = (put_sell_option_price - put_buy_option_price)

    put_percent = (put_sell_option_price - put_buy_option_price) / put_buy_option_price
    print(put_percent)
    put_percent_avg = np.sum(put_percent) / put_percent.shape[0]
    print(put_percent_avg)

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
    ax_twin.plot(time[tradeable], Bollinger_oscillator[tradeable])
    ax_twin.plot(time[tradeable], np.ones_like(time[tradeable]) * parameters['Bollinger_top'], color='k')
    ax_twin.plot(time[tradeable], np.ones_like(time[tradeable]) * parameters['Bollinger_bot'], color='k')

    ax[0].plot(time[tradeable], candle[tradeable], '.', label=str(put_percent_avg))
    ax[0].plot(time[tradeable], sma[tradeable])
    ax[0].plot(time[tradeable], sma_low_bollinger[tradeable])
    ax[0].plot(time[tradeable], sma_high_bollinger[tradeable])
    ax[0].plot(time[tradeable], candle_low_bollinger[tradeable])
    ax[0].plot(time[tradeable], candle_high_bollinger[tradeable])

    profit_put_buy_locs = put_buy_locs[put_profits >= 0]
    put_cut = profit_put_buy_locs[profit_put_buy_locs > focus_top]
    ax[0].plot(time[put_cut], candle[put_cut], '>', color='r')

    profit_put_sell_locs = put_sell_locs[put_profits >= 0]
    put_cut = profit_put_sell_locs[profit_put_sell_locs > focus_top]
    ax[0].plot(time[put_cut], candle[put_cut], '<', color='g')

    ax[0].legend()

    #################################################################################
    # plt.figure(figsize=(20, 10))
    # plt.suptitle('loss trades')
    # ax[1].plot(time, data_volume, '.')
    ax[1].plot(time[tradeable], candle[tradeable], '.', label=str(put_percent_avg))
    ax[1].plot(time[tradeable], sma[tradeable])
    ax[1].plot(time[tradeable], sma_low_bollinger[tradeable])
    ax[1].plot(time[tradeable], sma_high_bollinger[tradeable])
    ax[1].plot(time[tradeable], candle_low_bollinger[tradeable])
    ax[1].plot(time[tradeable], candle_high_bollinger[tradeable])

    loss_put_buy_locs = put_buy_locs[put_profits < 0]
    put_cut = loss_put_buy_locs[loss_put_buy_locs > focus_top]
    ax[1].plot(time[put_cut], candle[put_cut], '>', color='r')

    loss_put_sell_locs = put_sell_locs[put_profits < 0]
    put_cut = loss_put_sell_locs[loss_put_sell_locs > focus_top]
    ax[1].plot(time[put_cut], candle[put_cut], '<', color='g')

    ax[1].legend()

    return put_percent_avg


if __name__ == "__main__":

    '''File Handling'''
    filedirectory = 'D:/StockData/'
    ticker = 'SPY'
    # group_choice = np.random.choice(list(datafile.keys()))

    parameters = {'Bollinger_top': .0, 'Bollinger_bot': -.8, 'stop_loss': .8, 'profit': 1.8}
    parameters = {'Bollinger_top': .2, 'Bollinger_bot': -.4, 'stop_loss': .8, 'profit': .8}

    days_in_directory = DailyGenerator.days_in_directory(filedirectory='D:/StockData/', ticker=ticker)
    fig, axs = plt.subplots(nrows=days_in_directory, ncols=2, sharex=False, figsize=(30, int(4 * days_in_directory)))

    daily_percent_gain = []
    for ax_row, [datafile, date] in zip(axs,
                                        DailyGenerator.data_file_generator(filedirectory=filedirectory, ticker=ticker)):
        print('Date: {}'.format(date))
        daily_percent_gain.append(slinger(ax=ax_row, datafile=datafile, ticker=ticker, parameters=parameters))

    print(daily_percent_gain)
    array_profit = np.array(daily_percent_gain)
    array_profit[np.isnan(array_profit)] = 0
    total_profit = np.product(1 + array_profit)
    print('total \% profit over {}-day period is : {}'.format(len(daily_percent_gain), total_profit))
