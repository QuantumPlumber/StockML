import script_context

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

from Stonks.Orders import orders_class

from Stonks.utilities.utility_class import UtilityClass

importlib.reload(UtilityClass)

from Stonks.utilities import utility_exceptions

from Stonks.Strategies import putSlingerBollinger_conditions


class Strategy():
    def __init__(self, **kwargs):
        # symbol to trade
        self.symbol = kwargs['symbol']

        # utility class to handle API functions
        self.utility_class = UtilityClass(verbose=True)

        # analysis class to handle data analysis
        self.compute_dict = kwargs['compute_dict']
        self.analytics = Analytics_class.analysis(compute_dict=self.compute_dict)

        # timing and dates
        self.today = arrow.now('America/New_York')
        self.today = self.today.replace(hour=0, minute=0, second=0, microsecond=0)
        self.get_options_end_date()
        self.current_minute = self.trading_day_minute()

        # save initial account values
        self.initial_account_values = self.get_current_account_values()

        # positions list
        self.positions = []

        # strategy parameters and variables
        self.parameters = kwargs['parameters']
        self.buy_armed = False
        self.sell_armed = False

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
        price_history = self.utility_class.get_price_history(symbol=self.symbol, payload=payload)
        self.analytics.compute_analytics(data=price_history)

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
        self.percent_lost = 1. - self.current_account_values['liquidationValue'] / self.initial_account_values[
            'liquidationValue']

        if self.percent_lost >= .2:
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
        positions_dict = self.utility_class.get_account_positions()

        # get orders dict for this account and prepare it
        # get orders for today only.
        payload = {'maxResults': 1000,
                   'fromEnteredTime': arrow.now('America/New_York').format('YYYY-MM-DD'),
                   'toEnteredTime': arrow.now('America/New_York').format('YYYY-MM-DD')}
        account_orders_list = self.utility_class.get_orders(payload=payload)

        # iterate through positions
        pos: positions.Position
        for pos in self.positions:
            for account_position in positions_dict['positions']:
                # only work on open positions
                if pos.symbol == account_position['instrument']['symbol']:
                    option_quote = self.utility_class.get_quote(symbol=pos.symbol)
                    underlying_quote = self.utility_class.get_quote(symbol=pos.underlying_symbol)
                    pos.update_price_and_value(underlying_quote=underlying_quote,
                                               quote_data=option_quote,
                                               position_data=account_position)

            # update orders for all positions
            # first collect all orders related to this position
            local_order_list = []
            for order in account_orders_list:
                if order[enums.OrderLegCollectionDict.instrument.value()]['symbol'] == pos.symbol:
                    local_order_list.append(order)
            pos.update_orders(order_payload_list=local_order_list)

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

        candle = self.analytics.data['candle']
        sma = self.analytics.data['sma'][0]
        sma_short = self.analytics.data['sma'][1]
        bollinger_up, bollinger_down = self.analytics.data['Bollinger'][0]

        threshold = 2 * (sma_short[-1] - sma[-1]) / np.absolute(bollinger_up[-1] - bollinger_down[-1])

        if threshold > self.parameters['Bollinger_top']:
            self.buy_armed = True

        if self.buy_armed and threshold <= self.parameters['Bollinger_top'] and not open_position:
            strike_delta = self.parameters['price_multiplier'] * (candle[-1] - bollinger_down[-1])
            if strike_delta >= self.parameters['max_strik_delta']:
                strike_delta = self.parameters['max_strik_delta']

            # define strike price
            self.strike_price = candle[-1] - strike_delta

            # build the position
            self.build_new_position()

        if threshold < self.parameters['Bollinger_top']:
            self.buy_armed = False

        ########################################### trigger sell position ##############################################
        if threshold < self.parameters['Bollinger_bot']:
            self.sell_armed = True

        if self.sell_armed and threshold >= self.parameters['Bollinger_bot']:
            pos: positions.Position
            for pos in self.positions:
                if pos.position_active:
                    if pos.status is not enums.StonksPositionState.open_close_order:
                        pos.status = enums.StonksPositionState.needs_close_order

        if threshold > self.parameters['Bollinger_bot']:
            self.sell_armed = False

        ########################################### trigger update stop_loss ###########################################

        #update stoploss every 10 minutes
        for pos in self.positions:
            if pos.position_active:
                if pos.status is enums.StonksPositionState.open_stop_loss_order:
                    delta_t = arrow.now('America/New_York') - pos.last_stop_loss_update_time
                    if delta_t.seconds > 5*60:
                        pos.status = enums.StonksPositionState.needs_stop_loss_order

    def build_new_position(self):
        '''
        build a position according to strategy, including strike price, intended limit price, quantity
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
        best_strike_location = np.where(price_difference == min_price_difference)[0]

        chosen_option_quote = self.options_chain_dict[
            list(self.options_chain_dict.keys())[best_strike_location]
        ]
        underlying_security_quote = self.options_chain_dict['underlying']

        self.positions.append(positions.Position(parameters=self.parameters,
                                                 underlying_quote=underlying_security_quote,
                                                 quote_data=chosen_option_quote,
                                                 ))

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
                        pos.status = enums.StonksPositionState.open_buy_order

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
                               #enums.OrderPayload.price.value: limit_price,
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

                # update positions and orders in those positions to reflect account value
                self.update_positions()

                # stop trading if account value incurs too much loss..
                if self.check_stop_trading():
                    self.close_all_positions()
                    self.switch_position_state()
                    self.place_orders()
                    break
                else:
                    # build/add to positions
                    self.trigger_new_position()  # triggering changes state
                    self.switch_position_state()  # align order after triggering
                    self.place_orders()  # placing orders changes state
