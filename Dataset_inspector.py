import os
import h5py
import matplotlib.pyplot as plt
import numpy as np

'''File Handling'''
filedirectory = '../StockData/'
filename = 'S&P_500_2020-03-16'
filepath = filedirectory + filename
if os.path.exists(filepath):
    datafile = h5py.File(filepath)
else:
    print('Data file does not exist!')

'''
for group_key in datafile.keys():
    group = datafile[group_key]
    print(group_key)

    for data_key in group.keys():
        dataset = group[data_key]
        print(dataset.name)
        print(dataset.shape)
'''

group_choice = np.random.choice(list(datafile.keys()))
dataset_choice = np.random.choice(list(datafile[group_choice].keys()))

time = datafile[group_choice]['datetime']
data = datafile[group_choice][dataset_choice]
plt.figure()
plt.suptitle(group_choice + ' ' + dataset_choice)
plt.plot(time, data, '.')
