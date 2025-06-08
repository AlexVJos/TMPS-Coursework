from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        from services.notification_service import (
            get_order_notifier,
            EmailNotificationObserver,
            AdminNotificationObserver,
            InventoryAdjustmentObserver
        )

        notifier = get_order_notifier()

        if not any(isinstance(obs, EmailNotificationObserver) for obs in notifier._observers):
            notifier.attach(EmailNotificationObserver())
        if not any(isinstance(obs, AdminNotificationObserver) for obs in notifier._observers):
            notifier.attach(AdminNotificationObserver())
        if not any(isinstance(obs, InventoryAdjustmentObserver) for obs in notifier._observers):
            notifier.attach(InventoryAdjustmentObserver())

        print("OrdersConfig: Observers attached to OrderNotifier.")