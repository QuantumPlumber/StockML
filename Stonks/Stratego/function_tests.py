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

parameters = {'Bollinger_top': .0, 'Bollinger_bot': -2.0, 'stop_loss': .8, 'profit': .5, 'price_multiplier': 2,
              'max_strike_delta': 6, 'stop_trading': .2}

compute_dict = {enums.ComputeKeys.sma: [10, 30],
                enums.ComputeKeys.derivative: [[10, 10], [30, 30]],
                enums.ComputeKeys.Bollinger: [[30, 10, 10]]}

# Must initialize the strategy instance
strategy_instance = strategy_class.Strategy(symbol='SPY',
                                            compute_dict=compute_dict,
                                            parameters=parameters,
                                            verbose=True)

start_time = time.perf_counter()
strategy_instance.trading_day_time()
end_time = time.perf_counter() - start_time
print(end_time)

start_time = time.perf_counter()
strategy_instance.get_options_end_date()
end_time = time.perf_counter() - start_time
print(end_time)

start_time = time.perf_counter()
strategy_instance.get_current_account_values()
end_time = time.perf_counter() - start_time
print(end_time)

start_time = time.perf_counter()
strategy_instance.update_analytics()
end_time = time.perf_counter() - start_time
print(end_time)
times = []
for date in strategy_instance.analytics.compute[enums.ComputeKeys.datetime] * 1e-3:
    times.append(arrow.get(int(date)).to('America/New_York').time())
plt.plot(times,
         strategy_instance.analytics.compute[enums.ComputeKeys.candle])
print('most recent time in analysis is: {}'.format(times[-1]))

start_time = time.perf_counter()
strategy_instance.check_stop_trading()
end_time = time.perf_counter() - start_time
print(end_time)

start_time = time.perf_counter()
strategy_instance.close_all_positions()
end_time = time.perf_counter() - start_time
print(end_time)

start_time = time.perf_counter()
print('position status:')
strategy_instance.update_positions()
print([pos.status for pos in strategy_instance.positions])
print([[order.current_status, order.order_id] for pos in strategy_instance.positions for order in pos.order_list])
end_time = time.perf_counter() - start_time
print(end_time)

########################################################################################################################
# test position creation

start_time = time.perf_counter()
print('testing position creation')
strategy_instance.state = enums.StonksStrategyState.triggering
strategy_instance.buy_armed = True
strategy_instance.threshold = .1 * parameters['Bollinger_top']

print('calling create_position:')
strategy_instance.create_position()

print('position status:')
strategy_instance.update_positions()
print([pos.status for pos in strategy_instance.positions])
print([[order.current_status, order.order_id] for pos in strategy_instance.positions for order in pos.order_list])
end_time = time.perf_counter() - start_time
print(end_time)

# test creation order handling
start_time = time.perf_counter()
strategy_instance.state = enums.StonksStrategyState.processing
print('creating a new needs_buy_order..')
pos: positions.Position
for pos in strategy_instance.positions:
    pos.status = enums.StonksPositionState.needs_buy_order
    pos.target_quantity = 1
print('calling create_position:')
strategy_instance.create_position()

print('position status:')
strategy_instance.update_positions()
print([pos.status for pos in strategy_instance.positions])
print([[order.current_status, order.order_id] for pos in strategy_instance.positions for order in pos.order_list])


print('calling create_position:')
strategy_instance.create_position()

print('position status:')
strategy_instance.update_positions()
print([pos.status for pos in strategy_instance.positions])
print([[order.current_status, order.order_id] for pos in strategy_instance.positions for order in pos.order_list])

end_time = time.perf_counter() - start_time
print(end_time)

#manually delete orders

'''
start_time = time.perf_counter()
strategy_instance.hold_position()
end_time = time.perf_counter() - start_time
print(end_time)
'''

'''
#old functions:

start_time = time.perf_counter()
strategy_instance.buy_armed = True
strategy_instance.threshold = .1 * parameters['Bollinger_top']
strategy_instance.position_triggers()
end_time = time.perf_counter() - start_time
print(end_time)

start_time = time.perf_counter()
strategy_instance.build_new_position()
end_time = time.perf_counter() - start_time
print(end_time)

start_time = time.perf_counter()
strategy_instance.align_orders()
end_time = time.perf_counter() - start_time
print(end_time)
'''
