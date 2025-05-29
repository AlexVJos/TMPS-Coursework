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


class InventoryAdjustmentObserver(OrderObserver): # Новый наблюдатель
    """Уменьшает количество товара на складе при создании заказа."""
    def update(self, order: Order, event_type: str, **kwargs):
        if event_type == 'created':
            print(f"InventoryAdjustment: Adjusting stock for order {order.id}.")
            for item in order.items.all():
                product = item.product
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    product.available = product.stock > 0 # Можно обновить доступность
                    product.save(update_fields=['stock']) # , 'available'
                    print(f"  - Product {product.name}: stock reduced by {item.quantity}, new stock {product.stock}")
                else:
                    # Это серьезная проблема: товара не хватило. Нужна обработка.
                    # В реальном приложении это должно проверяться ДО создания OrderItem,
                    # или заказ должен переходить в спец. статус "ожидание товара".
                    print(f"  - CRITICAL STOCK ERROR: Product {product.name} (ID: {product.id}) - requested {item.quantity}, available {product.stock}")
                    # Здесь можно отправить срочное уведомление администратору,
                    # или инициировать откат транзакции, если это возможно.
        elif event_type == 'canceled_with_stock_return': # Если заказ отменен и товары возвращаются на склад
            print(f"InventoryAdjustment: Returning stock for canceled order {order.id}.")
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.available = True
                product.save(update_fields=['stock']) # , 'available'
                print(f"  - Product {product.name}: stock increased by {item.quantity}, new stock {product.stock}")


class OrderNotifier:
    _instance = None  # Для реализации Синглтона (опционально, но часто для глобальных уведомителей)

    def __new__(cls, *args, **kwargs):  # Синглтон
        if not cls._instance:
            cls._instance = super(OrderNotifier, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._observers: List[OrderObserver] = []
        self._initialized = True
        print("OrderNotifier initialized.")

    def attach(self, observer: OrderObserver):
        if not isinstance(observer, OrderObserver):
            raise TypeError("Attached observer must be an instance of OrderObserver.")
        if observer not in self._observers:
            self._observers.append(observer)
            print(f"Observer {observer.__class__.__name__} attached.")

    def detach(self, observer: OrderObserver):
        try:
            self._observers.remove(observer)
            print(f"Observer {observer.__class__.__name__} detached.")
        except ValueError:
            pass

    def notify(self, order: Order, event_type: str, **kwargs):
        print(f"OrderNotifier: Notifying observers about order {order.id}, event: {event_type}")
        for observer in self._observers:
            try:
                observer.update(order, event_type, **kwargs)
            except Exception as e:
                # Логирование ошибки наблюдателя, чтобы не прерывать остальных
                print(f"Error in observer {observer.__class__.__name__}: {e}")


# Получение экземпляра уведомителя
def get_order_notifier() -> OrderNotifier:
    return OrderNotifier()