from abc import ABC, abstractmethod
from orders.models import Order
from .notification_service import get_order_notifier


class OrderState(ABC):
    def __init__(self, order: Order):
        self.order = order

    @abstractmethod
    def process_next_step(self):  # Перейти к следующему логическому состоянию
        pass

    @abstractmethod
    def cancel_order(self):  # Отменить заказ
        pass


class NewOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Processing payment and moving to 'PROCESSING'.")
        self.order.status = 'PROCESSING'
        self.order.save(update_fields=['status'])
        notifier = get_order_notifier()
        notifier.notify(self.order, 'status_changed', previous_status='NEW')

    def cancel_order(self):
        print(f"Order {self.order.id}: Canceling new order.")
        self.order.status = 'CANCELED'
        self.order.save(update_fields=['status'])
        notifier = get_order_notifier()
        should_return_stock = True
        if should_return_stock:
            notifier.notify(self.order, 'canceled_with_stock_return')
        else:
            notifier.notify(self.order, 'status_changed', previous_status='NEW', reason='canceled_no_stock_return')


class ProcessingOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Order processed, moving to 'SHIPPED' (or 'Ready for Pickup').")
        self.order.status = 'SHIPPED'
        self.order.save(update_fields=['status'])
        notifier = get_order_notifier()
        notifier.notify(self.order, 'status_changed')

    def cancel_order(self):
        print(f"Order {self.order.id}: Canceling order in processing. (Refund logic would be here)")
        self.order.status = 'CANCELED'
        self.order.save(update_fields=['status'])
        notifier = get_order_notifier()
        notifier.notify(self.order, 'status_changed')


class ShippedOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Order delivered/picked up, moving to 'COMPLETED'.")
        self.order.status = 'COMPLETED'
        self.order.save(update_fields=['status'])
        notifier = get_order_notifier()
        notifier.notify(self.order, 'status_changed')

    def cancel_order(self):
        print(f"Order {self.order.id}: Cannot cancel a shipped order through this simple flow.")


class CompletedOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Order is already completed. No further steps.")
        # No state change

    def cancel_order(self):
        print(f"Order {self.order.id}: Cannot cancel a completed order.")


class CanceledOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Order is canceled. No further steps.")

    def cancel_order(self):
        print(f"Order {self.order.id}: Order is already canceled.")

class OrderContext:
    def __init__(self, order: Order):
        self.order = order
        self._state = self._get_state_from_order_status()

    def _get_state_from_order_status(self) -> OrderState:
        status_map = {
            'NEW': NewOrderState,
            'PROCESSING': ProcessingOrderState,
            'SHIPPED': ShippedOrderState,
            'COMPLETED': CompletedOrderState,
            'CANCELED': CanceledOrderState,
        }
        state_class = status_map.get(self.order.status)
        if not state_class:
            print(f"Warning: Unknown order status '{self.order.status}'. Defaulting to NewOrderState.")
            return NewOrderState(self.order)
        return state_class(self.order)

    def refresh_state(self):
        self._state = self._get_state_from_order_status()

    def process_next_step(self):
        self._state.process_next_step()
        self.refresh_state()

    def cancel_order(self):
        self._state.cancel_order()
        self.refresh_state()