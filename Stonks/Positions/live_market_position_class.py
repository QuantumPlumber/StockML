import numpy as np
import arrow
import os
import inspect
import time

from Stonks import global_enums as enums
from Stonks.Orders import orders_class as orders


class Position:
    def __init__(self, underlying_quote: dict, quote_data: dict, quantity: int):

        # save all quote data passed in
        self.underlying_quote = []
        self.underlying_quote.append(underlying_quote)
        self.quote_data = []
        self.quote_data.append(quote_data)

        # define the option
        self.type = quote_data['contractType']
        self.expiration = arrow.Arrow(day=quote_data['expirationDay'],
                                      month=quote_data['expirationMonth'],
                                      year=quote_data['expirationYear'],
                                      tzinfo='America/New_York')
        self.strike_price = quote_data['strikePrice']
        self.symbol = quote_data['symbol']
        self.underlying_symbol = underlying_quote['symbol']
        self.target_quantity = quantity

        # define prices and initialize lists to hold price data
        self.stock_price_at_trigger = underlying_quote['lastPrice']

        # strictly for holding prices when position is bought
        self.price_history = []
        self.price_history.append(quote_data['lastPrice'])
        self.value_history = []
        self.value_history.append(None)

        # enumerated states of the option for buying, adding, reducing and selling position.
        self.status = enums.StonksPositionState.needs_buy_order
        self.position_active = True

        # tracking orders and order status:
        self.open_order = None
        self.multiple_open_orders = None
        self.buy_order_exists = None
        self.sell_order_exists = None
        self.orders_consistent = None
        self.order_list = []

        # track position data from accounts api
        self.position_data = []
        self.position_data.append(None)
        self.quantity = 0
        self.average_price = None
        self.currentDayProfitLossPercentage = None
        self.stop_loss_limit = None
        self.last_stop_loss_update_time = None

    def log_snapshot(self, log_directory):

        metadata_name = self.symbol + '_' + arrow.now('America/New_York').format('YYYY-MM-DD_HH-mm-ss') + '.txt'
        metadata_path = log_directory + metadata_name
        if not os.path.isfile(metadata_path):
            metadata = open(metadata_path, 'a+', buffering=1)
        else:
            metadata_name = self.symbol + '_B_' + arrow.now('America/New_York').format('YYYY-MM-DD_HH-mm-ss') + '.txt'
            metadata_path = log_directory + metadata_name
            metadata = open(metadata_path, 'a+', buffering=1)

        attributes = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        writeable = [a for a in attributes if not (a[0].startswith('__') and a[0].endswith('__'))]

        for element in writeable:
            metadata.write(str(element) + '\n')

        time.sleep(1)

    def update_price_and_value(self, underlying_quote: dict, quote_data: dict, position_data: dict):
        self.underlying_quote.append(underlying_quote)

        self.quote_data.append(quote_data)
        self.price_history.append(quote_data['lastPrice'])

        self.position_data.append(position_data)
        self.value_history.append(position_data['marketValue'])
        self.quantity = position_data['longQuantity']
        self.average_price = position_data['averagePrice']
        self.currentDayProfitLossPercentage = position_data['currentDayProfitLossPercentage']

    def update_orders(self, order_payload_list: list):
        for order_payload in order_payload_list:
            order_already_recorded = False
            order: orders.Order
            for order in self.order_list:
                # update order if it has a corresponding id
                #print(order.order_id)
                #print(order_payload[enums.OrderPayload.orderId.value])
                if int(order.order_id) == int(order_payload[enums.OrderPayload.orderId.value]):
                    order_already_recorded = True
                    order.update(order_dict=order_payload)
            if not order_already_recorded:
                # create the order
                order = orders.Order(order_dict=order_payload)
                order.update(order_dict=order_payload)
                self.order_list.append(order)

        # check consistency of orders
        self.check_order_stati()

    def track_open_order_time(self, time: arrow.Arrow):
        open_times = []
        order: orders.Order
        for order in self.order_list:
            if order.is_open:
                open_times.append(order.time_since_last_update())
        return open_times

    def check_order_stati(self):
        self.num_open_orders = 0
        self.buy_order_exists = False
        self.sell_order_exists = False
        order: orders.Order
        for order in self.order_list:
            if order.is_open:
                self.open_order = True
                self.num_open_orders += 1

                if order.order_instruction == enums.InstructionOptions.BUY_TO_OPEN.value:
                    self.buy_order_exists = True
                if order.order_instruction == enums.InstructionOptions.SELL_TO_CLOSE.value:
                    self.sell_order_exists = True

        if self.num_open_orders == 0:
            self.open_order = False


        if self.num_open_orders > 1:
            self.multiple_open_orders = True
        else:
            self.multiple_open_orders = False

        if self.buy_order_exists and self.sell_order_exists:
            self.orders_consistent = False
        else:
            self.orders_consistent = True


    def de_activate_position(self):
        '''
        Function for attempting to set the position in the inactive state
        :param option_price:
        :return:
        '''
        self.check_order_stati()
        if not self.open_order and self.orders_consistent and self.quantity == 0:
            self.position_active = False



if __name__ == "__main__":
    pass
