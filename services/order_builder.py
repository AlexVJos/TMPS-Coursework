from decimal import Decimal
from orders.models import Order, OrderItem
from cart.cart import Cart  # Нужен для получения товаров
from .discount_strategies import DiscountStrategy, NoDiscountStrategy  # Для применения скидки


class OrderBuilder:
    def __init__(self):
        self._order_data = {}
        self._order_items_data = []
        self._discount_strategy: DiscountStrategy = NoDiscountStrategy()  # По умолчанию без скидки
        self._cart_instance = None

    def set_customer_details(self, first_name: str, last_name: str, email: str,
                             address: str, postal_code: str, city: str):
        self._order_data['first_name'] = first_name
        self._order_data['last_name'] = last_name
        self._order_data['email'] = email
        self._order_data['address'] = address
        self._order_data['postal_code'] = postal_code
        self._order_data['city'] = city
        return self

    def set_cart(self, cart: Cart):
        self._cart_instance = cart
        for item in cart:  # cart.__iter__() возвращает элементы с product_obj
            self._order_items_data.append({
                'product': item['product_obj'],
                'price': item['price'],  # Цена из корзины (на момент добавления)
                'quantity': item['quantity']
            })
        return self

    def set_discount_strategy(self, strategy: DiscountStrategy):
        self._discount_strategy = strategy
        return self

    def _calculate_prices(self):
        if not self._order_items_data:
            raise ValueError("Cannot build order without items.")

        total_items_cost = sum(
            item['price'] * item['quantity'] for item in self._order_items_data
        )

        discount_amount = self._discount_strategy.calculate_discount(total_items_cost, self._cart_instance)
        final_total_price = total_items_cost - discount_amount

        # Убедимся, что цена не отрицательная
        final_total_price = max(final_total_price, Decimal('0.00'))

        return total_items_cost, discount_amount, final_total_price

    def build(self) -> Order:
        if not self._order_data or not self._order_items_data:
            raise ValueError("Customer details and cart items must be set before building.")

        total_items_cost, discount_amount, final_total_price = self._calculate_prices()

        # Создаем объект Order
        order = Order.objects.create(
            **self._order_data,  # Передаем данные клиента
            final_total_price=final_total_price,
            applied_discount_info=self._discount_strategy.get_description()
            # Статус по умолчанию 'NEW' из модели
        )

        # Создаем OrderItem'ы
        for item_data in self._order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                price=item_data['price'],
                quantity=item_data['quantity']
            )

        # После создания заказа, его можно передать в систему уведомлений (паттерн Наблюдатель)
        # или изменить его состояние (паттерн Состояние)
        return order