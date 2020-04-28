import script_context
import time
import arrow
import matplotlib.pyplot as plt
from Stonks import global_enums as enums
from Stonks.Stratego import live_market_strategy_class as strategy_class
import importlib

importlib.reload(strategy_class)

parameters = {'Bollinger_top': .0, 'Bollinger_bot': -2.0, 'stop_loss': .2, 'profit': .5, 'price_multiplier': 2,
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
strategy_instance.trading_day_minute()
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
strategy_instance.update_positions()
end_time = time.perf_counter() - start_time
print(end_time)

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
