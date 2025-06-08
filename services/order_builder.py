from decimal import Decimal

from django.db import transaction

from orders.models import Order, OrderItem
from cart.cart import Cart
from .discount_strategies import DiscountStrategy, NoDiscountStrategy


class OrderBuilder:
    def __init__(self):
        self._order_data = {}
        self._order_items_data = []
        self._discount_strategy: DiscountStrategy = NoDiscountStrategy()
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
        for item in cart:
            self._order_items_data.append({
                'product': item['product_obj'],
                'price': item['price'],
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

        final_total_price = max(final_total_price, Decimal('0.00'))

        return total_items_cost, discount_amount, final_total_price

    @transaction.atomic
    def build(self) -> Order:
        if not self._order_data or not self._order_items_data:
            raise ValueError("Customer details and cart items must be set before building.")

        total_items_cost, discount_amount, final_total_price = self._calculate_prices()

        order = Order.objects.create(
            **self._order_data,
            final_total_price=final_total_price,
            applied_discount_info=self._discount_strategy.get_description()
        )

        for item_data in self._order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                price=item_data['price'],
                quantity=item_data['quantity']
            )

        return order