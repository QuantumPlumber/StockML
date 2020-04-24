from enum import Enum


########################################################################################################################
########################################################################################################################
########################################################################################################################
class StonksPositionState(Enum):
    needs_buy_order = 1
    open_buy_order = 2

    needs_add_order = 3
    open_add_order = 4

    needs_stop_loss_order = 9
    open_stop_loss_order = 10

    needs_reduce_order = 5
    open_reduce_order = 6

    needs_close_order = 7
    open_close_order = 8



########################################################################################################################
########################################################################################################################
########################################################################################################################
class DataKeys(Enum):
    datetime = 'datetime'
    open = 'open'
    high = 'high'
    low = 'low'
    close = 'close'
    volume = 'volume'


########################################################################################################################
########################################################################################################################
########################################################################################################################
class ComputeKeys(Enum):
    data = 'data'
    sma = 'sma'
    derivative = 'derivative'
    Bollinger = 'Bollinger'


########################################################################################################################
########################################################################################################################
########################################################################################################################
class PriceHistoryPayload(Enum):
    apikey = 'apikey'
    periodType = 'periodType'
    period = 'period'
    frequencyType = 'frequencyType'
    frequency = 'frequency'
    startDate = 'startDate'
    endDate = 'endDate'
    needExtendedHoursData = 'needExtendedHoursData'


class PeriodTypeOptions(Enum):
    day = 'day'
    month = 'month'
    year = 'year'
    ytd = 'ytd'


class FrequencyTypeOptions(Enum):
    minute = 'minute'
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'


########################################################################################################################
########################################################################################################################
########################################################################################################################

class OrderPayload(Enum):
    session = 'session'
    duration = 'duration'
    orderType = 'orderType'
    complexOrderStrategyType = 'complexOrderStrategyType'
    quantity = 'quantity'
    stopPrice = 'stopPrice'
    stopType = 'stopType'
    price = 'price'
    orderLegCollection = 'orderLegCollection'
    orderStrategyType = 'orderStrategyType'
    orderId = 'orderId'
    status = 'status'


class SessionOptions(Enum):
    NORMAL = 'NORMAL'


class DurationOptions(Enum):
    DAY = 'DAY'
    GOOD_TILL_CANCEL = 'GOOD_TILL_CANCEL'
    FILL_OR_KILL = 'FILL_OR_KILL'


class OrderTypeOptions(Enum):
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    STOP = 'STOP'
    STOP_LIMIT = 'STOP_LIMIT'
    TRAILING_STOP = 'TRAILING_STOP'
    MARKET_ON_CLOSE = 'MARKET_ON_CLOSE'
    TRAILING_STOP_LIMIT = 'TRAILING_STOP_LIMIT'


class ComplexOrderStrategyTypeOptions(Enum):
    NONE = 'NONE'
    STRADDLE = 'STRADDLE'
    STRANGLE = 'STRANGLE'


class StopTypeOptions(Enum):
    STANDARD = 'STANDARD'
    BID = 'BID'
    ASK = 'ASK'
    LAST = 'LAST'
    MARK = 'MARK'


class OrderLegCollectionDict(Enum):
    orderLegType = 'orderLegType'
    legId = 'legId'
    instrument = 'instrument'
    instruction = 'instruction'
    quantity = 'quantity'


class OrderLegTypeOptions:
    EQUITY = 'EQUITY'
    OPTION = 'OPTION'


class InstrumentType(Enum):
    symbol = 'symbol'
    assetType = 'assetType'


class AssetTypeOptions(Enum):
    EQUITY = 'EQUITY'
    OPTION = 'OPTION'


class InstructionOptions(Enum):
    BUY = 'BUY'
    SELL = 'SELL'
    BUY_TO_OPEN = 'BUY_TO_OPEN'
    SELL_TO_CLOSE = 'SELL_TO_CLOSE'


class OrderStrategyTypeOptions(Enum):
    SINGLE = 'SINGLE'
    OCO = 'OCO'
    TRIGGER = 'TRIGGER'


class StatusOptions(Enum):
    AWAITING_PARENT_ORDER = 'AWAITING_PARENT_ORDER'
    AWAITING_CONDITION = 'AWAITING_CONDITION'
    AWAITING_MANUAL_REVIEW = 'AWAITING_MANUAL_REVIEW'
    ACCEPTED = 'ACCEPTED'
    AWAITING_UR_OUT = 'AWAITING_UR_OUT'
    PENDING_ACTIVATION = 'PENDING_ACTIVATION'
    QUEUED = 'QUEUED'
    WORKING = 'WORKING'
    REJECTED = 'REJECTED'
    PENDING_CANCEL = 'PENDING_CANCEL'
    CANCELED = 'CANCELED'
    PENDING_REPLACE = 'PENDING_REPLACE'
    REPLACED = 'REPLACED'
    FILLED = 'FILLED'
    EXPIRED = 'EXPIRED'


########################################################################################################################
########################################################################################################################
########################################################################################################################
'''
order class status
'''
