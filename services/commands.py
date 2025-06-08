from abc import ABC, abstractmethod
from django.http import HttpRequest
from cart.cart import Cart
from catalog.models import Product
from django.shortcuts import get_object_or_404


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

class AddToCartCommand(Command):
    def __init__(self, request: HttpRequest, product_id: int, quantity: int, update_quantity: bool = False):
        self.request = request
        self.product_id = product_id
        self.quantity = quantity
        self.update_quantity = update_quantity
        self._cart = None
        self._product = None

    def _initialize(self):
        if not self._cart:
            self._cart = Cart(self.request)
        if not self._product:
            self._product = get_object_or_404(Product, id=self.product_id)

    def execute(self):
        self._initialize()
        if self.quantity <= 0:
            print(f"Command Error: Quantity for product {self.product_id} must be positive.")
            return False

        self._cart.add(
            product=self._product,
            quantity=self.quantity,
            update_quantity=self.update_quantity
        )
        print(f"AddToCartCommand: Product {self._product.name} (Qty: {self.quantity}) added/updated in cart.")
        return True
