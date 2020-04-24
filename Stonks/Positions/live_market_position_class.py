import numpy as np
import arrow

from Stonks import global_enums as enums
from Stonks.Orders import orders_class as orders


class Position:
    def __init__(self, underlying_quote: dict, quote_data: dict):

        # save all quote data passed in
        self.underlying_quote = []
        self.underlying_quote.append(underlying_quote)
        self.quote_data = []
        self.quote_data.append(quote_data)

        # define the option
        self.type = quote_data['putCall']
        self.expiration = quote_data['expirationDate']
        self.strike_price = quote_data['strikePrice']
        self.symbol = quote_data['symbol']
        self.underlying_symbol = underlying_quote['symbol']

        # define prices and initialize lists to hold price data
        self.stock_price_at_trigger = underlying_quote['ask']  # use the ask as the initial price of the option

        # strictly for holding prices when position is bought
        self.price_history = []
        self.value_history = []

        # enumerated states of the option for buying, adding, reducing and selling position.
        self.status = None
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
        self.quantity = None
        self.average_price = None
        self.currentDayProfitLossPercentage = None

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
        if len(self.order_list) > 0:
            for order_payload in order_payload_list:
                order: orders.Order
                for order in self.order_list:
                    # update order if it has a corresponding id
                    if order.order_id == order_payload[enums.OrderPayload.orderId.value()]:
                        order.update(order_dict=order_payload)
                    else:
                        # create the order
                        self.order_list.append(orders.Order(order_dict=order_payload))
        else:
            # if no orders exist then create new orders
            for order_payload in order_payload_list:
                self.order_list.append(orders.Order(order_dict=order_payload))

        # check consistency of orders
        self.check_order_stati()

        # check if the position meets definition for being closed
        self.de_activate_position()

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

                if order.order_instruction == enums.InstructionOptions.BUY_TO_OPEN.value():
                    self.buy_order_exists = True
                if order.order_instruction == enums.InstructionOptions.SELL_TO_CLOSE.value():
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
