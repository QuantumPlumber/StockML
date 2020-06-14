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
    parameters = {'option_type': enums.StonksOptionType.CALL,
                  'Bollinger_top': .0, 'Bollinger_bot': -2.0,
                  'stop_loss': .8, 'profit': .5,
                  'price_multiplier': 2,
                  'min_strike_delta': 3, 'max_strike_delta': 6,
                  'minimum_position_size_fraction': .2, 'maximum_position_size_fraction': .3,
                  'stop_trading': .2}
    '''
    parameters = {'option_type': enums.StonksOptionType.CALL,
                  'Bollinger_top': .0, 'Bollinger_bot': -2.0,
                  'stop_loss': .8, 'profit': .5,
                  'price_multiplier': 2,
                  'min_strike_delta': 3, 'max_strike_delta': 6,
                  'minimum_position_size_fraction': .2, 'maximum_position_size_fraction': .3,
                  'stop_trading': .2}
    '''
    '''
    #old dict: this probably needs to change according to volatility
    compute_dict = {enums.ComputeKeys.sma: [30, 10],
                    enums.ComputeKeys.derivative: [[10, 10], [30, 30]],
                    enums.ComputeKeys.Bollinger: [[30, 10, 30]]}
    '''

    compute_dict = {enums.ComputeKeys.sma: [40, 13],
                    enums.ComputeKeys.derivative: [[10, 10], [30, 30]],
                    enums.ComputeKeys.Bollinger: [[40, 13, 40]]}

    # Must initialize the strategy instance
    strategy_instance = strategy_class.Strategy(symbol='SPY',
                                                compute_dict=compute_dict,
                                                parameters=parameters,
                                                verbose=True,
                                                log_directory='D:/AlgoLogs')

    strategy_instance.run_strategy()
