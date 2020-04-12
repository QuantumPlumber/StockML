import script_context

from Stonks.Analytics import Analytics
import numpy as np
import timeit


class analysis():
    def __init__(self, compute_dict):
        self.compute = {}
        self.data = {}
        self.compute_analytics(compute_dict=compute_dict)

    def compute_analytics(self, compute_dict):
        self.num_datapoints = int(compute_dict['time'].shape[0])
        self.data['time'] = compute_dict['time']
        self.data['data'] = compute_dict['data']

        self.compute['tradeable'] = Analytics.market_hours(compute_dict['time'])

        for key, val in compute_dict.items():
            if key == 'sma':
                if isinstance(compute_dict[key], list):
                    self.compute[key] = []
                    for period in compute_dict[key]:
                        self.compute[key].append(Analytics.moving_average(data=compute_dict['data'], period=period))
                else:
                    continue

            elif key == 'derivative':
                if isinstance(compute_dict[key], list):
                    self.compute[key] = []
                    for sma_period, deriv_period in compute_dict[key]:
                        local_sma = Analytics.moving_average(data=compute_dict['data'], period=sma_period)
                        self.compute[key].append(Analytics.derivative(data=local_sma, period=deriv_period))
                else:
                    continue

            elif key == 'Bollinger':
                if isinstance(compute_dict[key], list):
                    self.compute[key] = []
                    for anchor_period, oscillator_period, bollinger_period in compute_dict[key]:
                        local_anchor = Analytics.moving_average(data=compute_dict['data'], period=anchor_period)
                        local_oscillator = Analytics.moving_average(data=compute_dict['data'], period=oscillator_period)
                        self.compute[key].append(Analytics.bollinger_bands(data=local_oscillator,
                                                                           average=local_anchor,
                                                                           period=bollinger_period))
                else:
                    continue

    def timing_test(self, iterations=100):
        '''
        time the computation to check if it is lagging

        :return:
        '''

        seconds_in_a_trading_day = (6 * 60 + 30) * 60
        compute_dict = {'time': np.arange(seconds_in_a_trading_day),
                        'data': np.random.random(size=seconds_in_a_trading_day),
                        'sma': [10, 20, 30],
                        'derivative': [[10, 10], [20, 20], [30, 30]],
                        'Bollinger': [[30, 5, 10], [30, 10, 10], [30, 15, 10]]}

        def dummy_func():
            self.compute_analytics(compute_dict=compute_dict)

        # test_instance.compute_analytics(compute_dict=compute_dict)
        result = timeit.Timer(dummy_func).timeit(number=iterations)
        return result, result / iterations


if __name__ == '__main__':
    seconds_in_a_trading_day = (6 * 60 + 30) * 60
    compute_dict = {'time': np.arange(seconds_in_a_trading_day),
                    'data': np.random.random(size=seconds_in_a_trading_day),
                    'sma': [10, 20, 30],
                    'derivative': [[10, 10], [20, 20], [30, 30]],
                    'Bollinger': [[30, 5, 10], [30, 10, 10], [30, 15, 10]]}

    test_instance = analysis(compute_dict)
    print(test_instance.timing_test())

    '''
    iterations = 100

    #test_instance.compute_analytics(compute_dict=compute_dict)
    result = timeit.timeit('test_instance.compute_analytics(compute_dict=compute_dict)',
                           setup="from __main__ import test_instance, compute_dict", number=iterations)

    print(result/iterations)
    '''
