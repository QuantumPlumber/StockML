import script_context

import requests
from Stonks.utilities.config import apikey
import pandas as pd
import matplotlib.pyplot as plt
import time
import importlib
import h5py
import os
import sys
import numpy as np
import arrow


def grub(symbol='SPY'):
    # define endpoint
    price_endpoint = r'https://api.tdameritrade.com/v1/marketdata/{}/pricehistory'.format(symbol)

    payload = {'apikey': str(apikey),
               'periodType': 'year',
               'period': int(15),
               'frequencyType': 'daily',
               'frequency': int(1),
               'needExtendedHoursData': 'false',
               }

    content = requests.get(url=price_endpoint, params=payload)
    print(content.url)
    time.sleep(1)  # wait for webpage to load

    prelim_data = content.json()
    print(prelim_data)
    try:
        symbol = prelim_data['symbol']
        data = pd.DataFrame.from_dict(prelim_data['candles'])
        return True, symbol, data
    except KeyError:
        print('symbol {} is invalid'.format(symbol))
        return False, None, None


if __name__ == '__main__':
    # symbol, data = grub(symbol='SPY')

    grub_targets = ['SPY']

    '''File Handling'''
    filename = 'D:/StockData/Daily_History/S&P_500_Daily_{}'.format(str(arrow.now('America/New_York').date()))

    if not os.path.exists(filename):
        print('creating datafile:')
        print(filename)
        datafile = h5py.File(filename)
    else:
        print('Data file already exists!')
        print('exiting program')
        sys.exit()

    successful_grubs = 0
    for grubbie in grub_targets:
        success, symbol, data = grub(symbol=grubbie)
        successful_grubs += 1

        if success:
            local_group = datafile.create_group(str(symbol))
            # print(local_group.name)
            for key in data.keys():
                local_dataset = local_group.create_dataset(name=key, shape=data[key].shape, dtype=np.float64)
                # print(local_dataset.name)
                local_dataset[...] = data[key]

        print('successfully grubbed {}'.format(symbol))

    print('successfully grubbed {} tickers'.format(successful_grubs))

    datafile.close()
