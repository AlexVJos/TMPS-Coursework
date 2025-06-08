from abc import ABC, abstractmethod
from decimal import Decimal
from catalog.models import Product


class PricedItem(ABC):
    @abstractmethod
    def get_price(self) -> Decimal:
        pass

    @abstractmethod
    def get_description_suffix(self) -> str:
        pass

    @abstractmethod
    def get_base_product(self) -> Product:
        pass

class StandardProductItem(PricedItem):
    def __init__(self, product: Product):
        self._product = product

    def get_price(self) -> Decimal:
        return self._product.price

    def get_description_suffix(self) -> str:
        return ""

    def get_base_product(self) -> Product:
        return self._product

class ProductOptionDecorator(PricedItem, ABC):
    def __init__(self, wrapped_item: PricedItem):
        self._wrapped_item = wrapped_item

    def get_price(self) -> Decimal:
        return self._wrapped_item.get_price()

    def get_description_suffix(self) -> str:
        return self._wrapped_item.get_description_suffix()

    def get_base_product(self) -> Product:
        return self._wrapped_item.get_base_product()


class GiftWrapDecorator(ProductOptionDecorator):
    def __init__(self, wrapped_item: PricedItem, gift_wrap_cost: Decimal = Decimal('2.50')):
        super().__init__(wrapped_item)
        self._gift_wrap_cost = gift_wrap_cost

    def get_price(self) -> Decimal:
        return super().get_price() + self._gift_wrap_cost

    def get_description_suffix(self) -> str:
        return super().get_description_suffix() + " (Gift Wrapped)"


class ExpressAssemblyDecorator(ProductOptionDecorator):
    def __init__(self, wrapped_item: PricedItem, assembly_surcharge_percent: Decimal = Decimal('5.0')):  # 5% наценка
        super().__init__(wrapped_item)
        self._assembly_surcharge_percent = assembly_surcharge_percent

    def get_price(self) -> Decimal:
        base_price = super().get_price()
        surcharge = (base_price * self._assembly_surcharge_percent) / Decimal('100')
        return base_price + surcharge.quantize(Decimal('0.01'))

    def get_description_suffix(self) -> str:
        return super().get_description_suffix() + f" (Express Assembly +{self._assembly_surcharge_percent}%)"