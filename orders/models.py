from django.db import models
from catalog.models import Product
from decimal import Decimal


ORDER_STATUS_CHOICES = [
    ('NEW', 'New'),
    ('PROCESSING', 'Processing'),
    ('SHIPPED', 'Shipped'),
    ('COMPLETED', 'Completed'),
    ('CANCELED', 'Canceled'),
]


class Order(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='NEW'
    )

    final_total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    applied_discount_info = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f'Order {self.id} - {self.first_name} {self.last_name}'

    def get_total_cost_of_items(self):
        return sum(item.get_cost() for item in self.items.all())

    def update_final_price_from_items(self):
        self.final_total_price = self.get_total_cost_of_items()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
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