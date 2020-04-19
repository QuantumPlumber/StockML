import numpy as np
import arrow

from Stonks import global_enums as enums


class Position():
    def __init__(self, parameters: dict, underlying_quote: dict, quote_data: dict):
        # save arguments
        self.parameters = parameters
        self.underlying_quote = underlying_quote
        self.quote_data = quote_data

        # define the option
        self.type = quote_data['putCall']
        self.expiration = quote_data['expirationDate']
        self.strike_price = quote_data['strikePrice']
        self.symbol = quote_data['symbol']

        self.stock_price_at_trigger = underlying_quote['ask']  # use the ask as the initial price of the option

        self.stop_loss = self.parameters['stop_loss']
        self.stop_profit = self.parameters['stop_profit']

        self.value_history = []

        self.position_needs_bought = True
        self.position_bought = False
        self.position_open = False

        self.position_needs_sold = False
        self.position_sold = False
        self.position_closed = False

        self.open_order = False
        self.order_id = []
        self.order_time = []
        self.order_payload = []

        self.number_of_contracts = []

    def needs_bought(self):
        if self.position_needs_bought and not self.position_open \
                and not self.position_sold and not self.position_closed:
            return True
        else:
            return False

    def needs_sold(self):
        if self.position_needs_sold and self.position_open \
                and not self.position_sold and not self.position_closed:
            return True
        else:
            return False

    def update_price(self, option_price):
        self.value_history.append(option_price)

    def open_buy_order(self, payload, time: arrow.Arrow):
        self.open_order = True
        self.order_time.append(time)
        self.order_payload.append(payload)
        self.order_id.append(payload[enums.OrderPayload.orderId.value])

    def close_buy_order(self, payload, time: arrow.Arrow):
        self.open_order = False
        self.order_time.append(time)
        self.order_payload.append(payload)
        self.order_id.append(payload[enums.OrderPayload.orderId.value])

    def track_open_order(self, time: arrow.Arrow):
        return self.order_time[0] - time

    def open_position(self, option_price):
        self.position_needs_bought = False
        self.position_bought = True
        self.position_open = True
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

    def open_sell_order(self, payload, time: arrow.Arrow):
        self.open_order = True
        self.order_time.append(time)
        self.order_payload.append(payload)
        self.order_id.append(payload[enums.OrderPayload.orderId.value])

    def close_sell_order(self, payload, time: arrow.Arrow):
        self.open_order = False
        self.order_time.append(time)
        self.order_payload.append(payload)
        self.order_id.append(payload[enums.OrderPayload.orderId.value])

    def close_position(self, option_price):
        self.position_needs_sold = False
        self.position_sold = True
        self.position_open = False
        self.position_closed = True
        self.value_history.append(option_price)


if __name__ == "__main__":
    pass
