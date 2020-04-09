import numpy as np


class position():

    def __init__(self, strike_price, volatility, t, stock_price, expiration=60 * 6 + 30, stop_loss=.8, stop_profit=2.0):
        self.expiration = expiration
        self.strike_price = strike_price

        self.n_binomial = 50
        self.volatility = volatility

        self.r = 0
        self.q = 0

        self.stock_price_at_open = stock_price
        self.stop_loss = stop_loss
        self.stop_profit = stop_profit

        self.value_history = []
        self.value_history.append(self.compute_price(t, stock_price=stock_price))

        self.position_open = True
        self.position_closed = False

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

        binomial_tree = self.strike_price - price_tree
        binomial_tree[binomial_tree <= 0] = 0

        # reduce binomial tree to determine the price:
        for i in np.arange(1, self.n_binomial):
            price_tree = stock_price * up ** (2 * np.arange(self.n_binomial - i) - (self.n_binomial - i))
            # print(price_tree)
            binomial_tree = p * binomial_tree[1:] + q * binomial_tree[:-1]

            # compute excersize price
            exercise = self.strike_price - price_tree
            binomial_tree[binomial_tree <= exercise] = exercise[binomial_tree <= exercise]

            # print(binomial_tree)

        option_price = binomial_tree[0]

        self.value_history.append(option_price)

        return option_price

    def check_stop_loss(self):
        if self.value_history[-1] <= self.stop_loss * self.value_history[0]:
            return True

    def check_stop_profit(self):
        if self.value_history[-1] <= self.stop_profit * np.max(np.array(self.value_history)):
            return True

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

    print(put_option.value_history)
