from django import forms

# Ограничим максимальное количество товара, которое можно добавить за раз
PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)] # от 1 до 20

class CartAddProductForm(forms.Form):
    quantity = forms.TypedChoiceField(
        choices=PRODUCT_QUANTITY_CHOICES,
        coerce=int, # Преобразовать значение в int
        label='Quantity'
    )
    # Скрытое поле, чтобы различать добавление и полное обновление количества
    update_quantity = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )