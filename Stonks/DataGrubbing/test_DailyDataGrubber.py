import script_context

import requests
from Stonks.utilities.config import apikey
import pandas as pd
import importlib
from Stonks.DataGrubbing import SandPfromWiki
import h5py
import os
import time

import numpy as np
import arrow

importlib.reload(SandPfromWiki)


def grub(symbol='GOOG', startdate=1581921000000):
    # define endpoint
    price_endpoint = r'https://api.tdameritrade.com/v1/marketdata/{}/pricehistory'.format(symbol)

    payload = {'apikey': apikey,
               'periodType ': 'day',
               'period': 1,
               'frequencyType': 'minute',
               'frequency': 1,
               'startDate ': startdate,
               # 'endDate ': startdate,
               'needExtendedHoursData ': 'true'
               }

    content = requests.get(url=price_endpoint, params=payload)
    time.sleep(1)  # wait for webpage to load

    prelim_data = content.json()
    try:
        symbol = prelim_data['symbol']
        data = pd.DataFrame.from_dict(prelim_data['candles'])
        #print(data['datetime'])
        #print([datetime['datetime'] for datetime in prelim_data['candles']])
        #print(data.dtypes)
        return True, symbol, data
    except KeyError:
        print('symbol {} is invalid'.format(symbol))
        return False, None, None


'''
def market_hours(t):
    tradeable = np.zeros_like(t)

    for i in np.arange(tradeable.shape[0]):
        gm_time = time.gmtime(t[i] * 1e-3)
        if (gm_time[3] - 4 > 9) and (gm_time[3] - 4 < 16):
            tradeable[i] = True
        else:
            tradeable[i] = False

    return tradeable
'''


def market_hours(t):
    tradeable = np.zeros_like(t)

    for i in np.arange(tradeable.shape[0]):
        gm_time = time.gmtime(t[i] * 1e-3)
        # print(gm_time[4])

        if gm_time[3] - 4 == 9 and gm_time[4] > 30 and (gm_time[3] - 4 < 10):
            tradeable[i] = True
        else:
            tradeable[i] = False

        if gm_time[3] - 4 >= 10 and (gm_time[3] - 4 < 16):
            tradeable[i] = True

    return tradeable


def DailyDataGrubberFunc(lookback_days=1, grub_targets=[]):
    # symbol, data = grub(symbol='SPY')

    '''
    for key in data.keys():
        plt.figure()
        plt.suptitle(key)
        plt.plot(data['datetime'], data[key])
    '''

    # caculate current date
    # today = datetime.datetime.today()
    # today = today.replace(hour=8, minute=0, second=0, microsecond=0)  # UCT time is 4 hours ahead of NYC. Military time
    # yesterday = today - datetime.timedelta(days=lookback_days)  # get the time yesterday.

    today = arrow.now('America/New_York')
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today.shift(days=-int(lookback_days))

    print('Grubbing 24hrs of data from {}'.format(str(yesterday.date())))

    epoch_time = yesterday.to('utc')
    # epoch_time = (yesterday - datetime.datetime(1970, 1, 1)).total_seconds()  # convert to epoch time.
    # gm_time = time.gmtime(time[i] * 1e-3)

    #grub_targets = []
    #grub_targets.append('SPY')

    '''File Handling'''
    # filename = '../StockData/S&P_500_{}'.format(str(datetime.date.today() - datetime.timedelta(days=lookback_days)))
    # filename = 'D:/StockData/S&P_500_{}'.format(str(datetime.date.today() - datetime.timedelta(days=lookback_days)))
    filename = 'D:/StockData/S&P_500_{}'.format(str(yesterday.date()))
    if not os.path.exists(filename):
        print('creating datafile:')
        print(filename)
        datafile = h5py.File(filename)
    else:
        print('Data file already exists!')
        print('skipping file')
        return None

    successful_grubs = 0
    for grubbie in grub_targets:
        success, symbol, data = grub(symbol=grubbie, startdate=epoch_time.timestamp * 1e3)
        successful_grubs += 1

        if success:
            local_group = datafile.create_group(str(symbol))
            # print(local_group.name)
            for key in data.keys():
                local_dataset = local_group.create_dataset(name=key, shape=data[key].shape, dtype=np.float64)
                # print(local_dataset.name)
                local_dataset[...] = data[key]
                if key == 'datetime':
                    local_dataset = local_group.create_dataset(name='market_hours', shape=data[key].shape,
                                                               dtype=np.float64)
                    local_dataset[...] = market_hours(data[key])

        print('successfully grubbed {}'.format(symbol))

    print('successfully grubbed {} tickers of the S&P 500'.format(successful_grubs))

    datafile.close()

    return None


if __name__ == '__main__':
    grub_targets = []
    grub_targets.append('SPY')

    DailyDataGrubberFunc(lookback_days=1, grub_targets=grub_targets)
