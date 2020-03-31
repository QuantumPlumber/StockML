import script_context

import importlib
from Stonks.DataGrubbing import SandPfromWiki
import numpy as np
from Stonks.DataGrubbing import test_DailyDataGrubber

importlib.reload(test_DailyDataGrubber)
importlib.reload(SandPfromWiki)

lookback_list = np.arange(start=1, stop=10)

grub_targets = SandPfromWiki.get_SandP500()
grub_targets.append('SPY')

for lookback in lookback_list:
    test_DailyDataGrubber.DailyDataGrubberFunc(lookback_days=lookback, grub_targets=grub_targets)
