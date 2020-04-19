import script_context

from Stonks import global_enums
from Stonks.Analytics import Analytics
import numpy as np
import timeit


class analysis():
    def __init__(self):
        self.compute = {}
        self.data = {}

        self.Analytics_up_to_date = False

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # Begin compute functions

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def validate_compute_dict(self, compute_dict):
        for key in compute_dict.keys():
            if isinstance(key, global_enums.ComputeKeys):
                pass
            else:
                print('{} is not a valid compute key'.format(key))
                return False

        return True

    def compute_analytics(self, compute_dict):

        if not self.validate_compute_dict(compute_dict):
            return False

        self.num_datapoints = int(compute_dict['data'].shape[0])
        self.compute['time'] = compute_dict['datetime']

        self.compute['candle'] = Analytics.candle(open=compute_dict['open'],
                                                  high=compute_dict['high'],
                                                  low=compute_dict['low'])

        self.data['data'] = compute_dict['data']

        self.compute['tradeable'] = Analytics.market_hours(compute_dict['time'])

        for key, val in compute_dict.items():
            if key == 'sma':
                if isinstance(compute_dict[key], list):
                    self.compute[key] = []
                    for period in compute_dict[key]:
                        self.compute[key].append(Analytics.moving_average(data=self.compute['candle'], period=period))
                else:
                    continue

            if key == 'derivative':
                if isinstance(compute_dict[key], list):
                    self.compute[key] = []
                    for sma_period, deriv_period in compute_dict[key]:
                        local_sma = Analytics.moving_average(data=self.compute['candle'], period=sma_period)
                        self.compute[key].append(Analytics.derivative(data=local_sma, period=deriv_period))
                else:
                    continue

            if key == 'Bollinger':
                if isinstance(compute_dict[key], list):
                    self.compute[key] = []
                    for anchor_period, oscillator_period, bollinger_period in compute_dict[key]:
                        local_anchor = Analytics.moving_average(data=self.compute['candle'], period=anchor_period)
                        local_oscillator = Analytics.moving_average(data=self.compute['candle'],
                                                                    period=oscillator_period)
                        self.compute[key].append(Analytics.bollinger_bands(data=local_oscillator,
                                                                           average=local_anchor,
                                                                           period=bollinger_period))

        self.analytics_up_to_date = True

        return True

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # consistency checks

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def check_data_time(self, new_data):
        # check shape
        old_data_size = self.data['time'].shape[0]
        if old_data_size < new_data.shape[0]:
            equal_times = np.all(self.data['time'] == new_data[:old_data_size])
            return equal_times
        else:
            return False

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # Begin built-in test functions

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def timing_test(self, iterations=100):
        '''
        time the computation to check if it is lagging

        :return:
        '''

        seconds_in_a_trading_day = (6 * 60 + 30) * 60
        compute_dict = {global_enums.ComputeKeys.time: np.arange(seconds_in_a_trading_day),
                        global_enums.ComputeKeys.data: np.random.random(size=seconds_in_a_trading_day),
                        global_enums.ComputeKeys.sma: [10, 20, 30],
                        global_enums.ComputeKeys.derivative: [[10, 10], [20, 20], [30, 30]],
                        global_enums.ComputeKeys.Bollinger: [[30, 5, 10], [30, 10, 10], [30, 15, 10]]}

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
