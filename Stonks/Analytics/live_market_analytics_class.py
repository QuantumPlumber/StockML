import script_context

from Stonks import global_enums as enums
from Stonks.Analytics import Analytics
import numpy as np
import timeit


class Analysis():
    def __init__(self, compute_dict):
        self.compute = {}
        self.data = {}
        self.compute_dict = compute_dict
        self.num_datapoints = None

        self.analytics_up_to_date = False

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
            if isinstance(key, enums.ComputeKeys):
                pass
            else:
                print('{} is not a valid compute key'.format(key))
                return False

        return True

    def compute_analytics(self, data):

        # if not self.validate_compute_dict(self.compute_dict):
        #    return False

        self.data = data
        self.compute[enums.ComputeKeys.datetime] = np.array(data['datetime'].tolist())
        self.num_datapoints = int(self.compute[enums.ComputeKeys.datetime].shape[0])

        self.compute[enums.ComputeKeys.candle] = Analytics.candle_avg(open=np.array(data['open'].tolist()),
                                                                      high=np.array(data['high'].tolist()),
                                                                      low=np.array(data['low'].tolist()))

        self.compute[enums.ComputeKeys.tradeable] = Analytics.market_hours(self.compute[enums.ComputeKeys.datetime])

        for key, val in self.compute_dict.items():
            if key is enums.ComputeKeys.sma:
                if isinstance(val, list):
                    self.compute[key] = []
                    for period in val:
                        self.compute[key].append(
                            Analytics.moving_average(data=self.compute[enums.ComputeKeys.candle], period=period))
                else:
                    continue

            if key is enums.ComputeKeys.derivative:
                if isinstance(self.compute_dict[key], list):
                    self.compute[key] = []
                    for sma_period, deriv_period in val:
                        local_sma = Analytics.moving_average(data=self.compute[enums.ComputeKeys.candle],
                                                             period=sma_period)
                        self.compute[key].append(Analytics.derivative(data=local_sma, period=deriv_period))
                else:
                    continue

            if key is enums.ComputeKeys.Bollinger:
                if isinstance(val, list):
                    self.compute[key] = []
                    for anchor_period, oscillator_period, Bollinger_period in val:
                        local_anchor = Analytics.moving_average(data=self.compute[enums.ComputeKeys.candle],
                                                                period=anchor_period)
                        local_oscillator = Analytics.moving_average(data=self.compute[enums.ComputeKeys.candle],
                                                                    period=oscillator_period)
                        self.compute[key].append(Analytics.bollinger_bands(data=local_oscillator,
                                                                           average=local_anchor,
                                                                           period=Bollinger_period))

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
        old_data_size = self.data['datetime'].shape[0]
        if old_data_size < new_data.shape[0]:
            equal_times = np.all(self.data['datetime'] == new_data[:old_data_size])
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

    def timing_test(self, data, iterations=100):
        '''
        time the computation to check if it is lagging

        :return:
        '''

        def dummy_func():
            self.compute_analytics(data=data)

        # test_instance.compute_analytics(compute_dict=compute_dict)
        result = timeit.Timer(dummy_func).timeit(number=iterations)
        return result, result / iterations


if __name__ == '__main__':
    seconds_in_a_trading_day = (6 * 60 + 30) * 60
    test_compute_dict = {enums.ComputeKeys.sma: [10, 30],
                         enums.ComputeKeys.derivative: [[10, 10], [30, 30]],
                         enums.ComputeKeys.Bollinger: [[30, 10, 10]]}

    test_data = {'datetime': np.arange(seconds_in_a_trading_day),
                 'open': np.random.random(size=seconds_in_a_trading_day),
                 'high': np.random.random(size=seconds_in_a_trading_day),
                 'low': np.random.random(size=seconds_in_a_trading_day),
                 'close': np.random.random(size=seconds_in_a_trading_day),
                 'volume': np.random.random(size=seconds_in_a_trading_day)}

    test_instance = Analysis(test_compute_dict)
    print(test_instance.timing_test(data=test_data))

    '''
    iterations = 100

    #test_instance.compute_analytics(compute_dict=compute_dict)
    result = timeit.timeit('test_instance.compute_analytics(compute_dict=compute_dict)',
                           setup="from __main__ import test_instance, compute_dict", number=iterations)

    print(result/iterations)
    '''
