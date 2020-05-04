import numpy as np
from enum import Enum


class OptionType(Enum):
    PUT = 'PUT'
    CALL = 'CALL'


class position():

    def __init__(self,
                 strike_price,
                 volatility,
                 t,
                 stock_price,
                 expiration=60 * 6 + 30,
                 stop_loss=.8,
                 stop_profit=2.0,
                 option_type=OptionType.PUT,
                 capital=1):

        self.option_type = option_type

        self.expiration = expiration
        self.strike_price = strike_price

        self.n_binomial = 50
        self.volatility = volatility

        self.r = 0
        self.q = 0

        self.stock_price_at_open = stock_price
        self.stop_loss = stop_loss
        self.stop_profit = stop_profit

        self.price_history = []
        self.compute_price(t, stock_price=stock_price)

        self.capital_history = []
        self.price_at_buy_or_add = []
        self.quantity_at_buy_or_add = []
        self.average_value = []
        self.add_to_position(capital=capital)

        self.value_history = []
        self.compute_value()

        self.position_open = True
        self.position_closed = False

    def add_to_position(self, capital):
        ''' only call after compute price'''
        self.capital_history.append(capital)
        self.price_at_buy_or_add.append(self.price_history[-1])
        self.quantity_at_buy_or_add.append(capital/self.price_history[-1])

        total_quantity = np.sum(self.quantity_at_buy_or_add)
        total_capital = np.sum(np.array(self.capital_history))

        loc_average_price = total_capital / total_quantity

        self.average_value.append(loc_average_price)


    def compute_price(self, t, stock_price):
        '''

        :param t: time in seconds since market open
        :param stock_price: current price of stock
        :return: returns the
        '''
        delta_t = (self.expiration - t) / self.n_binomial
        self.delta_t = delta_t

        up = np.exp(self.volatility * np.sqrt(delta_t))
        self.up = up
        down = 1 / up
        self.down = down

        p = (np.exp((self.r - self.q) * delta_t) - down) / (up - down)
        q = 1 - p

        # define initial conditions
        price_tree = stock_price * up ** (2 * np.arange(self.n_binomial) - self.n_binomial)

        if self.option_type is OptionType.PUT:
            binomial_tree = self.strike_price - price_tree
        elif self.option_type is OptionType.CALL:
            binomial_tree = price_tree - self.strike_price

        binomial_tree[binomial_tree <= 0] = 0

        # reduce binomial tree to determine the price:
        for i in np.arange(1, self.n_binomial):
            price_tree = stock_price * up ** (2 * np.arange(self.n_binomial - i) - (self.n_binomial - i))
            # print(price_tree)
            binomial_tree = p * binomial_tree[1:] + q * binomial_tree[:-1]

            # compute excersize price
            if self.option_type is OptionType.PUT:
                exercise = self.strike_price - price_tree
            elif self.option_type is OptionType.CALL:
                exercise = price_tree - self.strike_price
            binomial_tree[binomial_tree <= exercise] = exercise[binomial_tree <= exercise]

            # print(binomial_tree)

        option_price = binomial_tree[0]

        self.price_history.append(option_price)

        return option_price

    def compute_value(self):
        value = np.sum(self.quantity_at_buy_or_add) * self.price_history[-1]

        self.value_history.append(value)

    def check_stop_loss(self):
        if self.value_history[-1] <= self.stop_loss * self.value_history[0]:
            return True

    def check_stop_profit(self):
        if self.value_history[-1] <= self.stop_profit * np.max(np.array(self.value_history)):
            return True

    def percent_gain(self):
        return self.value_history[-1] / self.average_value[-1]

    def close_position(self, stock_price):
        self.position_closed = True
        self.stock_price_at_close = stock_price


if __name__ == "__main__":
    strike = 260
    volatitity = .001
    end_of_day = 60 * 6 + 30
    put_option = position(expiration=end_of_day, strike_price=strike, volatility=volatitity)

    # put_option.compute_price(t=0, stock_price=260)

    for t in np.arange(0, end_of_day, 10):
        put_option.compute_price(t=t, stock_price=250)

    print(put_option.price_history)
