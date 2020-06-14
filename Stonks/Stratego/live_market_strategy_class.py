import script_context

import numpy as np
import pandas as pd
import os
import h5py
import arrow
import matplotlib.pyplot as plt
import importlib
import time
import math
import inspect
import h5py

from Stonks.utilities.config import apikey, username, password, secretQ
# import Stonks.utilities.config
import Stonks.global_enums as enums

from Stonks.Analytics import live_market_analytics_class as analytics_class

importlib.reload(analytics_class)

from Stonks.Positions import live_market_position_class as positions

importlib.reload(positions)

from Stonks.Orders import orders_class

importlib.reload(orders_class)

from Stonks.utilities import utility_class

importlib.reload(utility_class)

from Stonks.utilities import utility_exceptions


class Strategy:
    def __init__(self, **kwargs):

        # behavior
        self.verbose = kwargs['verbose']
        self.state = enums.StonksStrategyState.initialized

        # Data logging
        self.log_root_directory = kwargs['log_directory']
        self.log_directory = None
        self.metadata_name = None
        self.metadata_path = None

        # symbol to trade
        self.symbol = kwargs['symbol']

        # utility class to handle API functions
        self.utility_class = utility_class.UtilityClass(verbose=True)
        # login
        self.utility_class.login()

        # analysis class to handle data analysis
        self.compute_dict = kwargs['compute_dict']
        self.analytics = analytics_class.Analysis(compute_dict=self.compute_dict)

        # timing and dates
        self.today = arrow.now('America/New_York')
        self.today = self.today.replace(hour=0, minute=0, second=0, microsecond=0)
        self.get_options_end_date()
        # self.current_second = self.trading_day_second()

        # save initial account values and current account values
        self.initial_account_values = self.get_current_account_values()
        # variable set by function call above
        self.current_account_values = None

        # positions list
        self.positions = []

        # strategy parameters and variables
        self.parameters = kwargs['parameters']
        self.buy_armed = False
        self.sell_armed = False

    def set_up_data_logging(self):
        '''
        Create a directory for storing data

        :return:
        '''

        self.log_directory = self.log_root_directory + '/' + self.today.format('MMDDYY') + '/'

        if not os.path.isdir(self.log_directory):  # Create the directory if it does not exist
            os.mkdir(self.log_directory)

        self.position_log_directory = self.log_directory + 'Positions/'
        if not os.path.isdir(self.position_log_directory):  # Create the directory if it does not exist
            os.mkdir(self.position_log_directory)

        self.option_chain_log_directory = self.log_directory + 'Options_Quote/'
        if not os.path.isdir(self.option_chain_log_directory):  # Create the directory if it does not exist
            os.mkdir(self.option_chain_log_directory)

        market_open = arrow.now('America/New_York').replace(hour=9, minute=30, second=0)
        market_close = arrow.now('America/New_York').replace(hour=16, minute=0, second=0)
        delta_market = market_close - market_open
        self.number_of_option_logs = int(delta_market.seconds // 60 + 10)
        self.current_option_log_number = 0

        '''
        self.metadata_name = 'metadata.txt'
        self.metadata_path = self.log_directory + self.metadata_name
        if not os.path.isfile(self.metadata_path):
            self.metadata = open(self.metadata_path, 'a+', buffering=1)

            self.metadata.write('Data logging for strategy class ' + self.today.format('MM-DD-YYYY'))
            self.metadata.write('\n')
            print('metadata created')
        else:
            # open metadata file for writing
            self.metadata = open(self.metadata_path, 'a+', buffering=1)
            print('metadata opened')
        # self.metadata = metadata
        '''

    def log_snapshot(self):

        metadata_name = 'metadata' + arrow.now('America/New_York').format('HH_mm_ss') + '.txt'
        metadata_path = self.log_directory + metadata_name
        if not os.path.isfile(metadata_path):
            metadata = open(metadata_path, 'a+', buffering=1)
        else:
            metadata_name = 'metadata_B_' + arrow.now('America/New_York').format('HH_mm_ss') + '.txt'
            metadata_path = self.log_directory + metadata_name
            metadata = open(metadata_path, 'a+', buffering=1)

        attributes = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        writeable = [a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))]

        for element in writeable:
            metadata.write(str(element) + '\n')

        # sleep to prevent name conflict in file creation.
        time.sleep(1)

    def log_options_chain(self):

        def group_creator(nested_dict: dict, group: h5py.Group):
            if type(nested_dict) is dict:
                # check if item is a dict
                for key in nested_dict.keys():
                    if (type(nested_dict[key]) is list) or (type(nested_dict[key]) is dict):
                        # if item contains a dict or a list, create a subroup for it and recurse
                        subgroup = group.create_group(key)
                        group_creator(nested_dict=nested_dict[key], group=subgroup)
                    else:
                        # if the item is not a list or a dict, then it must be a value
                        # if type(nested_dict[key]) is in [np.]
                        # print(np.dtype(type(nested_dict[key])))
                        if type(nested_dict[key]) in [str, bool, type(None)]:
                            pass
                        else:
                            data_type = np.float
                            group.create_dataset(key, shape=[self.number_of_option_logs], dtype=data_type)
            elif type(nested_dict) is list:
                for item in nested_dict:
                    # if the item is a list, then recurse with the original group for each item in the list
                    # this has the effect of ignoring lists.
                    group_creator(nested_dict=item, group=group)

        # TODO: update this function to work

        payload = {'symbol': 'SPY',
                   'contractType': 'PUT',
                   'strikeCount': 20,
                   'includeQuotes': 'TRUE',
                   'strategy': 'SINGLE',
                   'fromDate': self.today.shift(days=-1).format('YYYY-MM-DD'),
                   'toDate': self.options_end_date.shift(days=1).format('YYYY-MM-DD')}

        self.options_chain_quote = self.utility_class.get_options_chain(payload=payload)

        filename = self.option_chain_log_directory + 'Option_chain.hdf5'
        if not os.path.isfile(filename):
            self.option_chain_hdf5 = h5py.File(filename, 'a')
            group_creator(nested_dict=self.options_chain_quote, group=self.option_chain_hdf5)
        else:
            self.option_chain_hdf5 = h5py.File(filename, 'w')

        def write_nested_dict(nested_dict: dict, group: h5py.Group):
            num = 0
            if type(nested_dict) is dict:
                # check if item is a dict
                for key in nested_dict.keys():
                    if (type(nested_dict[key]) is list) or (type(nested_dict[key]) is dict):
                        # if item contains a dict or a list, create a subroup for it and recurse
                        subgroup = group[key]
                        write_nested_dict(nested_dict=nested_dict[key], group=subgroup)
                    else:
                        # if the item is not a list or a dict, then it must be a value
                        # if type(nested_dict[key]) is in [np.]
                        # print(np.dtype(type(nested_dict[key])))
                        if type(nested_dict[key]) in [str, bool, type(None)]:
                            pass
                        else:
                            # print(float(nested_dict[key]))
                            data_type = np.float
                            group[key][num] = float(nested_dict[key])
            elif type(nested_dict) is list:
                for item in nested_dict:
                    # if the item is a list, then recurse with the original group for each item in the list
                    # this has the effect of ignoring lists.
                    write_nested_dict(nested_dict=item, group=group)

        write_nested_dict(nested_dict=self.options_chain_quote, group=self.option_chain_hdf5)

        self.option_chain_hdf5.close()
        self.current_option_log_number += 1

    def trading_day_time(self):
        market_open = arrow.now('America/New_York').replace(hour=9, minute=30, second=0)
        market_close = arrow.now('America/New_York').replace(hour=16, minute=0, second=0)
        current_time = arrow.now('America/New_York').replace(second=0)
        delta_t_from_open = current_time - market_open
        self.seconds_from_open = delta_t_from_open.seconds
        delta_t_from_close = market_close - current_time
        self.seconds_to_close = delta_t_from_close.seconds

    def get_options_end_date(self):
        '''
        set the options end date for quotes to the nearest options end date.
        for SPY this is MWF
        for all others this is F = 5 in isoweekdays
        :return:
        '''
        today = arrow.now('America/New_York')
        if self.symbol == 'SPY':
            if today.isoweekday() in [2, 4]:
                self.options_end_date = today.shift(days=1)
            else:
                self.options_end_date = today
        else:
            self.options_end_date = today.shift(days=(5 - today.isoweekday()))

    def get_current_account_values(self):
        account = self.utility_class.access_accounts()
        current_account_values = account[0]['securitiesAccount']['currentBalances']
        self.current_account_values = current_account_values
        return current_account_values

    def update_analytics(self):
        '''
        request new data and call the analytics class
        :return:
        '''

        today = arrow.now('America/New_York')
        # TODO: remove shift...
        # today = today.shift(days=-3)
        yesterday = today.shift(hours=-1)

        # build the payload.
        payload = {enums.PriceHistoryPayload.apikey.value: apikey,
                   # enums.PriceHistoryPayload.periodType.value: enums.PeriodTypeOptions.day.value,
                   # enums.PriceHistoryPayload.period.value: 1,
                   enums.PriceHistoryPayload.frequencyType.value: enums.FrequencyTypeOptions.minute.value,
                   enums.PriceHistoryPayload.frequency.value: 1,
                   enums.PriceHistoryPayload.startDate.value: int(yesterday.timestamp * 1e3),
                   enums.PriceHistoryPayload.endDate.value: int(today.timestamp * 1e3),
                   enums.PriceHistoryPayload.needExtendedHoursData.value: 'true'
                   }
        price_history = self.utility_class.get_price_history(symbol=self.symbol, payload=payload)

        data = pd.DataFrame.from_dict(price_history['candles'])
        # print(data)
        self.analytics.compute_analytics(data=data)

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

        # must explicitly ensure updated account values in main loop
        # self.get_current_account_values()

        self.percent_lost = 1. - self.current_account_values['liquidationValue'] / self.initial_account_values[
            'liquidationValue']

        if self.percent_lost >= self.parameters['stop_trading']:
            return True

    def close_all_positions(self):
        '''
        Close it out!
        :return:
        '''

        pos: positions.Position
        for pos in self.positions:
            pos.status = enums.StonksPositionState.needs_close_order

    def update_positions(self):
        '''
        update positions and orders to match current account status

        This by default does not create positions, so there is a possibility that a misplaced order can create
        a position that won't be handled.

        It is expected that any order is created from a position definition

        :return:
        '''
        # get account position dicts to feed in to positions
        self.account_positions = self.utility_class.get_account_positions()

        # get orders dict for this account and prepare it
        # get orders for today only.
        payload = {'maxResults': 1000,
                   'fromEnteredTime': arrow.now('America/New_York').format('YYYY-MM-DD'),
                   'toEnteredTime': arrow.now('America/New_York').format('YYYY-MM-DD')}
        self.account_orders_list = self.utility_class.get_orders(payload=payload)

        # run this for loop in both directions:
        # first look for account positions that match strategy positions
        for account_position in self.account_positions:
            account_position_found = False
            # iterate through positions
            pos: positions.Position
            for pos in self.positions:
                if pos.position_active:
                    # only work on open positions
                    if pos.symbol == account_position['instrument']['symbol']:
                        self.option_quote = self.utility_class.get_quote(symbol=pos.symbol)
                        self.underlying_quote = self.utility_class.get_quote(symbol=pos.underlying_symbol)
                        pos.update_price_and_value(underlying_quote=self.underlying_quote,
                                                   quote_data=self.option_quote,
                                                   position_data=account_position)
                        account_position_found = True

            # if there are no matching open strategy positions, create a new position..
            if not account_position_found:
                if self.verbose:
                    print('creating new position from unknown account position..')
                self.option_quote = self.utility_class.get_quote(symbol=account_position['instrument']['symbol'])
                self.underlying_quote = self.utility_class.get_quote(
                    symbol=account_position['instrument']['underlyingSymbol'])
                new_position = positions.Position(underlying_quote=self.underlying_quote,
                                                  quote_data=self.option_quote,
                                                  quantity=None)
                # update new position:
                new_position.update_price_and_value(underlying_quote=self.underlying_quote,
                                                    quote_data=self.option_quote,
                                                    position_data=account_position)

                new_position.status = enums.StonksPositionState.needs_stop_loss_order

                # TODO: this needs a function to determine the state of the newly created function. Mainly is there an open order?

                # log the position creation for good measure.
                new_position.log_snapshot(self.position_log_directory)

                self.positions.append(new_position)

        # Then look for strategy positions that don't match account positions
        pos: positions.Position
        for pos in self.positions:
            if pos.position_active:
                strategy_position_found = False
                # iterate through positions
                for account_position in self.account_positions:
                    # only work on open positions
                    if pos.symbol == account_position['instrument']['symbol']:
                        # if the position is found, great, we already updated it above
                        strategy_position_found = True

                        # if there are no matching open strategy positions, create a new position..
                if not strategy_position_found:
                    if self.verbose:
                        print('No account position found for active strategy position. Setting quantity to zero..')

                    # if the position is not found, then teh quantity has been reduced to zero!
                    pos.quantity = 0

        # iterate through positions
        # order information from the API is always complete
        pos: positions.Position
        for pos in self.positions:
            if pos.position_active:
                # update orders for this positions
                # first collect all orders related to this position
                local_order_list = []
                for order in self.account_orders_list:
                    if order[enums.OrderPayload.orderLegCollection.value][0][
                        enums.OrderLegCollectionDict.instrument.value]['symbol'] == pos.symbol:
                        local_order_list.append(order)
                pos.update_orders(order_payload_list=local_order_list)

        # iterate through positions and update order status.
        pos: positions.Position
        for pos in self.positions:
            pos.check_order_stati()

        # print out diagnostics of position:
        if self.verbose:
            pos: positions.Position
            for pos in self.positions:
                if pos.position_active:
                    print('position status:')
                    print(pos.status)
                    print('position target_quantity and quantity:')
                    print([pos.target_quantity, pos.quantity])
                    print('position current currentDayProfitLossPercentage:')
                    print([pos.currentDayProfitLossPercentage])
                    print('position orders:')
                    print([[order.current_status, order.order_id, order.is_open]
                           for order in pos.order_list if order.is_open is not False])

    def create_position(self):
        if self.state is enums.StonksStrategyState.triggering:
            # check for open positions
            self.open_position = False
            pos: positions.Position
            for pos in self.positions:
                if pos.position_active:
                    self.open_position = True

            # compute analytics
            candle = self.analytics.compute[enums.ComputeKeys.candle]
            sma = self.analytics.compute[enums.ComputeKeys.sma][0]
            sma_short = self.analytics.compute[enums.ComputeKeys.sma][1]
            bollinger_down, bollinger_up = self.analytics.compute[enums.ComputeKeys.Bollinger][0]

            self.threshold = 2 * (sma_short[-1] - sma[-1]) / np.absolute(bollinger_up[-1] - bollinger_down[-1])
            if self.verbose: print('Threshold value is: {}'.format(self.threshold))

            ########################################### trigger new position ###########################################

            if self.threshold > self.parameters['Bollinger_top']:
                self.buy_armed = True

            # TODO: revert to previous condition
            if self.buy_armed and self.threshold <= self.parameters['Bollinger_top'] and not self.open_position:
                # if True:

                self.strike_delta = self.parameters['price_multiplier'] * (candle[-1] - bollinger_down[-1])

                if self.verbose: print('Target strike delta is: {}'.format(self.strike_delta))

                if self.strike_delta <= self.parameters['min_strike_delta']:
                    self.strike_delta = self.parameters['min_strike_delta']
                if self.strike_delta >= self.parameters['max_strike_delta']:
                    self.strike_delta = self.parameters['max_strike_delta']

                # TODO: adjust this to allow calls:
                # define strike price
                if self.parameters['option_type'] == enums.StonksOptionType.PUT:
                    self.strike_price = candle[-1] - self.strike_delta
                elif self.parameters['option_type'] == enums.StonksOptionType.CALL:
                    self.strike_price = candle[-1] + self.strike_delta
                if self.verbose: print('Target strike price is: {}'.format(self.strike_price))

                #################################### Compute capital for new position ################################

                # self.get_current_account_values()
                self.trading_day_time()

                minimum_investment = self.parameters['minimum_position_size_fraction'] * \
                                     self.initial_account_values['cashAvailableForTrading']
                maximum_investment = self.parameters['maximum_position_size_fraction'] * \
                                     self.initial_account_values['cashAvailableForTrading']

                self.target_capital_deployment = self.initial_account_values['cashAvailableForTrading'] * \
                                                 (self.seconds_from_open / (
                                                             self.seconds_from_open + self.seconds_to_close))
                self.actual_capital_deployment = self.initial_account_values['cashAvailableForTrading'] - \
                                                 self.current_account_values['cashAvailableForTrading']

                # the target capital takes us as close as possible to the target capital deployment
                self.target_capital = self.target_capital_deployment - self.actual_capital_deployment

                # check to see if we are below threshold for minimum investment
                if self.target_capital <= minimum_investment:
                    # check if the minimum investment is greater than available cash.
                    if self.current_account_values['cashAvailableForTrading'] < minimum_investment:
                        self.target_capital = self.current_account_values['cashAvailableForTrading']
                    else:
                        self.target_capital = minimum_investment
                elif self.target_capital >= maximum_investment:
                    # check if the maximum investment is greater than available cash.
                    if self.current_account_values['cashAvailableForTrading'] < maximum_investment:
                        self.target_capital = self.current_account_values['cashAvailableForTrading']
                    else:
                        self.target_capital = maximum_investment

                # build the position
                self.build_new_position()

            if self.threshold < self.parameters['Bollinger_top']:
                self.buy_armed = False

        if self.state is enums.StonksStrategyState.processing:
            pos: positions.Position
            for pos in self.positions:
                if pos.position_active:

                    # create buy orders
                    if pos.status is enums.StonksPositionState.needs_buy_order:
                        # if the position has an open order or multiple open orders, cancel all those orders
                        if pos.open_order or pos.multiple_open_orders:
                            order: orders_class.Order
                            for order in pos.order_list:
                                # delete any open orders
                                if order.is_open:
                                    self.utility_class.delete_order(order.order_id)

                        # enter strategy to buy here

                        # calculate limit value
                        # limit_price = pos
                        limit_price = pos.price_history[0]  # the original price of the option at trigger time.
                        # for now just do a market order

                        # calculate number of options contracts
                        number_of_options = pos.target_quantity

                        # TODO: revert to market order
                        # build purchase dictionary
                        payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                                   enums.OrderPayload.orderType.value: enums.OrderTypeOptions.MARKET.value,
                                   # enums.OrderPayload.orderType.value: enums.OrderTypeOptions.LIMIT.value,
                                   # enums.OrderPayload.price.value: limit_price,
                                   enums.OrderPayload.duration.value: enums.DurationOptions.DAY.value,
                                   enums.OrderPayload.quantity.value: number_of_options,
                                   enums.OrderPayload.orderLegCollection.value: [
                                       {
                                           enums.OrderLegCollectionDict.instruction.value: enums.InstructionOptions.BUY_TO_OPEN.value,
                                           enums.OrderLegCollectionDict.quantity.value: number_of_options,
                                           enums.OrderLegCollectionDict.instrument.value: {
                                               enums.InstrumentType.symbol.value: pos.symbol,
                                               enums.InstrumentType.assetType.value: enums.AssetTypeOptions.OPTION.value
                                           }

                                       }],
                                   enums.OrderPayload.orderStrategyType.value: enums.OrderStrategyTypeOptions.SINGLE.value,
                                   # enums.OrderPayload.orderId.value: int(np.random.random_integers(low=int(1e8),high=int(1e9),size=1)[0])
                                   }

                        if self.utility_class.place_order(payload=payload):
                            pos.status = enums.StonksPositionState.open_buy_order
                            pos.log_snapshot(self.position_log_directory)
                            continue

                        continue

                    # handle open buy orders
                    if pos.status is enums.StonksPositionState.open_buy_order:
                        # if the position has multiple open orders, cancel all those orders and ask for a new order
                        if pos.multiple_open_orders:
                            order: orders_class.Order
                            for order in pos.order_list:
                                # delete any open orders
                                if order.is_open:
                                    self.utility_class.delete_order(order.order_id)
                            pos.status = enums.StonksPositionState.needs_buy_order
                            pos.log_snapshot(self.position_log_directory)
                            continue

                        if self.verbose:
                            print('Position quantity is: {}'.format(int(pos.quantity)))
                        if not pos.open_order and int(pos.quantity) > 0.:
                            pos.status = enums.StonksPositionState.needs_stop_loss_order
                            pos.log_snapshot(self.position_log_directory)
                        elif not pos.open_order:
                            pos.status = enums.StonksPositionState.needs_buy_order
                            pos.log_snapshot(self.position_log_directory)

                        continue

    def build_new_position(self):
        '''
        build a position according to strategy, including strike price, intended limit price, quantity
        :return:
        '''

        if self.verbose: print('inside the new position building function')

        if self.parameters['option_type'] == enums.StonksOptionType.PUT:
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
                self.options_chain_dict = putExpDateMap[date_keys[0]]

        elif self.parameters['option_type'] == enums.StonksOptionType.CALL:
            payload = {'symbol': 'SPY',
                       'contractType': 'CALL',
                       'strikeCount': 20,
                       'includeQuotes': 'TRUE',
                       'strategy': 'SINGLE',
                       'fromDate': self.today.shift(days=-1).format('YYYY-MM-DD'),
                       'toDate': self.options_end_date.shift(days=1).format('YYYY-MM-DD')}

            self.options_chain_quote = self.utility_class.get_options_chain(payload=payload)

            callExpDateMap = self.options_chain_quote['callExpDateMap']
            date_keys = list(callExpDateMap.keys())
            if len(date_keys) > 1:
                self.callExpDateMap = None
                return False
            else:
                self.options_chain_dict = callExpDateMap[date_keys[0]]

        # now find the closest strike price to the strategy price
        strike_prices = []
        quote_prices = []
        for key in self.options_chain_dict.keys():
            strike_prices.append(self.options_chain_dict[key][0]['strikePrice'])
            quote_prices.append(self.options_chain_dict[key][0]['ask'])
        strike_prices = np.array(strike_prices)
        quote_prices = np.array(quote_prices)

        price_difference = np.abs(strike_prices - self.strike_price)
        min_price_difference = price_difference.min()

        self.best_strike_location = np.nonzero(price_difference == min_price_difference)[0][0]

        self.optoin_price = quote_prices[self.best_strike_location] * 100

        # check if this option is affordable
        if self.target_capital < self.optoin_price:
            # target option is too expensive, do not create it.
            if self.verbose: print(
                'target capital of {} could not afford options of price {}'.format(self.target_capital,
                                                                                   self.optoin_price))
            self.log_snapshot()
            return
        else:
            self.target_quantity = self.target_capital // self.optoin_price
            if self.verbose: print('target quantity for new position is: {}'.format(self.target_quantity))

        chosen_option_symbol = \
            self.options_chain_dict[list(self.options_chain_dict.keys())[self.best_strike_location]][0]['symbol']

        # underlying_security_quote = self.options_chain_dict['underlying']

        self.option_quote = self.utility_class.get_quote(symbol=chosen_option_symbol)
        underlying_symbol = self.option_quote['underlying']
        self.underlying_quote = self.utility_class.get_quote(symbol=underlying_symbol)

        self.positions.append(positions.Position(underlying_quote=self.option_quote,
                                                 quote_data=self.option_quote,
                                                 quantity=int(self.target_quantity)))

        # log the values for debugging purposes
        self.log_snapshot()
        time.sleep(.5)

    def hold_position(self):
        if self.state is enums.StonksStrategyState.triggering:
            # trigger add/reduce/sell here

            candle = self.analytics.compute[enums.ComputeKeys.candle]
            sma = self.analytics.compute[enums.ComputeKeys.sma][0]
            sma_short = self.analytics.compute[enums.ComputeKeys.sma][1]
            bollinger_down, bollinger_up = self.analytics.compute[enums.ComputeKeys.Bollinger][0]

            self.threshold = 2 * (sma_short[-1] - sma[-1]) / np.absolute(bollinger_up[-1] - bollinger_down[-1])

            ########################################### trigger sell position ##########################################
            if self.threshold < self.parameters['Bollinger_bot']:
                self.sell_armed = True

            if self.sell_armed and self.threshold >= self.parameters['Bollinger_bot']:
                pos: positions.Position
                for pos in self.positions:
                    if pos.position_active:
                        if pos.status is not enums.StonksPositionState.open_close_order:
                            pos.status = enums.StonksPositionState.needs_close_order

            if self.threshold > self.parameters['Bollinger_bot']:
                self.sell_armed = False

            ########################################### profit trigger sell position ###################################
            pos: positions.Position
            for pos in self.positions:
                if pos.position_active:
                    if pos.percent_gain is not None:
                        if pos.percent_gain > 1.60:
                            if pos.status is not enums.StonksPositionState.open_close_order:
                                pos.status = enums.StonksPositionState.needs_close_order

        if self.state is enums.StonksStrategyState.processing:
            # ensure a stop-loss is in

            for pos in self.positions:
                if pos.position_active:

                    ####################################################################################################
                    if pos.status is enums.StonksPositionState.needs_stop_loss_order:
                        # if the position has an open order or multiple open orders, cancel all those orders
                        if pos.open_order or pos.multiple_open_orders:
                            order: orders_class.Order
                            for order in pos.order_list:
                                # delete any open orders
                                if order.is_open:
                                    self.utility_class.delete_order(order.order_id)

                        # enter strategy to buy here

                        # calculate limit value
                        stop_price_offset = np.max(pos.price_history) * self.parameters['stop_loss']

                        stop_price_offset = math.trunc(stop_price_offset * 100.) / 100.

                        print('stop_price_offset is: {}'.format(stop_price_offset))

                        # calculate number of options contracts
                        number_of_options = int(pos.quantity)

                        print('number_of_options is: {}'.format(number_of_options))

                        # build purchase dictionary
                        payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                                   # TODO: revert back to stop order
                                   enums.OrderPayload.orderType.value: enums.OrderTypeOptions.STOP.value,
                                   enums.OrderPayload.stopPrice.value: stop_price_offset,
                                   enums.OrderPayload.duration.value: enums.DurationOptions.DAY.value,
                                   enums.OrderPayload.quantity.value: number_of_options,
                                   enums.OrderPayload.orderLegCollection.value: [
                                       {
                                           enums.OrderLegCollectionDict.instruction.value: enums.InstructionOptions.SELL_TO_CLOSE.value,
                                           enums.OrderLegCollectionDict.quantity.value: number_of_options,
                                           enums.OrderLegCollectionDict.instrument.value: {
                                               enums.InstrumentType.symbol.value: pos.symbol,
                                               enums.InstrumentType.assetType.value: enums.AssetTypeOptions.OPTION.value
                                           }

                                       }],
                                   enums.OrderPayload.orderStrategyType.value: enums.OrderStrategyTypeOptions.SINGLE.value,
                                   # enums.OrderPayload.orderId.value: np.random.random_integers(low=int(1e8),high=int(1e9),size=1)
                                   }

                        if self.utility_class.place_order(payload=payload):
                            pos.last_stop_loss_update_time = arrow.now('America/New_York')
                            pos.status = enums.StonksPositionState.open_stop_loss_order
                            pos.log_snapshot(self.position_log_directory)
                            continue

                        continue

                    if pos.status is enums.StonksPositionState.open_stop_loss_order:
                        if pos.multiple_open_orders:
                            order: orders_class.Order
                            for order in pos.order_list:
                                # delete any open orders
                                if order.is_open:
                                    self.utility_class.delete_order(order.order_id)
                            pos.status = enums.StonksPositionState.needs_close_order
                            pos.log_snapshot(self.position_log_directory)
                            continue

                        if pos.open_order:
                            # update stoploss every 10 minutes
                            delta_t = arrow.now('America/New_York') - pos.last_stop_loss_update_time
                            if delta_t.seconds > 5 * 60:
                                pos.status = enums.StonksPositionState.needs_stop_loss_order
                            continue

                        if not pos.open_order:
                            # de-activate position if the order filled, implicitly this is true if it is no longer active..
                            # Needs an explicit check though. If not, ask for a close order to the position.
                            pos.de_activate_position()
                            if pos.position_active:
                                pos.status = enums.StonksPositionState.needs_close_order
                                pos.log_snapshot(self.position_log_directory)
                            continue

                        continue

    def expand_position(self):
        if self.state is enums.StonksStrategyState.triggering:
            # put in functionality here, otherwise just ensure that a stoploss is in.
            pass
        if self.state is enums.StonksStrategyState.processing:
            pass

    def reduce_position(self):
        if self.state is enums.StonksStrategyState.triggering:
            # put in functionality here, otherwise just ensure that a stoploss is in.
            pass
        if self.state is enums.StonksStrategyState.processing:
            pass

    def sell_position(self):
        if self.state is enums.StonksStrategyState.triggering:
            pass

        if self.state is enums.StonksStrategyState.processing:
            pos: positions.Position
            for pos in self.positions:
                if pos.position_active:

                    if pos.status is enums.StonksPositionState.needs_close_order:
                        # if the position has an open order or multiple open orders, cancel all those orders
                        if pos.open_order or pos.multiple_open_orders:
                            order: orders_class.Order
                            for order in pos.order_list:
                                # delete any open orders
                                if order.is_open:
                                    self.utility_class.delete_order(order.order_id)

                        # calculate number of options contracts
                        number_of_options = int(pos.quantity)

                        print('number_of_options is: {}'.format(number_of_options))

                        # build purchase dictionary
                        payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                                   # TODO: revert back to stop order
                                   enums.OrderPayload.orderType.value: enums.OrderTypeOptions.MARKET.value,
                                   enums.OrderPayload.duration.value: enums.DurationOptions.DAY.value,
                                   enums.OrderPayload.quantity.value: number_of_options,
                                   enums.OrderPayload.orderLegCollection.value: [
                                       {
                                           enums.OrderLegCollectionDict.instruction.value: enums.InstructionOptions.SELL_TO_CLOSE.value,
                                           enums.OrderLegCollectionDict.quantity.value: number_of_options,
                                           enums.OrderLegCollectionDict.instrument.value: {
                                               enums.InstrumentType.symbol.value: pos.symbol,
                                               enums.InstrumentType.assetType.value: enums.AssetTypeOptions.OPTION.value
                                           }

                                       }],
                                   enums.OrderPayload.orderStrategyType.value: enums.OrderStrategyTypeOptions.SINGLE.value,
                                   # enums.OrderPayload.orderId.value: np.random.random_integers(low=int(1e8),high=int(1e9),size=1)
                                   }

                        if self.utility_class.place_order(payload=payload):
                            pos.last_stop_loss_update_time = arrow.now('America/New_York')
                            pos.status = enums.StonksPositionState.open_close_order
                            pos.log_snapshot(self.position_log_directory)
                            continue

                    if pos.status is enums.StonksPositionState.open_close_order:
                        if pos.multiple_open_orders:
                            order: orders_class.Order
                            for order in pos.order_list:
                                # delete any open orders
                                if order.is_open:
                                    self.utility_class.delete_order(order.order_id)
                            pos.status = enums.StonksPositionState.needs_close_order
                            pos.log_snapshot(self.position_log_directory)
                            continue
                        elif not pos.open_order:
                            # de-activate position if the order filled, implicitly this is true if it is no longer active..
                            # Needs an explicit check though. If not, ask for a close order to the position.
                            pos.de_activate_position()
                            pos.log_snapshot(self.position_log_directory)
                            if pos.position_active:
                                pos.status = enums.StonksPositionState.needs_close_order
                                pos.log_snapshot(self.position_log_directory)
                            continue

    def position_triggers(self):
        '''
        This function contains triggers for modifying the state of the position.

        Self-consistency is handled by the align orders function.

        Modifies the state of each position or creates a position if it does not exist.
        Maps positions from one state to another..

        :return:
        '''

        ########################################### trigger new position ###############################################
        open_position = False
        position: positions.Position
        for position in self.positions:
            if position.position_active:
                open_position = True

        candle = self.analytics.compute[enums.ComputeKeys.candle]
        sma = self.analytics.compute[enums.ComputeKeys.sma][0]
        sma_short = self.analytics.compute[enums.ComputeKeys.sma][1]
        bollinger_up, bollinger_down = self.analytics.compute[enums.ComputeKeys.Bollinger][0]

        self.threshold = 2 * (sma_short[-1] - sma[-1]) / np.absolute(bollinger_up[-1] - bollinger_down[-1])

        if self.threshold > self.parameters['Bollinger_top']:
            self.buy_armed = True

        if self.buy_armed and self.threshold <= self.parameters['Bollinger_top'] and not open_position:
            strike_delta = self.parameters['price_multiplier'] * (candle[-1] - bollinger_down[-1])
            if strike_delta >= self.parameters['max_strike_delta']:
                strike_delta = self.parameters['max_strike_delta']

            # define strike price
            self.strike_price = candle[-1] - strike_delta

            # build the position
            self.build_new_position()

        if self.threshold < self.parameters['Bollinger_top']:
            self.buy_armed = False

        ########################################### trigger sell position ##############################################
        if self.threshold < self.parameters['Bollinger_bot']:
            self.sell_armed = True

        if self.sell_armed and self.threshold >= self.parameters['Bollinger_bot']:
            pos: positions.Position
            for pos in self.positions:
                if pos.position_active:
                    if pos.status is not enums.StonksPositionState.open_close_order:
                        pos.status = enums.StonksPositionState.needs_close_order

        if self.threshold > self.parameters['Bollinger_bot']:
            self.sell_armed = False

        ########################################### trigger update stop_loss ###########################################

        # update stoploss every 10 minutes
        for pos in self.positions:
            if pos.position_active:
                if pos.status is enums.StonksPositionState.open_stop_loss_order:
                    delta_t = arrow.now('America/New_York') - pos.last_stop_loss_update_time
                    if delta_t.seconds > 5 * 60:
                        pos.status = enums.StonksPositionState.needs_stop_loss_order

    def align_orders(self):
        '''
        This function aligns orders with position states and vice versa. Ensures a complete handling of all states.

        This function, along with the place orders function contains a complete mapping of position states onto other
        position states, and ensures self consistent behavior. Critically, there are no strategy triggers in either
        function.

        orders should be in line with position states.

        This function prevents multiple orders from existing.

        This function deletes current orders in preparation for new orders. By default, all old orders are deleted if
        they are open.

        This function determines the priority of states.

        By default, closing orders have priority over opening orders

        :return:
        '''
        pos: positions.Position
        for pos in self.positions:
            if pos.position_active:
                ########################################### needs_[order] conditions####################################
                # basically delete all open orders if the program specifies a new order is required

                if pos.status is enums.StonksPositionState.needs_buy_order:
                    # if the position has an open order or multiple open orders, cancel all those orders
                    if pos.open_order or pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)

                    continue

                if pos.status is enums.StonksPositionState.needs_add_order:
                    # if the position has an open order or multiple open orders, cancel all those orders
                    if pos.open_order or pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)

                    continue

                if pos.status is enums.StonksPositionState.needs_stop_loss_order:
                    # if the position has an open order or multiple open orders, cancel all those orders
                    if pos.open_order or pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)

                    continue

                if pos.status is enums.StonksPositionState.needs_reduce_order:
                    # if the position has an open order or multiple open orders, cancel all those orders
                    if pos.open_order or pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)

                    continue

                if pos.status is enums.StonksPositionState.needs_close_order:
                    # if the position has an open order or multiple open orders, cancel all those orders
                    if pos.open_order or pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)

                    continue

                ########################################### open_[]_order conditions####################################
                # force contradictory orders to be canceled. Only 1 order is possible
                # default is call for a stop_loss_order unless a close order is required, this ensures protection
                if pos.status is enums.StonksPositionState.open_buy_order:
                    # if the position has multiple open orders, cancel all those orders and ask for a new order
                    if pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)
                        pos.status = enums.StonksPositionState.needs_buy_order
                        continue
                    elif not pos.open_order and pos.quantity != 0:
                        pos.status = enums.StonksPositionState.needs_stop_loss_order
                        continue

                if pos.status is enums.StonksPositionState.open_add_order:
                    if pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)
                        pos.status = enums.StonksPositionState.needs_buy_order
                        continue
                    elif not pos.open_order:
                        pos.status = enums.StonksPositionState.needs_stop_loss_order
                        continue

                if pos.status is enums.StonksPositionState.open_stop_loss_order:
                    if pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)
                        pos.status = enums.StonksPositionState.needs_close_order
                        continue
                    elif not pos.open_order:
                        # de-activate position if the order filled, implicitly this is true if it is no longer active..
                        # Needs an explicit check though. If not, ask for a close order to the position.
                        pos.de_activate_position()
                        if pos.position_active:
                            pos.status = enums.StonksPositionState.needs_close_order
                        continue

                if pos.status is enums.StonksPositionState.open_reduce_order:
                    if pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)
                        pos.status = enums.StonksPositionState.needs_buy_order
                        continue
                    elif not pos.open_order:
                        pos.status = enums.StonksPositionState.needs_stop_loss_order
                        continue

                if pos.status is enums.StonksPositionState.open_close_order:
                    if pos.multiple_open_orders:
                        order: orders_class.Order
                        for order in pos.order_list:
                            # delete any open orders
                            if order.is_open:
                                self.utility_class.delete_order(order.order_id)
                        pos.status = enums.StonksPositionState.needs_close_order
                        continue
                    elif not pos.open_order:
                        # de-activate position if the order filled, implicitly this is true if it is no longer active..
                        # Needs an explicit check though. If not, ask for a close order to the position.
                        pos.de_activate_position()
                        if pos.position_active:
                            pos.status = enums.StonksPositionState.needs_close_order
                        continue

    def place_orders(self):
        '''
        Iterate through each position and place orders according to position states

        This takes positions from 'needs_orders' to 'open_orders' conditions

        :return:
        '''
        pos: positions.Position
        for pos in self.positions:
            if pos.position_active:

                if pos.status is enums.StonksPositionState.needs_stop_loss:
                    # enter strategy to buy here

                    # calculate limit value
                    limit_price = np.max(pos.price_history) * self.parameters['stop_loss']

                    # calculate number of options contracts
                    number_of_options = pos.quantity

                    # build purchase dictionary
                    payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                               enums.OrderPayload.orderType.value: enums.OrderTypeOptions.STOP.value,
                               enums.OrderPayload.price.value: limit_price,
                               enums.OrderPayload.duration.value: enums.DurationOptions.DAY.value,
                               enums.OrderPayload.quantity.value: number_of_options,
                               enums.OrderPayload.orderLegCollection.value: [
                                   {
                                       enums.OrderLegCollectionDict.instruction.value: enums.InstructionOptions.SELL_TO_CLOSE.value,
                                       enums.OrderLegCollectionDict.quantity.value: number_of_options,
                                       enums.OrderLegCollectionDict.instrument.value: {
                                           enums.InstrumentType.symbol.value: pos.symbol,
                                           enums.InstrumentType.assetType.value: enums.AssetTypeOptions.OPTION.value
                                       }

                                   }],
                               enums.OrderPayload.orderStrategyType.value: enums.OrderStrategyTypeOptions.SINGLE.value,
                               enums.OrderPayload.orderId.value: np.random.random_integers(low=int(1e8), high=int(1e9),
                                                                                           size=1)}

                    if self.utility_class.place_order(payload=payload):
                        pos.last_stop_loss_update_time = arrow.now('America/New_York')
                        pos.status = enums.StonksPositionState.open_stop_loss_order

                if pos.status is enums.StonksPositionState.needs_buy_order:
                    # enter strategy to buy here

                    # calculate limit value
                    # limit_price = pos
                    # for now just do a market order

                    # calculate number of options contracts
                    number_of_options = None

                    # build purchase dictionary
                    payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                               enums.OrderPayload.orderType.value: enums.OrderTypeOptions.MARKET.value,
                               # enums.OrderPayload.price.value: limit_price,
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
                        pos.status = enums.StonksPositionState.open_buy_order

                if pos.status is enums.StonksPositionState.needs_add_order:
                    # not used by this strategy
                    pass

                if pos.status is enums.StonksPositionState.needs_reduce_order:
                    # not used by this strategy
                    pass

                if pos.status is enums.StonksPositionState.needs_close_order:
                    # enter strategy to sell here

                    # calculate limit value
                    # limit_price = None

                    # calculate number of options contracts
                    number_of_options = pos.quantity

                    # build purchase dictionary
                    payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                               enums.OrderPayload.orderType.value: enums.OrderTypeOptions.MARKET.value,
                               # enums.OrderPayload.price.value: limit_price,
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
                        pos.status = enums.StonksPositionState.open_close_order

    def run_strategy(self):
        '''
        Implement the strategy at each timestep
        :param kwargs:
        :return:
        '''

        self.set_up_data_logging()
        self.log_snapshot()
        log_start = arrow.now('America/New_York').floor('minute')

        new_minute = arrow.now('America/New_York').floor('minute')
        update_minute_clock = True
        while True:
            # trigger on the minute, every minute, when the new candle is available.

            # update time
            self.trading_day_time()

            # log the state every 30 min
            log_timer = arrow.now('America/New_York').floor('minute') - log_start
            if int(log_timer.seconds) == 60 * 30:
                self.log_snapshot()

            # set the new minute.
            if update_minute_clock:
                new_minute = arrow.now('America/New_York').floor('minute')
                update_minute_clock = False

            # compute the elapsed time and trigger 5 seconds into the new minute.
            elapsed_time = arrow.now('America/New_York') - new_minute
            if self.verbose: print('Elapsed time since last trigger minute: {}'.format(elapsed_time.seconds))
            if elapsed_time.seconds > 65:
                # implement the algorithm

                # reset loop clock
                update_minute_clock = True

                # check if a new refresh token is required, update if so..
                self.utility_class.update_access_token()

                # update the analysis
                self.update_analytics()

                # record options quote for posterity
                # self.log_options_chain()

                # set the state to cause triggered behavior
                self.state = enums.StonksStrategyState.triggering

            # update account information, explicit call here to the account api
            self.get_current_account_values()

            # update positions and orders in those positions to reflect account value
            self.update_positions()

            # stop trading if account value incurs too much loss..
            if self.check_stop_trading():
                self.close_all_positions()
                # needs another function to end activity
            else:
                # build/add to positions
                self.create_position()
                self.hold_position()
                self.expand_position()
                self.reduce_position()
                self.sell_position()

            # set the state to resolve processing
            self.state = enums.StonksStrategyState.processing
            # Wait to redo loop every 20 seconds
            time.sleep(10)
