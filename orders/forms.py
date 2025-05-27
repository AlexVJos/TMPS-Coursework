from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    promo_code = forms.CharField(
        max_length=50,
        required=False,
        label="Promotional Code",
        widget=forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Enter promo code (optional)'})
    )

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']
        # Можно настроить виджеты, если нужно
        # widgets = {
        #     'address': forms.Textarea(attrs={'rows': 3}),
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control mb-2'}) # Добавим Bootstrap классы