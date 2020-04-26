import script_context

from Stonks.Stratego.live_market_strategy_class import Strategy

compute_dict = {}
parameters = {'Bollinger_top': .0, 'Bollinger_bot': -2.0, 'stop_loss': .2, 'profit': .5, 'price_multiplier': 2,
              'max_strik_delta': 6}

strategy_instance = Strategy(symbol='SPY', compute_dict=compute_dict, parameters=parameters[''])
