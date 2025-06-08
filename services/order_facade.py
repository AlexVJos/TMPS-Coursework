from typing import Optional

from django.http import HttpRequest
from orders.models import Order
from cart.cart import Cart
from .order_builder import OrderBuilder
from .discount_strategies import (
    DiscountAllocator,
    DefaultOrderDiscountAllocator,
    PromoCodeDiscountAllocator,
    NoDiscountStrategy
)
from .notification_service import get_order_notifier
from decimal import Decimal


class OrderPlacementFacade:
    def __init__(self, request: HttpRequest):
        self.request = request
        self.cart = Cart(request)

    def place_order(self, form_data: dict) -> tuple[Optional[Order], Optional[list]]:
        """
        Processes order placement.
        Returns a tuple (order_object, errors_list)
        order_object is None if placement failed.
        errors_list contains error messages if any.
        """
        if not self.cart:
            return None, ["Your cart is empty."]

        builder = OrderBuilder()
        builder.set_customer_details(
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            email=form_data['email'],
            address=form_data['address'],
            postal_code=form_data['postal_code'],
            city=form_data['city']
        )
        builder.set_cart(self.cart)

        current_total = self.cart.get_total_price()

        cart_items_for_discount = [
            {'product_id': item['product_obj'].id,
             'name': item['product_obj'].name,
             'price': item.get('price_decimal', Decimal(item['price'])),
             'quantity': item['quantity']}
            for item in self.cart
        ]

        selected_discount_strategy = None
        promo_code_value = form_data.get('promo_code')

        if promo_code_value:
            allocator: DiscountAllocator = PromoCodeDiscountAllocator(promo_code=promo_code_value)
            strategy_from_promo = allocator.get_discount_strategy(current_total, cart_items_for_discount)
            if not isinstance(strategy_from_promo, NoDiscountStrategy):
                selected_discount_strategy = strategy_from_promo

        if not selected_discount_strategy:
            allocator: DiscountAllocator = DefaultOrderDiscountAllocator()
            selected_discount_strategy = allocator.get_discount_strategy(current_total, cart_items_for_discount)

        if selected_discount_strategy and not isinstance(selected_discount_strategy, NoDiscountStrategy):
            builder.set_discount_strategy(selected_discount_strategy)

        try:
            order = builder.build()

            notifier = get_order_notifier()
            notifier.notify(order, 'created')

            self.cart.clear()

            return order, None
        except ValueError as e:
            return None, [str(e)]
        except Exception as e:
            print(f"Unexpected error during order placement: {e}")
            return None, ["An unexpected error occurred. Please try again."]