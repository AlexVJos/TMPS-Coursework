from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional


class DiscountStrategy(ABC):
    @abstractmethod
    def calculate_discount(self, order_total: Decimal,
                           cart_items: Optional[list] = None) -> Decimal:  # cart_items - список словарей товаров
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass


class NoDiscountStrategy(DiscountStrategy):
    def calculate_discount(self, order_total: Decimal, cart_items: Optional[list] = None) -> Decimal:
        return Decimal('0.00')

    def get_description(self) -> str:
        return "No discount applied."


class PercentageDiscountStrategy(DiscountStrategy):
    def __init__(self, percentage: Decimal, description_template: str = "{percentage}% Off"):
        if not (0 <= percentage <= 100):
            raise ValueError("Percentage must be between 0 and 100.")
        self.percentage = percentage
        self.description_template = description_template

    def calculate_discount(self, order_total: Decimal, cart_items: Optional[list] = None) -> Decimal:
        return (order_total * self.percentage) / Decimal('100')

    def get_description(self) -> str:
        return self.description_template.format(percentage=self.percentage)


class FixedAmountDiscountStrategy(DiscountStrategy):
    def __init__(self, amount: Decimal, description_template: str = "${amount} Off"):
        if amount < 0:
            raise ValueError("Discount amount cannot be negative.")
        self.amount = amount
        self.description_template = description_template

    def calculate_discount(self, order_total: Decimal, cart_items: Optional[list] = None) -> Decimal:
        return min(self.amount, order_total)

    def get_description(self) -> str:
        return self.description_template.format(amount=self.amount)


class DiscountAllocator(ABC):
    """
    Абстрактный Создатель. Он определяет операцию, которая использует фабричный метод
    для получения объекта-продукта (стратегии скидки).
    """

    def get_discount_strategy(self, order_total: Decimal, cart_items: Optional[list] = None,
                              **kwargs) -> DiscountStrategy:
        strategy = self._create_discount_strategy(order_total, cart_items, **kwargs)
        return strategy

    @abstractmethod
    def _create_discount_strategy(self, order_total: Decimal, cart_items: Optional[list] = None,
                                  **kwargs) -> DiscountStrategy:
        """Абстрактный Фабричный Метод."""
        pass


class DefaultOrderDiscountAllocator(DiscountAllocator):
    """
    Конкретный Создатель, применяющий скидки по объему заказа.
    """

    def _create_discount_strategy(self, order_total: Decimal, cart_items: Optional[list] = None,
                                  **kwargs) -> DiscountStrategy:
        if order_total > Decimal('100.00'):
            return PercentageDiscountStrategy(percentage=Decimal('15'), description_template="15% Off (Order > $100)")
        elif order_total > Decimal('50.00'):
            return PercentageDiscountStrategy(percentage=Decimal('10'), description_template="10% Off (Order > $50)")
        elif order_total > Decimal('20.00'):
            return FixedAmountDiscountStrategy(amount=Decimal('3'), description_template="$3 Off (Order > $20)")
        return NoDiscountStrategy()


class PromoCodeDiscountAllocator(DiscountAllocator):
    """
    Конкретный Создатель, применяющий скидки по промокоду.
    """

    def __init__(self, promo_code: Optional[str]):
        self.promo_code = promo_code.upper() if promo_code else None

    def _create_discount_strategy(self, order_total: Decimal, cart_items: Optional[list] = None,
                                  **kwargs) -> DiscountStrategy:
        if not self.promo_code:
            return NoDiscountStrategy()

        if self.promo_code == "BAKERYLOVE15":
            return PercentageDiscountStrategy(percentage=Decimal('15'),
                                              description_template="15% Off with Promo BAKERYLOVE15")
        elif self.promo_code == "FRESH5":
            return FixedAmountDiscountStrategy(amount=Decimal('5'), description_template="$5 Off with Promo FRESH5")

        print(f"Warning: Promo code '{self.promo_code}' not recognized.")
        return NoDiscountStrategy()