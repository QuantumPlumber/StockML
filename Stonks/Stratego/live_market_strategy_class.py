import script_context

import numpy as np
import pandas as pd
import os
import h5py
import arrow
import matplotlib.pyplot as plt
import importlib
import time

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

        # symbol to trade
        self.symbol = kwargs['symbol']

        # utility class to handle API functions
        self.utility_class = utility_class.UtilityClass(verbose=False)
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

        self.get_current_account_values()

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

        for account_position in self.account_positions:
            position_found = False
            # iterate through positions
            pos: positions.Position
            for pos in self.positions:
                # only work on open positions
                if pos.symbol == account_position['instrument']['symbol'] and pos.position_active:
                    self.option_quote = self.utility_class.get_quote(symbol=pos.symbol)
                    self.underlying_quote = self.utility_class.get_quote(symbol=pos.underlying_symbol)
                    pos.update_price_and_value(underlying_quote=self.underlying_quote,
                                               quote_data=self.option_quote,
                                               position_data=account_position)
                    position_found = True
                # if there are no matching open positions, create a new position..

            if not position_found:
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

                self.positions.append(new_position)
            '''
            # if there are no positions, create a new position..
            if len(self.positions) == 0:
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

                self.positions.append(new_position)
            '''

        # iterate through positions
        pos: positions.Position
        for pos in self.positions:
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
            bollinger_up, bollinger_down = self.analytics.compute[enums.ComputeKeys.Bollinger][0]

            self.threshold = 2 * (sma_short[-1] - sma[-1]) / np.absolute(bollinger_up[-1] - bollinger_down[-1])

            ########################################### trigger new position ###########################################

            if self.threshold > self.parameters['Bollinger_top']:
                self.buy_armed = True

            # TODO: revert to previous condition
            # if self.buy_armed and self.threshold <= self.parameters['Bollinger_top'] and not self.open_position:
            if True:
                strike_delta = self.parameters['price_multiplier'] * (candle[-1] - bollinger_down[-1])
                if strike_delta >= self.parameters['max_strike_delta']:
                    strike_delta = self.parameters['max_strike_delta']

                # define strike price
                self.strike_price = candle[-1] - strike_delta

                #################################### Compute capital for new position ################################

                self.get_current_account_values()
                self.trading_day_time()

                minimum_investment = self.parameters['minimum_position_size_fraction'] * \
                                     self.initial_account_values['cashAvailableForTrading']
                expected_current_cash = self.initial_account_values['cashAvailableForTrading'] * \
                                        (self.seconds_to_close / (self.seconds_from_open + self.seconds_to_close))
                self.target_capital = self.current_account_values['cashAvailableForTrading'] - expected_current_cash

                # check to see if we are below threshold for minimum investment
                if self.target_capital <= minimum_investment:
                    # check if the minimum investment is greater than available cash.
                    if self.current_account_values['cashAvailableForTrading'] < minimum_investment:
                        self.target_capital = self.current_account_values['cashAvailableForTrading']
                    else:
                        self.target_capital = minimum_investment

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
                                   # enums.OrderPayload.orderType.value: enums.OrderTypeOptions.MARKET.value,
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
                                   # enums.OrderPayload.orderId.value: int(np.random.random_integers(low=int(1e8),high=int(1e9),size=1)[0])
                                   }

                        if self.utility_class.place_order(payload=payload):
                            pos.status = enums.StonksPositionState.open_buy_order
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
                            continue

                        if not pos.open_order:
                            pos.status = enums.StonksPositionState.needs_buy_order
                            continue

                        elif not pos.open_order and pos.quantity != 0:
                            pos.status = enums.StonksPositionState.needs_stop_loss_order
                            continue

    def build_new_position(self):
        '''
        build a position according to strategy, including strike price, intended limit price, quantity
        :return:
        '''

        if self.verbose: print('inside the new position building function')

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

        # check if this option is affordable
        if self.target_capital < quote_prices[self.best_strike_location] * 100:
            # target option is too expensive, do not create it.
            return
        else:
            target_quantity = self.target_capital // (quote_prices[self.best_strike_location] * 100)

        chosen_option_symbol = \
            self.options_chain_dict[list(self.options_chain_dict.keys())[self.best_strike_location]][0]['symbol']

        # underlying_security_quote = self.options_chain_dict['underlying']

        self.option_quote = self.utility_class.get_quote(symbol=chosen_option_symbol)
        underlying_symbol = self.option_quote['underlying']
        self.underlying_quote = self.utility_class.get_quote(symbol=underlying_symbol)

        self.positions.append(positions.Position(underlying_quote=self.option_quote,
                                                 quote_data=self.option_quote,
                                                 quantity=int(target_quantity)))

    def hold_position(self):
        if self.state is enums.StonksStrategyState.triggering:
            # trigger add/reduce/sell here

            candle = self.analytics.compute[enums.ComputeKeys.candle]
            sma = self.analytics.compute[enums.ComputeKeys.sma][0]
            sma_short = self.analytics.compute[enums.ComputeKeys.sma][1]
            bollinger_up, bollinger_down = self.analytics.compute[enums.ComputeKeys.Bollinger][0]

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
                                   # enums.OrderPayload.orderId.value: np.random.random_integers(low=int(1e8),high=int(1e9),size=1)
                                   }

                        if self.utility_class.place_order(payload=payload):
                            pos.last_stop_loss_update_time = arrow.now('America/New_York')
                            pos.status = enums.StonksPositionState.open_stop_loss_order

                    if pos.status is enums.StonksPositionState.open_stop_loss_order:

                        # update stoploss every 10 minutes
                        delta_t = arrow.now('America/New_York') - pos.last_stop_loss_update_time
                        if delta_t.seconds > 5 * 60:
                            pos.status = enums.StonksPositionState.needs_stop_loss_order

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

    def implement_strategy(self, **kwargs):
        '''
        Implement the strategy at each timestep
        :param kwargs:
        :return:
        '''

        new_minute = arrow.now('America/New_York').floor('minute')
        update_minute_clock = True
        while True:
            # trigger on the minute, every minute, when the new candle is available.

            # set the new minute.
            if update_minute_clock:
                new_minute = arrow.now('America/New_York').floor('minute')
                update_minute_clock = False

            # compute the elapsed time and trigger 5 seconds into the new minute.
            elapsed_time = new_minute - arrow.now('America/New_York')
            if elapsed_time.seconds > 65:
                # implement the algorithm

                # reset loop clock
                update_minute_clock = True

                # check if a new refresh token is required, update if so..
                self.utility_class.update_access_token()

                # update the analysis
                self.update_analytics()

                # set the state to cause triggered behavior
                self.state = enums.StonksStrategyState.triggering

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
            time.sleep(20)
