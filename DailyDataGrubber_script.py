import importlib
import SandPfromWiki

importlib.reload(SandPfromWiki)
import test_DailyDataGrubber

importlib.reload(test_DailyDataGrubber)
import numpy as np

lookback_list = np.arange(start=1, stop=10)

grub_targets = SandPfromWiki.get_SandP500()
grub_targets.append('SPY')

for lookback in lookback_list:
    test_DailyDataGrubber.DailyDataGrubberFunc(lookback_days=lookback, grub_targets=grub_targets)
