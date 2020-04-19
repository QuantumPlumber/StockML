import numpy as np
import os
import h5py
import arrow
import matplotlib.pyplot as plt
import importlib

from Stonks.utilities.config import apikey, username, password, secretQ
import Stonks.utilities.config
import Stonks.global_enums as enums

from Stonks.Analytics import live_market_analytics_class as Analytics_class

importlib.reload(Analytics_class)

from Stonks.Positions import live_market_position_class as positions

importlib.reload(positions)

from Stonks.utilities.utility_class import UtilityClass

importlib.reload(UtilityClass)

from Stonks.Strategies import putSlingerBollinger_conditions


class strategy():
    def __init__(self, **kwargs):
        # symbol to trade
        self.symbol = kwargs['symbol']

        # utility class to handle API functions
        self.utility_class = UtilityClass(verbos=True)

        # analysis class to handle data analysis
        self.analytics = Analytics_class.analysis(compute_dict=self.analysis_parameters)

        # timing and dates
        self.today = arrow.now('America/New_York')
        self.today = self.today.replace(hour=0, minute=0, second=0, microsecond=0)
        self.get_options_end_date()
        self.current_minute = self.trading_day_minute()

        # save initial account values
        self.initial_account_values = self.get_current_account_values()

        # positions list
        self.positions = []

        self.parameters = kwargs['parameters']

    def trading_day_minute(self):
        market_open = arrow.now('America/New_York').replace(hours=9, minutes=30, seconds=0)
        current_time = arrow.now('America/New_York').replace(seconds=0)
        difference = current_time - market_open
        minute = difference.hours * 60 + difference.minutes
        return minute

    def get_options_end_date(self):
        '''
        set the options end date for quotes to the nearest options end date.
        for SPY this is MWF
        for all others this is F
        :return:
        '''
        lookback_days = 0
        today = arrow.now('America/New_York')
        if self.symbol == 'SPY':
            if today.isoweekday() in [2, 4]:
                self.options_end_date = today.shift(days=1)
        else:
            self.options_end_date = today.shift(days=(5 - today.isoweekday()))

    def get_current_account_values(self):
        account = self.utility_class.access_accounts(self.utility_class.account_id)
        self.current_account_values = self.utility_class.account_data[0]['securitiesAccount']['currentBalances']

    def create_option_name(self, ticker: str, strike: int, option_type: str):
        self.option_date_string = self.options_end_date.format(fmt='MMDDYY')
        quote_string = ticker + '_' + self.options_end_date.format(fmt='MMDDYY') + option_type + str(strike)
        self.quote_string = quote_string
        return quote_string

    def update_analytics(self):
        '''
        request new data and call the analytics class
        :return:
        '''

        today = arrow.now('America/New_York')
        yesterday = today.shift(days=-1)

        # build the payload.
        payload = {enums.PriceHistoryPayload.apikey.value: apikey,
                   enums.PriceHistoryPayload.periodType.value: enums.PeriodTypeOptions.day.value,
                   enums.PriceHistoryPayload.period.value: 1,
                   enums.PriceHistoryPayload.frequencyType.value: enums.FrequencyTypeOptions.minute.value,
                   enums.PriceHistoryPayload.frequency.value: 1,
                   enums.PriceHistoryPayload.startDate.value: yesterday.timestamp * 1e3,
                   enums.PriceHistoryPayload.endDate.value: today.timestamp * 1e3,
                   enums.PriceHistoryPayload.needExtendedHoursData.value: 'true'
                   }
        price_history = self.pointer_to_utility_class.get_price_history(symbol=self.symbol, payload=payload)
        self.analytics.compute_analytics(compute_dict=self.analysis_parameters)

    def change_metaparameters(self, **kwargs):
        '''
        Needs alot of work to handle open orders...
        :return:
        '''
        self.__init__(kwargs)  # re-initialize to new kwargs

    def check_stop_trading(self):
        '''
        Determine if trading should continue
        :return:
        '''
        percent_lost = 1. - self.current_account_values['liquidationValue'] / self.initial_account_values[
            'liquidationValue']

        if percent_lost >= .2:
            return True

    def sell_all_positions(self):
        '''
        Close it out!
        :return:
        '''

        for position in self.positions:
            position.sell_condition = True

        self.sell()

    def check_buy_condition(self):
        '''
        put buy condition function here
        :return:
        '''

        open_position = False
        for position in self.positions:
            if position.is_open:
                open_position = True

        candle = self.analytics.data['candle']
        sma = self.analytics.data['sma'][0]
        sma_short = self.analytics.data['sma'][1]
        bollinger_up, bollinger_down = self.analytics.data['Bollinger'][0]

        threshold = 2 * (sma_short[-1] - sma[-1]) / np.absolute(bollinger_up[-1] - bollinger_down[-1])

        if threshold > self.parameters['Bollinger_top']:
            self.buy_armed = True

        if self.buy_armed and threshold <= self.parameters['Bollinger_top'] and not open_position:
            strike_delta = 2 * (candle[-1] - bollinger_down[-1])
            if strike_delta >= 6:
                strike_delta = 6

            self.strike_price = candle[-1] - strike_delta
            self.positions.append(position.Position())
            self.buy()

        if threshold < self.parameters['Bollinger_top']:
            self.buy_armed = False

    def build_position(self):
        '''
        utiltiy functions for building a position
        :return:
        '''

        payload = {'symbol': 'SPY',
                   'contractType': 'PUT',
                   'strikeCount': 20,
                   'includeQuotes': 'TRUE',
                   'strategy': 'SINGLE',
                   'fromDate': self.today.shift(days=-1).format('YYYY-MM-DD'),
                   'toDate': self.options_end_date.shift(days=1).format('YYYY-MM-DD')}

        self.options_chain_quote = self.utility_class.get_options_chain(payload=payload)

        putExpDateMap = self.options_chain_quote['putExpDateMap']
        date_keys = list(putExpDateMap.keys())
        if len(date_keys) > 1:
            self.putExpDateMap = None
            return False
        else:
            self.options_chain_dict = self.options_chain_quote['putExpDateMap'][date_keys[0]]

        # now find the closest strike price to the strategy price
        strikes_prices = []
        for key in self.options_chain_dict:
            strikes_prices.append(self.options_chain_dict[key]['strikePrice'])

        price_difference = np.abs(np.array(strikes_prices) - self.strike_price)
        min_price_difference = price_difference.min()
        best_stirke_location = np.where(price_difference == min_price_difference)[0]

        chosen_option_quote = self.options_chain_dict[list(self.options_chain_dict.keys())[best_stirke_location]]
        underlying_security_quote = self.options_chain_dict['underlying']

        self.positions.append(positions.Position(parameters=self.parameters,
                                                 underlying_quote=underlying_security_quote,
                                                 quote_data=chosen_option_quote,
                                                 ))

    def buy(self):
        '''
        open a new position
        :return:
        '''
        pos: positions.Position
        for pos in self.positions:
            if pos.needs_bought():
                # enter strategy to buy here

                # calculate limit value
                limit_price = None

                # calculate number of options contracts
                number_of_options = None

                # build purchase dictionary
                payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                           enums.OrderPayload.orderType.value: enums.OrderTypeOptions.LIMIT.value,
                           enums.OrderPayload.price.value: limit_price,
                           enums.OrderPayload.duration.value: enums.DurationOptions.DAY.value,
                           enums.OrderPayload.quantity.value: number_of_options,
                           enums.OrderPayload.orderLegCollection.value: [
                               {
                                   enums.OrderLegCollectionDict.instruction.value: enums.InstructionOptions.BUY_TO_OPEN.value,
                                   enums.OrderLegCollectionDict.quantity.value: 1,
                                   enums.OrderLegCollectionDict.instrument.value: {
                                       enums.InstrumentType.symbol.value: pos.symbol,
                                       enums.InstrumentType.assetType.value: enums.AssetTypeOptions.OPTION.value
                                   }

                               }],
                           enums.OrderPayload.orderStrategyType.value: enums.OrderStrategyTypeOptions.SINGLE.value,
                           enums.OrderPayload.orderId.value: np.random.random_integers(low=int(1e8), high=int(1e9),
                                                                                       size=1)}

                if self.utility_class.place_order(payload=payload):
                    pos.update_orders(order_payload_list=[payload, ])

    def update_positions(self):
        # get account position dicts to feed in to positions

        # request position oders and get quotes
        pass

    def implement_stop_loss(self):
        # input stoploss positions on all positions with open orders.
        pass

    def check_sell_condition(self):
        '''
        put buy condition function here
        :return:
        '''

    def sell(self):
        '''
        close positions
        :return:
        '''
        pos: positions.Position
        for pos in self.positions:
            if pos.needs_sold():
                # enter strategy to sell here

                # calculate limit value
                limit_price = None

                # calculate number of options contracts
                number_of_options = None

                # build purchase dictionary
                payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                           enums.OrderPayload.orderType.value: enums.OrderTypeOptions.LIMIT.value,
                           enums.OrderPayload.price.value: limit_price,
                           enums.OrderPayload.duration.value: enums.DurationOptions.DAY.value,
                           enums.OrderPayload.quantity.value: number_of_options,
                           enums.OrderPayload.orderLegCollection.value: [
                               {
                                   enums.OrderLegCollectionDict.instruction.value: enums.InstructionOptions.SELL_TO_CLOSE.value,
                                   enums.OrderLegCollectionDict.quantity.value: 1,
                                   enums.OrderLegCollectionDict.instrument.value: {
                                       enums.InstrumentType.symbol.value: pos.symbol,
                                       enums.InstrumentType.assetType.value: enums.AssetTypeOptions.OPTION.value
                                   }

                               }],
                           enums.OrderPayload.orderStrategyType.value: enums.OrderStrategyTypeOptions.SINGLE.value,
                           enums.OrderPayload.orderId.value: np.random.random_integers(low=int(1e8), high=int(1e9),
                                                                                       size=1)}

                if self.utility_class.place_order(payload=payload):
                    pos.update_orders(order_payload_list=[payload, ])

    def order_status(self):
        '''
        check on order stati for options with open orders
        :return:
        '''
        pos: positions.Position
        for pos in self.positions:
            if pos.open_order:
                # must write function in utility class to get order history. Close orders on options that have filled.
                # Raise flags on orders that need re-assessed.
                pass

    def implement_strategy(self, **kwargs):
        '''
        Implement the strategy at each timestep
        :param kwargs:
        :return:
        '''
        update_minute_clock = True
        while True:
            # trigger on the minute, every minute, when the new candle is available.

            # set the new minute.
            if update_minute_clock:
                new_minute = arrow.now('America/New_York')
                new_minute = new_minute.replace(seconds=0)
                update_minute_clock = False

            # compute the elapsed time and trigger 5 seconds into the new minute.
            elapsed_time = new_minute - arrow.now('America/New_York')
            if elapsed_time.seconds > 65:
                # implement the algorithm

                # reset clock
                update_minute_clock = True

                self.update_analytics()

                if self.check_stop_trading():
                    self.close_all_positions()
                    break
                else:
                    self.check_buy_condition()
                    self.check_sell_condition()

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
