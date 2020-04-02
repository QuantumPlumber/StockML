import os
import h5py
import arrow

'''
    A generator to grab daily day files from the Data repository return them
'''


def days_in_directory(filedirectory='D:/StockData/', ticker='SPY'):

    file_number = 0

    for direntry in os.scandir(filedirectory):
        result_dict = {}
        meta_result_dict = {}

        if direntry.is_dir():
            continue

        if direntry.is_file():
            filepath = direntry.path
            #print(filepath)
            try:
                datafile = h5py.File(filepath, 'r')
            except:
                print('could not open file: {}'.format(filepath))
                continue

        time_data = datafile[ticker]['datetime'][...]
        if time_data.shape[0] == 0:
            print('no \'SPY\' data in file: {}'.format(filepath))
            continue

        file_number += 1
        datafile.close()

    return file_number


def data_file_generator(filedirectory='D:/StockData/', ticker='SPY'):
    result_list = []
    meta_result_list = []

    for direntry in os.scandir(filedirectory):
        result_dict = {}
        meta_result_dict = {}

        if direntry.is_dir():
            continue

        if direntry.is_file():
            filepath = direntry.path
            print(filepath)
            try:
                datafile = h5py.File(filepath, 'r')
            except:
                print('could not open file: {}'.format(filepath))
                continue

        time_data = datafile[ticker]['datetime'][...]
        if time_data.shape[0] == 0:
            print('no \'SPY\' data in file: {}'.format(filepath))
            continue
        else:
            mid_day = time_data[time_data.shape[0] // 2]
            utc_time = arrow.get(mid_day * 1e-3).to('utc')
            utc_time = utc_time.shift(hours=-4)  # must explicitely shift time for numpy to recognize
            date = str(utc_time.date())

        yield datafile, date
