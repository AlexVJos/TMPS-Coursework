from django.db import models
from django.conf import settings  # Для связи с User, если потребуется
from catalog.models import Product
from decimal import Decimal

# Статусы заказа - хорошая основа для паттерна Состояние
# Но для простоты курсовой, начнем с CharField, а сам паттерн Состояние
# реализуем на уровне сервиса, управляющего логикой перехода между статусами.
# Если бы статусов было много и логика была сложной в самой модели,
# то паттерн Состояние мог бы быть реализован прямо в модели через ForeignKey к модели State.
ORDER_STATUS_CHOICES = [
    ('NEW', 'New'),
    ('PROCESSING', 'Processing'),
    ('SHIPPED', 'Shipped'),  # Для пекарни это может быть "Ready for pickup" или "Delivering"
    ('COMPLETED', 'Completed'),
    ('CANCELED', 'Canceled'),
]


class Order(models.Model):
    # Если у вас будет аутентификация, можно раскомментировать:
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=250)  # Упрощенный адрес
    postal_code = models.CharField(max_length=20)  # Опционально
    city = models.CharField(max_length=100)  # Опционально

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='NEW'
    )
    # total_price будет рассчитываться. Можно хранить его для истории.
    # Мы будем использовать DecimalField для точности
    # total_price_before_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    # discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    final_total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Поле для информации о примененной скидке (для паттерна Стратегия)
    applied_discount_info = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f'Order {self.id} - {self.first_name} {self.last_name}'

    def get_total_cost_of_items(self):
        return sum(item.get_cost() for item in self.items.all())

    # Метод для обновления общей стоимости, может быть вызван при создании или изменении заказа
    # Этот метод не будет учитывать скидку, скидка будет применяться отдельно сервисом
    def update_final_price_from_items(self):
        self.final_total_price = self.get_total_cost_of_items()
        # self.save(update_fields=['final_total_price']) # Осторожно с save в методах модели, может вызвать рекурсию


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена товара на момент заказа
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        return Decimal('0.00')