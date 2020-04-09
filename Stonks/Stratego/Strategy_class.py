import numpy as np
import os
import h5py
import arrow
import matplotlib.pyplot as plt
import importlib

from Stonks.Analytics import Analytics_class

importlib.reload(Analytics_class)

from Stonks.Positions import position_class

importlib.reload(position_class)


class strategy():
    def __init__(self, **kwargs):
        self.analysis_parameters = kwargs['analysis_parameters']
        self.trigger_parameters = kwargs['trigger_parameters']
        self.buy_condition = kwargs['buy_condition']
        self.sell_condition = kwargs['sell_condition']

        self.data_directory = kwargs['data_directory']

        self.analytics = Analytics_class.analysis(compute_dict=self.analysis_parameters)

    def days_in_directory(self, filedirectory='D:/StockData/', ticker='SPY'):

        file_number = 0

        for direntry in os.scandir(filedirectory):

            if direntry.is_dir():
                continue

            if direntry.is_file():
                filepath = direntry.path
                # print(filepath)
                try:
                    datafile = h5py.File(filepath, 'r')
                except:
                    print('could not open file: {}'.format(filepath))
                    continue

            time_data = datafile[ticker]['datetime'][...]
            if time_data.shape[0] == 0:
                print('no \'SPY\' data in file: {}'.format(filepath))
                continue

            file_number += 1
            datafile.close()

        self.num_files_in_directory = file_number
        return file_number

    def data_file_generator(self, filedirectory='D:/StockData/', ticker='SPY'):

        for direntry in os.scandir(filedirectory):

            if direntry.is_dir():
                continue

            if direntry.is_file():
                filepath = direntry.path
                print(filepath)
                try:
                    datafile = h5py.File(filepath, 'r')
                except:
                    print('could not open file: {}'.format(filepath))
                    continue

            time_data = datafile[ticker]['datetime'][...]
            if time_data.shape[0] == 0:
                print('no \'{}\' data in file: {}'.format(ticker, filepath))
                continue
            else:
                mid_day = time_data[time_data.shape[0] // 2]
                utc_time = arrow.get(mid_day * 1e-3).to('utc')
                utc_time = utc_time.shift(hours=-4)  # must explicitely shift time for numpy to recognize
                date = str(utc_time.date())

            yield datafile, date

    def update_analytics(self, compute_dict):
        self.analysis_parameters = compute_dict
        self.analytics.compute_analytics(compute_dict=self.analysis_parameters)

    def test_strategy(self, **kwargs):
        self.__init__(kwargs)  # re-initialize to new kwargs

        for i in np.arange(self.analytics.num_datapoints):
            pass
            # this is where the algorithm gets tested.

    def setup_plot(self):
        fig, axs = plt.subplots(nrows=self.num_files_in_directory, ncols=2, sharex=False,
                                figsize=(30, int(4 * self.num_files_in_directory)))

    def plot_day(self, ax):
        ax_twin = ax[0].twinx()
        ax_twin.plot(self.self.time[self.tradeable], self.Bollinger_oscillator[self.tradeable])
        ax_twin.plot(self.time[self.tradeable],
                     np.ones_like(self.time[self.tradeable]) * self.hyper_parameters['Bollinger_top'], color='k')
        ax_twin.plot(self.time[self.tradeable],
                     np.ones_like(self.time[self.tradeable]) * self.hyper_parameters['Bollinger_bot'], color='k')

        ax[0].plot(self.time[self.tradeable], self.self.candle[self.tradeable], '.', label=str(put_percent_avg))
        ax[0].plot(self.time[self.tradeable], self.sma[self.tradeable])
        ax[0].plot(self.time[self.tradeable], self.self.sma_low_bollinger[self.tradeable])
        ax[0].plot(self.time[self.tradeable], self.sma_high_bollinger[self.tradeable])
        ax[0].plot(self.time[self.tradeable], self.candle_low_bollinger[self.tradeable])
        ax[0].plot(self.time[self.tradeable], self.candle_high_bollinger[self.tradeable])

        profit_put_buy_locs = self.put_buy_locs[self.put_profits >= 0]
        put_cut = profit_put_buy_locs
        ax[0].plot(self.time[put_cut], self.candle[put_cut], '>', color='k')

        profit_put_sell_locs = self.put_sell_locs[self.put_profits >= 0]
        put_cut = profit_put_sell_locs
        ax[0].plot(self.time[put_cut], self.candle[put_cut], '<', color='k')

        ax[0].legend()

        #################################################################################
        # plt.figure(figsize=(20, 10))
        # plt.suptitle('loss trades')
        # ax[1].plot(self.time, data_volume, '.')

        ax_twin = ax[1].twinx()
        ax_twin.plot(self.time[self.tradeable], self.Bollinger_oscillator[self.tradeable])
        ax_twin.plot(self.time[self.tradeable], np.ones_like(self.time[self.tradeable]) * parameters['Bollinger_top'],
                     color='k')
        ax_twin.plot(self.time[self.tradeable], np.ones_like(self.time[self.tradeable]) * parameters['Bollinger_bot'],
                     color='k')

        ax[1].plot(self.time[self.tradeable], self.candle[self.tradeable], '.', label=str(put_percent_avg))
        ax[1].plot(self.time[self.tradeable], self.sma[self.tradeable])
        ax[1].plot(self.time[self.tradeable], self.sma_low_bollinger[self.tradeable])
        ax[1].plot(self.time[self.tradeable], self.sma_high_bollinger[self.tradeable])
        ax[1].plot(self.time[self.tradeable], self.candle_low_bollinger[self.tradeable])
        ax[1].plot(self.time[self.tradeable], self.candle_high_bollinger[self.tradeable])

        loss_put_buy_locs = self.put_buy_locs[self.put_profits < 0]
        put_cut = loss_put_buy_locs
        ax[1].plot(self.time[put_cut], self.candle[put_cut], '>', color='k')

        loss_put_sell_locs = self.put_sell_locs[self.put_profits < 0]
        put_cut = loss_put_sell_locs
        ax[1].plot(self.time[put_cut], self.candle[put_cut], '<', color='k')

        ax[1].legend()
