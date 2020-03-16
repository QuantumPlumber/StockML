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

    grub_dates = [1582551000000]

    '''File Handling'''
    filename = '../StockData/S&P_500_{}'.format(str(datetime.date.today()))
    if not os.exists(filename):
        datafile = h5py.File(filename)
    else:
        print('Data file already exists!')

    grub_symbols = []
    grub_data = []
    # grub_targets = ['SPY']
    grub_targets = SandPfromWiki.get_SandP500()
    grub_targets.append('SPY')
    for grubbie, grub_date in zip(grub_targets, grub_dates):
        symbol, data = grub(symbol=grubbie, startdate=grub_date)
        grub_symbols.append(symbol)
        grub_data.append(data)

    for key in grub_data[0].keys():
        plt.figure()
        plt.suptitle(key)
        for dat in grub_data:
            plt.plot(dat['datetime'], dat[key])
