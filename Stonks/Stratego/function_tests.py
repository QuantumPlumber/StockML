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

    parameters = {'Bollinger_top': .0, 'Bollinger_bot': -2.0, 'stop_loss': .8, 'profit': .5, 'price_multiplier': 2,
                  'max_strike_delta': 6, 'minimum_position_size_fraction': .3, 'stop_trading': .2}

    compute_dict = {enums.ComputeKeys.sma: [10, 30],
                    enums.ComputeKeys.derivative: [[10, 10], [30, 30]],
                    enums.ComputeKeys.Bollinger: [[30, 10, 10]]}

    # Must initialize the strategy instance
    strategy_instance = strategy_class.Strategy(symbol='SPY',
                                                compute_dict=compute_dict,
                                                parameters=parameters,
                                                verbose=True)

    ########################################################################################################################
    print('testing simple functions:')

    start_time = time.perf_counter()
    strategy_instance.trading_day_time()
    end_time = time.perf_counter() - start_time
    # print(end_time)

    start_time = time.perf_counter()
    strategy_instance.get_options_end_date()
    end_time = time.perf_counter() - start_time
    # print(end_time)

    start_time = time.perf_counter()
    strategy_instance.get_current_account_values()
    end_time = time.perf_counter() - start_time
    # print(end_time)

    input('press enter to continue')
    ########################################################################################################################

    ########################################################################################################################
    print('testing analysis update')
    start_time = time.perf_counter()
    strategy_instance.update_analytics()
    end_time = time.perf_counter() - start_time
    # print(end_time)
    times = []
    for date in strategy_instance.analytics.compute[enums.ComputeKeys.datetime] * 1e-3:
        times.append(arrow.get(int(date)).to('America/New_York').time())
    plt.plot(times,
             strategy_instance.analytics.compute[enums.ComputeKeys.candle])
    print('most recent time in analysis is: {}'.format(times[-1]))

    input('press enter to continue')
    ########################################################################################################################

    ########################################################################################################################
    print('testing more simple functions:')

    start_time = time.perf_counter()
    strategy_instance.check_stop_trading()
    end_time = time.perf_counter() - start_time
    # print(end_time)

    start_time = time.perf_counter()
    strategy_instance.close_all_positions()
    end_time = time.perf_counter() - start_time
    # print(end_time)

    input('press enter to continue')
    ########################################################################################################################

    ########################################################################################################################
    print('testing position updates:')
    start_time = time.perf_counter()
    print('position status:')
    strategy_instance.update_positions()
    print([pos.status for pos in strategy_instance.positions])
    print([[order.current_status, order.order_id, order.is_open] for pos in strategy_instance.positions for order in pos.order_list])
    end_time = time.perf_counter() - start_time
    # print(end_time)

    input('press enter to continue')
    ########################################################################################################################

    ########################################################################################################################
    print('testing position creation')

    start_time = time.perf_counter()

    strategy_instance.buy_armed = True
    strategy_instance.threshold = parameters['Bollinger_top'] - .2
    strategy_instance.target_capital = strategy_instance.current_account_values['cashAvailableForTrading']

    print('calling create_position:')
    strategy_instance.state = enums.StonksStrategyState.triggering
    strategy_instance.create_position()

    print('you should see a new position')

    strategy_instance.update_positions()
    print('position status:')
    print([pos.status for pos in strategy_instance.positions])
    print('position target_quantity and quantity:')
    print([[pos.target_quantity, pos.quantity] for pos in strategy_instance.positions])
    print('position orders:')
    print([[order.current_status, order.order_id, order.is_open] for pos in strategy_instance.positions for order in pos.order_list])
    # end_time = time.perf_counter() - start_time
    # print(end_time)

    input('press enter to continue')
    ########################################################################################################################

    ########################################################################################################################
    print('test order handling for needs_buy_order position state')


    print('creating a new needs_buy_order for each position..')
    pos: positions.Position
    for pos in strategy_instance.positions:
        pos.status = enums.StonksPositionState.needs_buy_order

    print('calling create_position..')
    strategy_instance.state = enums.StonksStrategyState.processing
    strategy_instance.create_position()

    print('you should see a new order for each position and positions should be in open_buy_order state')

    strategy_instance.update_positions()
    print('position status:')
    print([pos.status for pos in strategy_instance.positions])
    print('position target_quantity and quantity:')
    print([[pos.target_quantity, pos.quantity] for pos in strategy_instance.positions])
    print('position orders:')
    print([[order.current_status, order.order_id, order.is_open] for pos in strategy_instance.positions for order in pos.order_list])

    input('press enter to continue')
    ########################################################################################################################

    ########################################################################################################################
    print('test order handling for open_buy_order position state')

    print('calling create_position:')
    strategy_instance.state = enums.StonksStrategyState.processing
    strategy_instance.create_position()

    print('You should not see a change..')

    strategy_instance.update_positions()
    print('position status:')
    print([pos.status for pos in strategy_instance.positions])
    print('position status:')
    print([pos.open_order for pos in strategy_instance.positions])
    print('position target_quantity and quantity:')
    print([[pos.target_quantity, pos.quantity] for pos in strategy_instance.positions])
    print('position orders:')
    print([[order.current_status, order.order_id, order.is_open] for pos in strategy_instance.positions for order in pos.order_list])

    # manually delete orders
    input('manually delete open orders to continue testing, press enter when ready')

    print('calling create_position:')
    strategy_instance.state = enums.StonksStrategyState.processing
    strategy_instance.create_position()

    print('You should now see the position state either advance to needs_stop_loss or back to needs_buy_order')

    strategy_instance.update_positions()
    print('position status:')
    print([pos.status for pos in strategy_instance.positions])
    print('position target_quantity and quantity:')
    print([[pos.target_quantity, pos.quantity] for pos in strategy_instance.positions])
    print('position orders:')
    print([[order.current_status, order.order_id, order.is_open] for pos in strategy_instance.positions for order in pos.order_list])

    input('press enter to continue')
    ########################################################################################################################

    ########################################################################################################################
    print('test order handling for needs_stop_loss position state')

    print('calling create_position:')
    strategy_instance.state = enums.StonksStrategyState.processing
    strategy_instance.hold_position()

    print('You should now see a stop limit order for the filled position and the state should be open_stop_loss')

    strategy_instance.update_positions()
    print('position status:')
    print([pos.status for pos in strategy_instance.positions])
    print('position target_quantity and quantity:')
    print([[pos.target_quantity, pos.quantity] for pos in strategy_instance.positions])
    print('position orders:')
    print([[order.current_status, order.order_id, order.is_open] for pos in strategy_instance.positions for order in pos.order_list])

    input('press enter to continue')
    ########################################################################################################################


    ########################################################################################################################
    print('end of test')
    ########################################################################################################################