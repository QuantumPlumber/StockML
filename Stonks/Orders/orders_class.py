import numpy as np
import arrow

from Stonks import global_enums as enums


class Order:
    def __init__(self, order_dict):

        self.is_open = True

        self.order_id = order_dict['order_id']
        self.order_instruction = order_dict[enums.OrderPayload.orderLegCollection.value()][
            enums.OrderLegCollectionDict.instruction.value()]

        self.timestamps = []
        self.order_history = []
        self.order_status_history = []
        self.filledQuantity = None

        self.current_status = self._get_status_from_order_dict(order_dict)

        self.update(order_dict=order_dict)

    def _get_status_from_order_dict(self, order_dict):
        for name, member in enums.StatusOptions.__members__.items():
            if order_dict['status'] == name:
                return member

    def update(self, order_dict):
        # prevent the update if this order has been closed
        if self.is_open:
            self.timestamps.append(arrow.now('America/New_York'))
            self.order_history.append(order_dict)
            self.order_status_history.append(order_dict['status'])
            self.current_status = self._get_status_from_order_dict(order_dict)

            if self.current_status in [enums.StatusOptions.CANCELED.value(),
                                       enums.StatusOptions.EXPIRED.value(),
                                       enums.StatusOptions.REJECTED.value(),
                                       enums.StatusOptions.REPLACED.value()]:
                self.is_open = False
            elif self.current_status == enums.StatusOptions.Filled.value():
                self.is_open = False
                self.filledQuantity = order_dict['filledQuantity']
            elif self.current_status == enums.StatusOptions.WORKING.value():
                self.is_open = True
                self.filledQuantity = order_dict['filledQuantity']

    def time_since_last_update(self):
        return (arrow.now('America/New_York') - self.timestamps[-1])
