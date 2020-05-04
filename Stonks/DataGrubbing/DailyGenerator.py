import os
import h5py
import arrow

'''
    A generator to grab daily day files from the Data repository return them
'''


def days_in_directory(filedirectory='D:/StockData/', ticker='SPY'):
    file_number = 0
    unique_dates = []

    for direntry in os.scandir(filedirectory):
        result_dict = {}
        meta_result_dict = {}

        if direntry.is_dir():
            continue

        if direntry.is_file():
            filepath = direntry.path
            # print(filepath)
            try:
                datafile = h5py.File(filepath, 'r')
            except:
                print('could not open file: {}'.format(filepath))
                continue

        time_data = datafile[ticker]['datetime'][...]
        if time_data.shape[0] == 0:
            print('no \'SPY\' data in file: {}'.format(filepath))
            continue

        mid_day = arrow.get(time_data[time_data.shape[0] // 2] * 1e-3).to('America/New_York')
        date = mid_day.date()

        print('isoweekday is: {}'.format(type(mid_day.isoweekday())))
        if mid_day.isoweekday() not in [1, 2, 3, 4, 5]:
            print('not a weekday')
            continue
        else:
            if date not in unique_dates:
                file_number += 1
                unique_dates.append(date)
            else:
                continue

        datafile.close()

    return file_number, unique_dates


def data_file_generator(filedirectory='D:/StockData/', ticker='SPY'):
    result_list = []
    meta_result_list = []

    unique_dates = []
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

        mid_day = arrow.get(time_data[time_data.shape[0] // 2] * 1e-3).to('America/New_York')
        date = mid_day.date()

        if arrow.get(time_data[time_data.shape[0] // 2] * 1e-3).isoweekday() not in [1, 2, 3, 4, 5]:
            print('not a weekday')
            continue
        else:
            if date not in unique_dates:
                unique_dates.append(date)
                yield datafile, str(date)
            else:
                continue

