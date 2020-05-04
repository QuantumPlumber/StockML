'''
Calculate various technical signals, bollinger bands, moving averages, etc..

'''
import time
import arrow
import numpy as np
import h5py


def market_hours(t):
    # print(t.shape)
    tradeable = np.zeros_like(t, dtype=np.bool)
    # print(tradeable.shape)

    start_of_trading_minute = 9 * 60 + 30
    end_of_trading_minute = 16 * 60

    for i in np.arange(t.shape[0]):

        trade_time = arrow.get(t[i] * 1e-3).to('America/New_York')
        current_minute = trade_time.hour * 60 + trade_time.minute  # in minutes from open

        if start_of_trading_minute < current_minute < end_of_trading_minute:
            tradeable[i] = True
        else:
            tradeable[i] = False

    return tradeable


def minute_time(t):
    # print(t.shape)
    minute_t = np.zeros_like(t)
    # print(tradeable.shape)

    start_of_trading_minute = 9 * 60 + 30
    end_of_trading_minute = 16 * 60

    for i in np.arange(t.shape[0]):

        trade_time = arrow.get(t[i] * 1e-3).to('America/New_York')
        current_minute = trade_time.hour * 60 + trade_time.minute  # in minutes from open
        minute_t[i] = current_minute - start_of_trading_minute

    return minute_t


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


def moving_average_update(old_data, old_avg, new_data, period=20):
    '''
    update the moving average

    :param data:
    :param period:
    :return:
    '''

    if old_data.shape[0] < period:
        padded_data = np.concatenate((np.ones(period) * old_data[0], old_data))
        working_data = old_data[-period:]
    else:

        working_data = old_data[-period:]

    working_data = np.concatentate((working_data, new_data))

    cumulative_data = np.cumsum(working_data)
    working_moving_avg = (cumulative_data[period:] - cumulative_data[:-period]) / period

    moving_avg = np.concatenate((old_avg, working_moving_avg))

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


def bollinger_bands_update(old_data, old_average, new_data, new_average, period=20):
    if old_data.shape[0] < period and old_average.shape[0] < period:
        old_data_padded = np.concatenate((np.ones(period - 1) * old_data[0], old_data))
        working_old_data = old_data_padded[-(period - 1):]
        old_average_padded = np.concatenate((np.ones(period - 1) * old_average[0], old_average))
        working_old_average = old_average_padded[-(period - 1):]
    else:
        working_old_data = old_data[-(period - 1):]
        working_old_average = old_average[-(period - 1):]

    working_data = np.concatenate((working_old_data, new_data))
    working_average = np.concatenate((working_old_data, new_average))

    pad_squares = (working_data - working_average) ** 2
    two_sigma = 2 * np.sqrt(np.convolve(pad_squares, np.ones(period), mode='valid') / period)

    return working_average - two_sigma, working_average + two_sigma


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
