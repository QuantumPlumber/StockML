import numpy as np
import arrow

from Stonks import global_enums as enums
from Stonks.Orders import orders_class as orders


class Position():
    def __init__(self, parameters: dict, underlying_quote: dict, quote_data: dict):
        # save arguments
        self.parameters = parameters

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

        # define prices and initialize lists to hold price data
        self.stock_price_at_trigger = underlying_quote['ask']  # use the ask as the initial price of the option
        self.stop_loss = self.parameters['stop_loss']
        self.stop_profit = self.parameters['stop_profit']

        # strictly for holding prices when position is bought
        self.price_history = []
        self.value_history = []

        # toggle variables for the buying and selling.
        self.opening_position = True
        self.position_open = False

        self.closing_position = False
        self.position_closed = False

        # trackign orders and order status:
        self.open_order = False
        self.orders_consistent = True
        self.order_list = []

        # track position data from accounts api
        self.position_data = []

    def needs_bought(self):
        if self.opening_position and not self.position_open \
                and not self.closing_position and not self.position_closed:
            return True
        else:
            return False

    def needs_sold(self):
        if self.closing_position and self.position_open \
                and not self.opening_position and not self.position_closed:
            return True
        else:
            return False

    def update_price_and_value(self, underlying_quote: dict, quote_data: dict, position_data: dict):
        self.underlying_quote.append(underlying_quote)
        self.quote_data.append(quote_data)
        self.price_history.append(quote_data['lastPrice'])
        self.position_data.append(position_data)
        self.value_history.append(position_data['marketValue'])

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
                        self.order_list.append(orders.Order(order_payload))
        else:
            # if no orders exist then create new orders
            for order_payload in order_payload_list:
                self.order_list.append(orders.Order(order_payload))

    def track_open_order_time(self, time: arrow.Arrow):
        open_times = []

        order: orders.Order
        for order in self.order_list:
            if order.is_open:
                open_times.append(order.time_since_last_update())
        return open_times

    def _check_open_order(self):
        order: orders.Order
        for order in self.order_list:
            if order.is_open:
                self.open_order = True

    def _check_order_consistency(self):
        buy_order_exists = False
        sell_order_exists = False
        order: orders.Order
        for order in self.order_list:
            if order.is_open:
                if order.order_instruction == enums.InstructionOptions.BUY_TO_OPEN.value():
                    buy_order_exists = True
                if order.order_instruction == enums.InstructionOptions.SELL_TO_CLOSE.value():
                    sell_order_exists = True

        if buy_order_exists and sell_order_exists:
            self.orders_consistent = False
        else:
            self.orders_consistent = True

    def open_position(self, option_price):
        self._check_open_order()
        self._check_order_consistency()
        if self.open_position() and self.orders_consistent:
            self.building_position = False
            self.position_open = True
            self.value_history.append(option_price)

    def close_position(self, option_price):
        self._check_open_order()
        self._check_order_consistency()
        if self.open_position() and self.orders_consistent:
            self.building_position = False
            self.position_open = False
            self.closing_position = False
            self.position_closed = True
            self.value_history.append(option_price)

    def check_stop_loss(self):
        if self.position_purchased:
            if self.value_history[-1] <= self.stop_loss * self.value_history[0]:
                self.position_closed = True
                return True
        else:
            return False

    def check_stop_profit(self):
        if self.position_purchased:
            if self.value_history[-1] <= self.stop_profit * np.max(np.array(self.value_history)):
                self.price_at_close_trigger = self.value_history[-1]
                self.position_closed = True
                return True
        else:
            return False


if __name__ == "__main__":
    pass
