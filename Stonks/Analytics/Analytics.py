'''
Calculate various technical signals, bollinger bands, moving averages, etc..

'''
import time
import numpy as np
import h5py


def market_hours(t):
    # print(t.shape)
    tradeable = np.zeros_like(t, dtype=np.bool)
    # print(tradeable.shape)

    for i in np.arange(t.shape[0]):
        gm_time = time.gmtime(t[i] * 1e-3)
        # print(gm_time[4])

        if gm_time[3] - 4 == 9 and gm_time[4] > 30 and (gm_time[3] - 4 < 10):
            tradeable[i] = True
        else:
            tradeable[i] = False

        if gm_time[3] - 4 >= 10 and (gm_time[3] - 4 < 16):
            tradeable[i] = True

    return tradeable


def offset_price(data, period=20):
    '''
    calculate price difference between two points

    :param data: input data
    :param period: length of moving average
    :return: moving average
    '''
    padded_data = np.concatenate((np.ones(period) * data[0], data))
    price_change = padded_data[period:] - padded_data[:-period]

    return price_change


def moving_average(data, period=20):
    '''
    calculate moving average

    :param data: input data
    :param period: length of moving average
    :return: moving average
    '''
    padded_data = np.concatenate((np.ones(period) * data[0], data))
    cumulative_data = np.cumsum(padded_data)
    moving_avg = (cumulative_data[period:] - cumulative_data[:-period]) / period

    return moving_avg


def multi_average(data, periods):
    sma_list = []
    for period in periods:
        sma_list.append(moving_average(data=data, period=period))

    return np.array(sma_list)


def exp_moving_average(data, alpha, period=200):
    '''
    calculate exponential moving average
    :param data:
    :param period:
    :return:
    '''

    padded_data = np.concatenate((np.ones(int(period - 1)) * data[0], data))

    kernel = (1 - alpha) ** np.flip(np.arange(period))
    kernel_alpha = np.copy(kernel)
    kernel_alpha[1:] = kernel[1:] * alpha
    # scaling = (1 - alpha) ** np.flip(np.arange(data.shape[0]))
    # scaling_alpha = np.copy(scaling)
    # scaling_alpha[1:] = scaling[1:]*alpha

    # cumulative_scaled_data = np.cumsum(scaling_alpha*data)
    # exp_mv_avg = cumulative_scaled_data/scaling

    exp_mv_avg = np.convolve(padded_data, np.flip(kernel_alpha), mode='valid')
    return exp_mv_avg


def bollinger_bands(data, average, period=20):
    squares = (data - average) ** 2
    pad_squares = np.concatenate((np.ones(period - 1) * squares[0], squares))
    two_sigma = 2 * np.sqrt(np.convolve(pad_squares, np.ones(period), mode='valid') / period)

    return average - two_sigma, average + two_sigma


def multi_bollinger_bands(data, multi_average, periods):
    bollinger_list_low = []
    bollinger_list_high = []
    for i, period in enumerate(periods):
        low, high = bollinger_bands(data, multi_average[i], period=20)
        bollinger_list_low.append(low)
        bollinger_list_high.append(high)
    return np.array(bollinger_list_low), np.array(bollinger_list_high)


def candle_avg(open, high, low):
    avg = (open + high + low) / 3.
    return avg


def candle_squares(avg, open, high, low):
    sig = ((avg - open) ** 2 + (avg - high) ** 2 + (avg - low) ** 2) / 3.


def candle_bollinger_bands(open, high, low, average, period=20):
    pad_squares = []
    for data in [open, high, low]:
        # print(data)
        squares = (data - average) ** 2
        pad = np.concatenate((np.ones(period - 1) * squares[0], squares))
        pad_squares.append(np.convolve(pad, np.ones(period), mode='valid') / period)

    sum_pad_squares = np.sum(np.array(pad_squares), axis=0) / 3.
    two_sigma = 2 * np.sqrt(sum_pad_squares)

    return average - two_sigma, average + two_sigma


def derivative(data, period=20):
    derivative = np.zeros_like(data)
    for i in np.arange(start=period, stop=data.shape[0]):
        derivative[i] = (data[i] - data[i - period]) / period

    derivative[0:period] = np.ones_like(period - 1) * derivative[period]

    return derivative


def second_derivative(data, period=20):
    derivative = np.zeros_like(data)
    for i in np.arange(start=period, stop=data.shape[0]):
        derivative[i] = (data[i] - 2 * data[i - period // 2] + data[i - period]) / period

    derivative[0:period] = np.ones_like(period - 1) * derivative[period]

    return derivative


def third_derivative(data, period=20):
    derivative = np.zeros_like(data)
    for i in np.arange(start=period, stop=data.shape[0]):
        derivative[i] = (data[i] - 2 * data[i - period // 3] + data[i - 2 * period // 3] - data[i - period]) / period

    derivative[0:period] = np.ones_like(period - 1) * derivative[period]

    return derivative
