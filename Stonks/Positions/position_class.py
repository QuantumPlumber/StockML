import numpy as np
from enum import Enum
import matplotlib.pyplot as plt


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
                 capital=1,
                 n_binomial=100):

        self.option_type = option_type

        self.expiration = expiration
        self.strike_price = strike_price

        self.n_binomial = n_binomial
        self.volatility = volatility / 100.
        self.volatility_time_period = 30 * 24 * 60

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
        self.quantity_at_buy_or_add.append(capital / self.price_history[-1])

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
        period = (self.expiration - t)
        delta_t = period / self.n_binomial  # units of minutes
        # print(delta_t)
        self.delta_t = delta_t

        # convert volatility to local timestep
        volatility_rescale = self.volatility_time_period / delta_t  # compute number to steps in volatility interval
        volatility_rescale = self.volatility_time_period / period  # compute number to steps in volatility interval
        print(volatility_rescale)
        # local_volatility = self.volatility / np.sqrt(volatility_rescale) * 2
        local_volatility = self.volatility / 2

        local_volatility = self.volatility / np.sqrt(volatility_rescale)
        print(local_volatility)

        up = np.exp(local_volatility * np.sqrt(delta_t))
        # print('up: {}'.format(up))
        self.up = up
        down = 1 / up
        self.down = down

        p = (np.exp((self.r - self.q) * delta_t) - down) / (up - down)
        # print('p: {}'.format(p))
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
            binomial_tree[binomial_tree <= 0] = 0

            # print(binomial_tree)

        # print(binomial_tree)
        option_price = binomial_tree[0]
        '''
        if np.isnan(option_price):
            option_price = .1
        
        if option_price <= .1:
            option_price = .1
        '''

        self.price_history.append(option_price)

        return option_price

    def compute_value(self):
        value = np.sum(np.array(self.quantity_at_buy_or_add)) * self.price_history[-1]

        self.value_history.append(value)

    def check_stop_loss(self):
        if self.value_history[-1] <= self.stop_loss * self.value_history[0]:
            # if self.value_history[-1] <= self.stop_loss * np.max(np.array(self.value_history)):
            return True

    def check_stop_profit(self):
        if self.value_history[-1] >= self.value_history[0]:
            if self.value_history[-1] <= self.stop_profit * np.max(np.array(self.value_history)):
                # if self.value_history[-1] >= self.stop_profit * np.array(self.value_history)[0]:
                return True

    def percent_gain(self):
        return self.value_history[-1] / self.average_value[-1]

    def close_position(self, stock_price):
        self.position_closed = True
        self.stock_price_at_close = stock_price


if __name__ == "__main__":

    strike = 260
    stock_price = 260
    volatitity = .0018
    volatitity = 36.
    end_of_day = 60 * 6 + 30
    put_option = position(strike_price=strike,
                          volatility=volatitity,
                          t=0,
                          stock_price=stock_price,
                          expiration=end_of_day,
                          stop_loss=.8,
                          stop_profit=2.0,
                          option_type=OptionType.PUT,
                          capital=1)

    # put_option.compute_price(t=0, stock_price=260)

    time_step = 10
    compute_times = np.linspace(0, end_of_day, num=50)
    stock_prices = np.linspace(start=stock_price - 5, stop=stock_price + 5 + 2, num=50)
    price_history = np.zeros(shape=(stock_prices[0:-1].shape[0], compute_times[0:-1].shape[0]))
    for i, pri in enumerate(stock_prices[0:-1]):
        for j, t in enumerate(compute_times[0:-1]):
            price_history[i, j] = put_option.compute_price(t=t, stock_price=pri)

    tt, pp = np.meshgrid(compute_times, stock_prices)
    plt.figure(figsize=(10, 10))
    plt.pcolormesh(tt, pp, price_history)
    # plt.pcolormesh(tt, pp, price_history - price_history[stock_prices.shape[0] // 2, 0])
    plt.colorbar()

    '''
    strike = 260
    stock_price = 260
    volatitity = 24.
    end_of_day = 60 * 6 + 30

    time_step = 10
    compute_times = np.linspace(0, end_of_day-1, num=10)
    binomial_steps = np.arange(start=50, stop=450, step=100)
    price_history = np.zeros_like(compute_times)
    convergence = []
    for i, binom in enumerate(binomial_steps):
        put_option = position(strike_price=strike,
                              volatility=volatitity,
                              t=0,
                              stock_price=stock_price,
                              expiration=end_of_day,
                              stop_loss=.8,
                              stop_profit=2.0,
                              option_type=OptionType.PUT,
                              capital=1,
                              n_binomial=binom)

        for j, t in enumerate(compute_times):
            price_history[j] = put_option.compute_price(t=t, stock_price=stock_price)

        convergence.append(price_history)

    plt.figure(figsize=(10, 10))
    for conv in convergence:
        plt.plot(compute_times, conv)
    '''
