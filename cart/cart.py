from decimal import Decimal
from django.conf import settings
from catalog.models import Product


class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart_data = self.session.get(settings.CART_SESSION_ID)
        if not cart_data:
            cart_data = self.session[settings.CART_SESSION_ID] = {}
        self.cart_data = cart_data

    def add(self, product, quantity=1, update_quantity=False):
        """
        Add a product to the cart or update its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart_data:
            self.cart_data[product_id] = {'quantity': 0, 'price': str(product.price)}

        if update_quantity:
            self.cart_data[product_id]['quantity'] = quantity
        else:
            self.cart_data[product_id]['quantity'] += quantity

        if self.cart_data[product_id]['quantity'] <= 0:
            self.remove(product)
        else:
            self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        """
        product_id = str(product.id)
        if product_id in self.cart_data:
            del self.cart_data[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        product_ids = self.cart_data.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart_data.copy()

        for product in products:
            cart[str(product.id)]['product_obj'] = product

        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart_data.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart_data.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_item(self, product_id):
        """
        Get a specific item from the cart by product_id.
        Returns None if item not found.
        """
        product_id_str = str(product_id)
        if product_id_str in self.cart_data:
            return self.cart_data[product_id_str]
        return None