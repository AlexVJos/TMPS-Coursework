from abc import ABC, abstractmethod
from orders.models import Order # Для type hinting


class OrderObserver(ABC):
    @abstractmethod
    def update(self, order: Order, event_type: str): # event_type может быть 'created', 'status_changed'
        pass


class EmailNotificationObserver(OrderObserver):
    def update(self, order: Order, event_type: str):
        if event_type == 'created':
            print(f"SIMULATING: Sending email to {order.email} for new order {order.id}.")
        elif event_type == 'status_changed':
            print(f"SIMULATING: Sending email to {order.email} for order {order.id} status update: {order.status}.")
        # В реальном приложении здесь была бы логика отправки email

class AdminNotificationObserver(OrderObserver):
    def update(self, order: Order, event_type: str):
        if event_type == 'created':
            print(f"SIMULATING: Notifying admin about new order {order.id}.")
        # Можно логировать или отправлять уведомление в админ-панель


class OrderNotifier:
    def __init__(self):
        self._observers: list[OrderObserver] = []

    def attach(self, observer: OrderObserver):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: OrderObserver):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass # Observer not found

    def notify(self, order: Order, event_type: str):
        print(f"OrderNotifier: Notifying observers about order {order.id}, event: {event_type}")
        for observer in self._observers:
            observer.update(order, event_type)


order_notifier = OrderNotifier()

order_notifier.attach(EmailNotificationObserver())
order_notifier.attach(AdminNotificationObserver())