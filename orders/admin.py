from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['price', 'get_cost_display']  # Изменил get_cost на get_cost_display

    def get_cost_display(self, obj):
        cost = obj.get_cost()
        return f"${cost:.2f}" if cost is not None else "N/A"

    get_cost_display.short_description = 'Item Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email',
                    'status', 'created_at', 'final_total_price_display', 'applied_discount_info']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'first_name', 'last_name', 'email']
    inlines = [OrderItemInline]

    # Базовые поля, которые всегда только для чтения (если объект уже существует)
    # или не должны быть в форме добавления
    # base_readonly_fields = ('created_at', 'updated_at', 'final_total_price', 'applied_discount_info')

    # Определим fieldsets без auto_now/auto_now_add полей для формы добавления
    add_fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'address', 'postal_code', 'city')
        }),
        ('Order Status & Pricing (calculated on save)', {  # Уточнение для админа
            'fields': ('status', 'final_total_price', 'applied_discount_info')
            # 'final_total_price' и 'applied_discount_info' лучше рассчитывать при сохранении,
            # а не давать админу вводить вручную при создании через админку.
            # Для простоты курсовой можно оставить, но это не идеально.
        }),
    )

    # Fieldsets для формы изменения, где можно показать Timestamps
    edit_fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'address', 'postal_code', 'city')
        }),
        ('Order Status & Pricing', {
            'fields': ('status', 'final_total_price', 'applied_discount_info')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:  # Форма добавления
            return self.add_fieldsets
        return self.edit_fieldsets  # Форма изменения

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Форма изменения
            # Почти все поля делаем readonly после создания, т.к. заказы должны управляться через бизнес-логику
            return ('created_at', 'updated_at', 'final_total_price', 'applied_discount_info',
                    'first_name', 'last_name', 'email', 'address', 'postal_code', 'city')
            # Статус можно оставить редактируемым, если это нужно через стандартную админку,
            # но у нас есть кастомная страница для этого.
        return ()  # На форме добавления нет readonly полей из этого списка

    def final_total_price_display(self, obj):
        return f"${obj.final_total_price:.2f}" if obj.final_total_price is not None else "N/A"

    final_total_price_display.short_description = 'Total Price'

    # Если мы хотим, чтобы при сохранении заказа из админки (особенно нового)
    # final_total_price рассчитывался, нам нужен метод save_model или save_formset.
    # Однако, создание заказов через админку - это не основной сценарий для этого проекта,
    # основной флоу через сайт и OrderBuilder.
    # Поэтому для простоты оставим как есть. Если админ создает заказ вручную,
    # он должен будет сам корректно заполнить цены.


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order_link', 'product_link', 'price_display', 'quantity',
                    'get_cost_display']  # Обновил для ссылок и форматирования
    list_filter = ['product']
    search_fields = ['order__id', 'product__name']
    readonly_fields = ['price', 'get_cost_display']  # 'price' должно быть установлено при создании

    def get_cost_display(self, obj):
        cost = obj.get_cost()
        return f"${cost:.2f}" if cost is not None else "N/A"

    get_cost_display.short_description = 'Item Total'

    def price_display(self, obj):
        return f"${obj.price:.2f}" if obj.price is not None else "N/A"

    price_display.short_description = 'Unit Price'

    # Добавим ссылки для удобства
    def order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse("admin:orders_order_change", args=[obj.order.id])
        return format_html('<a href="{}">Order #{}</a>', link, obj.order.id)

    order_link.short_description = 'Order'

    def product_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.product:
            link = reverse("admin:catalog_product_change", args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', link, obj.product.name)
        return "N/A"

    product_link.short_description = 'Product'