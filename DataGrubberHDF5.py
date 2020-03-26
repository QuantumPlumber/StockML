import requests
from utilities.config import apikey
import pandas as pd
import matplotlib.pyplot as plt
import time
import importlib
import DataGrubbing.SandPfromWiki as SandPfromWiki
import h5py
import datetime
import os
import time

importlib.reload(SandPfromWiki)


def grub(symbol='GOOG', startdate=1581921000000):
    # define endpoint
    price_endpoint = r'https://api.tdameritrade.com/v1/marketdata/{}/pricehistory'.format(symbol)

    gm_time = tm.gmtime(time[i] * 1e-3)

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
    try:
        symbol = prelim_data['symbol']
        data = pd.DataFrame.from_dict(prelim_data['candles'])
        return True, symbol, data
    except KeyError:
        print('symbol {} is invalid'.format(symbol))
        return False, None, None



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
    else:
        print('Data file already exists!')

    for grubbie in grub_targets:
        success, symbol, data = grub(symbol=grubbie)

        if success:
            local_group = datafile.create_group(str(symbol))
            print(local_group.name)
            for key in data.keys():
                local_dataset = local_group.create_dataset(name=key, shape=data[key].shape)
                print(local_dataset.name)
                local_dataset[...] = data[key]

    datafile.close()

