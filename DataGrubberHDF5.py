import requests
from config import apikey
import pandas as pd
import matplotlib.pyplot as plt
import time
import importlib
import SandPfromWiki
import h5py
import datetime
import os

importlib.reload(SandPfromWiki)


def grub(symbol='GOOG', startdate=1581921000000):
    # define endpoint
    price_endpoint = r'https://api.tdameritrade.com/v1/marketdata/{}/pricehistory'.format(symbol)

    payload = {'apikey': apikey,
               'periodType ': 'day',
               'period': 10,
               'frequencyType': 'minute',
               'frequency': 1,
               # 'startDate ': startdate,
               # 'endDate ': 1584076357000,
               'needExtendedHoursData ': 'false'
               }

    content = requests.get(url=price_endpoint, params=payload)

    prelim_data = content.json()
    symbol = prelim_data['symbol']
    data = pd.DataFrame.from_dict(prelim_data['candles'])

    return symbol, data


if __name__ == '__main__':
    # symbol, data = grub(symbol='SPY')

    '''
    for key in data.keys():
        plt.figure()
        plt.suptitle(key)
        plt.plot(data['datetime'], data[key])
    '''

    grub_targets = SandPfromWiki.get_SandP500()
    grub_targets.append('SPY')
    grub_dates = [1582551000000]

    '''File Handling'''
    filename = '../StockData/S&P_500_{}'.format(str(datetime.date.today()))
    if not os.path.exists(filename):
        datafile = h5py.File(filename)
        datafile.attrs.create(name='SandP', data=grub_targets)
    else:
        print('Data file already exists!')

    for grubbie in grub_targets:
        symbol, data = grub(symbol=grubbie)

        local_group = datafile.create_group(str(symbol))
        print(local_group.name)
        for key in data.keys():
            local_dataset = local_group.create_dataset(name=key, shape=data[key].shape)
            print(local_dataset.name)
            local_dataset[...] = data[key]

    datafile.close()

