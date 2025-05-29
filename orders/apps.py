from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        # Импортируем здесь, чтобы избежать циклических зависимостей на уровне модуля
        from services.notification_service import (
            get_order_notifier,
            EmailNotificationObserver,
            AdminNotificationObserver,
            InventoryAdjustmentObserver  # Новый наблюдатель
        )

        notifier = get_order_notifier()

        # Проверяем, чтобы не дублировать при перезагрузке сервера разработки
        # Это простая проверка, в сложных случаях может потребоваться более надежный механизм
        if not any(isinstance(obs, EmailNotificationObserver) for obs in notifier._observers):
            notifier.attach(EmailNotificationObserver())
        if not any(isinstance(obs, AdminNotificationObserver) for obs in notifier._observers):
            notifier.attach(AdminNotificationObserver())
        if not any(isinstance(obs, InventoryAdjustmentObserver) for obs in notifier._observers):
            notifier.attach(InventoryAdjustmentObserver())

        print("OrdersConfig: Observers attached to OrderNotifier.")