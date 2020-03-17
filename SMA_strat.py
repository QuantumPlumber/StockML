import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
import Analytics

import importlib

importlib.reload(Analytics)


def SMA_strat(sma, bollinger_down, bolligner_up, candle, candle_down, candle_up):
    crossover_threshold = .2
    stop_loss_fraction = .8

    call_buy_locs = []
    call_buy_price = []

    call_sell_locs = []
    call_sell_price = []

    put_buy_locs = []
    put_buy_price = []

    put_sell_locs = []
    put_sell_price = []

    open_position = False
    stop_loss = 0
    for i in np.range(sma.shape[0]):
        crossover_up = candle_down[i] - crossover_threshold * (candle[i] - candle_down[i])
        if sma[i] < crossover_up:  # handle call options
            if not open_position:
                call_buy_locs.append(i)
                call_buy_price.append(candle_up[i])
                stop_loss = stop_loss_fraction * candle_up[i]
            elif candle_down[i] < stop_loss:
                call_sell_locs.append(i)
                call_sell_price.append(candle_down[i])
                open_position = False

        crossover_down = candle_up[i] + crossover_threshold * (candle_up[i] - candle[i])
        if sma[i] > crossover_down:  # handle put options
            if not open_position:
                put_buy_locs.append(i)
                put_buy_price.append(candle_down[i])
                stop_loss = stop_loss_fraction * candle_down[i]
            elif candle_up[i] < stop_loss:
                put_sell_locs.append(i)
                put_sell_price.append(candle_down[i])
                open_position = False


