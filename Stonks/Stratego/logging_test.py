import script_context
import time
import arrow
import matplotlib.pyplot as plt
from Stonks import global_enums as enums
from Stonks.Stratego import live_market_strategy_class as strategy_class
from Stonks.Analytics import live_market_analytics_class as analytics_class
from Stonks.Positions import live_market_position_class as positions
from Stonks.Orders import orders_class
from Stonks.utilities import utility_class

from Stonks.utilities import utility_exceptions

import importlib

importlib.reload(strategy_class)

if __name__ == '__main__':

    parameters = {'Bollinger_top': .0, 'Bollinger_bot': -2.0, 'stop_loss': .2, 'profit': .5, 'price_multiplier': 2,
                  'max_strike_delta': 6, 'minimum_position_size_fraction': .3, 'stop_trading': .2}

    compute_dict = {enums.ComputeKeys.sma: [10, 30],
                    enums.ComputeKeys.derivative: [[10, 10], [30, 30]],
                    enums.ComputeKeys.Bollinger: [[30, 10, 10]]}

    # Must initialize the strategy instance
    strategy_instance = strategy_class.Strategy(symbol='SPY',
                                                compute_dict=compute_dict,
                                                parameters=parameters,
                                                verbose=True,
                                                log_directory='D:/AlgoLogs')

    strategy_instance.set_up_data_logging()
    strategy_instance.log_snapshot()