from abc import ABC, abstractmethod
from orders.models import Order  # Для type hinting
from .notification_service import order_notifier  # Для уведомлений при смене статуса


# Интерфейс Состояния
class OrderState(ABC):
    def __init__(self, order: Order):
        self.order = order

    @abstractmethod
    def process_next_step(self):  # Перейти к следующему логическому состоянию
        pass

    @abstractmethod
    def cancel_order(self):  # Отменить заказ
        pass

    # Можно добавить другие методы, специфичные для состояний
    # def ship_order(self): raise NotImplementedError("Cannot ship from this state")


# Конкретные состояния
class NewOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Processing payment and moving to 'PROCESSING'.")
        self.order.status = 'PROCESSING'
        self.order.save(update_fields=['status'])
        order_notifier.notify(self.order, 'status_changed')
        # Здесь может быть логика обработки платежа

    def cancel_order(self):
        print(f"Order {self.order.id}: Canceling new order.")
        self.order.status = 'CANCELED'
        self.order.save(update_fields=['status'])
        order_notifier.notify(self.order, 'status_changed')


class ProcessingOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Order processed, moving to 'SHIPPED' (or 'Ready for Pickup').")
        self.order.status = 'SHIPPED'  # Или 'READY_FOR_PICKUP'
        self.order.save(update_fields=['status'])
        order_notifier.notify(self.order, 'status_changed')

    def cancel_order(self):
        # Возможно, отмена на этом этапе требует других действий (возврат средств и т.д.)
        print(f"Order {self.order.id}: Canceling order in processing. (Refund logic would be here)")
        self.order.status = 'CANCELED'
        self.order.save(update_fields=['status'])
        order_notifier.notify(self.order, 'status_changed')


class ShippedOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Order delivered/picked up, moving to 'COMPLETED'.")
        self.order.status = 'COMPLETED'
        self.order.save(update_fields=['status'])
        order_notifier.notify(self.order, 'status_changed')

    def cancel_order(self):  # Обычно нельзя отменить отправленный заказ без последствий
        print(f"Order {self.order.id}: Cannot cancel a shipped order through this simple flow.")
        # Можно реализовать логику возврата
        # raise PermissionError("Cannot cancel a shipped order.")


class CompletedOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Order is already completed. No further steps.")
        # No state change

    def cancel_order(self):
        print(f"Order {self.order.id}: Cannot cancel a completed order.")
        # raise PermissionError("Cannot cancel a completed order.")


class CanceledOrderState(OrderState):
    def process_next_step(self):
        print(f"Order {self.order.id}: Order is canceled. No further steps.")
        # No state change

    def cancel_order(self):
        print(f"Order {self.order.id}: Order is already canceled.")
        # No state change


# Контекст, который использует Состояние
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
            # По умолчанию или ошибка, если статус неизвестен
            print(f"Warning: Unknown order status '{self.order.status}'. Defaulting to NewOrderState.")
            return NewOrderState(self.order)
        return state_class(self.order)

    def refresh_state(self):  # Если статус изменился извне
        self._state = self._get_state_from_order_status()

    def process_next_step(self):
        self._state.process_next_step()
        self.refresh_state()  # Обновляем внутреннее состояние после изменения статуса заказа

    def cancel_order(self):
        self._state.cancel_order()
        self.refresh_state()