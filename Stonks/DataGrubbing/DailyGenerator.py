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

        if ticker not in list(datafile.keys()):
            print('no \'SPY\' data in file: {}'.format(filepath))
            continue

        time_data = datafile[ticker]['datetime'][...]
        if time_data.shape[0] == 0:
            print('no \'SPY\' data in file: {}'.format(filepath))
            continue
        else:
            print('\'SPY\' data found in file: {}'.format(filepath))

        mid_day = arrow.get(time_data[time_data.shape[0] // 2] * 1e-3).to('America/New_York')
        date = mid_day.date()

        start_date = arrow.Arrow(year=2020, month=4, day=21, tzinfo='America/New_York')
        end_date = arrow.now('America/New_York')

        print('isoweekday is: {}'.format((mid_day.isoweekday())))
        if mid_day.isoweekday() not in [1, 2, 3, 4, 5]:
            print('not a weekday')
            continue
        else:
            if date not in unique_dates and mid_day.is_between(start=start_date, end=end_date, bounds='()'):
                file_number += 1
                unique_dates.append(date)
            else:
                continue

        datafile.close()

    return file_number, unique_dates


def data_file_generator(filedirectory='D:/StockData/', ticker='SPY'):
    result_list = []
    meta_result_list = []

    VIX_path = filedirectory + 'S&P_500_VIX_2020-05-10'
    if os.path.exists(VIX_path):
        print('opening datafile:')
        print(VIX_path)
        VIX_datafile = h5py.File(VIX_path, 'r')
    else:
        print('VIX file does not exist!')

    VIX_datetime = VIX_datafile['VIX9D']['datetime'][...]
    VIX_dates = []
    for dd in VIX_datetime:
        VIX_dates.append(arrow.get(dd * 1e-3).to('America/New_York').date())

    VIX_volatility = (VIX_datafile['VIX9D']['open'][...] + VIX_datafile['VIX9D']['high'][...] +
                      VIX_datafile['VIX9D']['low'][...] + VIX_datafile['VIX9D']['close'][...]) / 4.

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

        if ticker not in list(datafile.keys()):
            print('no \'SPY\' data in file: {}'.format(filepath))
            continue

        time_data = datafile[ticker]['datetime'][...]
        if time_data.shape[0] == 0:
            print('no \'SPY\' data in file: {}'.format(filepath))
            continue

        mid_day = arrow.get(time_data[time_data.shape[0] // 2] * 1e-3).to('America/New_York')
        date = mid_day.date()

        start_date = arrow.Arrow(year=2020, month=4, day=21, tzinfo='America/New_York')
        end_date = arrow.now('America/New_York')

        if arrow.get(time_data[time_data.shape[0] // 2] * 1e-3).isoweekday() not in [1, 2, 3, 4, 5]:
            print('not a weekday')
            continue
        else:
            if date not in unique_dates and mid_day.is_between(start=start_date, end=end_date, bounds='()'):
                unique_dates.append(date)

                count = 0
                for dd in VIX_dates:
                    if dd == date:
                        break
                    count += 1

                yield datafile, str(date), VIX_volatility[count]
            else:
                continue
