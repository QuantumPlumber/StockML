import h5py
import os
import numpy as np
import arrow


def breakout(filedirectory='../StockData/10Day/', breakout_directory='../StockData/'):
    for direntry in os.scandir(filedirectory):
        if direntry.is_dir():
            continue

        if direntry.is_file():
            filepath = direntry.path
            try:
                datafile = h5py.File(filepath, 'r')
            except:
                print('could not open file: {}'.format(filepath))
                continue

            print('processing file: {}'.format(filepath))

            for group_key in datafile.keys():
                time_data = datafile[group_key]['datetime'][...]

                date_list = []
                for i, t in enumerate(time_data):
                    # gm_time = tm.gmtime(t * 1e-3)
                    utc_time = arrow.get(t * 1e-3).to('utc')
                    utc_time = utc_time.shift(hours=-4)  # must explicitely shift time for numpy to recognize
                    # nyt_time = utc_time.to('America/New_York')
                    date_list.append(str(utc_time.date()))

                date_array = np.array(date_list, dtype='datetime64')
                unique_dates = np.unique(date_array)
                print('found the following unique dates:')
                print(unique_dates)
                break

            for unique_date in unique_dates:
                daily_filename = breakout_directory + 'S&P_500_{}'.format(str(unique_date))
                if not os.path.exists(daily_filename):
                    print('creating datafile: {}'.format(daily_filename))
                    daily_datafile = h5py.File(daily_filename)
                else:
                    print('Data file already exists!')
                    print('skipping file')
                    continue

                for group_key in datafile.keys():

                    time_data = datafile[group_key]['datetime'][...]
                    # slow :(
                    date_list = []
                    for i, t in enumerate(time_data):
                        # gm_time = tm.gmtime(t * 1e-3)
                        utc_time = arrow.get(t * 1e-3).to('utc')
                        utc_time = utc_time.shift(hours=-4)  # must explicitely shift time for numpy to recognize
                        # nyt_time = utc_time.to('America/New_York')
                        date_list.append(str(utc_time.date()))

                    date_array = np.array(date_list, dtype='datetime64')
                    data_cut = date_array == unique_date

                    group = datafile[group_key]
                    daily_group = daily_datafile.create_group(group_key)
                    for data_key in group.keys():

                        dataset = group[data_key][...][data_cut]
                        #print(data_key)
                        #print(dataset.shape)
                        daily_dataset = daily_group.create_dataset(name=data_key, shape=dataset.shape,
                                                                   dtype=np.float64)
                        daily_dataset[...] = dataset

                        if data_key == 'datetime':
                            daily_dataset = daily_group.create_dataset(name='market_hours',
                                                                       shape=dataset.shape,
                                                                       dtype=np.float64)
                            daily_dataset[...] = dataset

                daily_datafile.close()
                print('processed {}'.format(unique_date))

        print('processed 10 Day file: {}'.format(filepath))
        datafile.close()


if __name__ == '__main__':
    breakout(filedirectory='../StockData/10Day/', breakout_directory='../StockData/')