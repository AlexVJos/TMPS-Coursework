from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['price', 'get_cost_display']

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

    add_fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'address', 'postal_code', 'city')
        }),
        ('Order Status & Pricing (calculated on save)', {
            'fields': ('status', 'final_total_price', 'applied_discount_info')
        }),
    )

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
        if not obj:
            return self.add_fieldsets
        return self.edit_fieldsets

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('created_at', 'updated_at', 'final_total_price', 'applied_discount_info',
                    'first_name', 'last_name', 'email', 'address', 'postal_code', 'city')
        return ()

    def final_total_price_display(self, obj):
        return f"${obj.final_total_price:.2f}" if obj.final_total_price is not None else "N/A"

    final_total_price_display.short_description = 'Total Price'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order_link', 'product_link', 'price_display', 'quantity',
                    'get_cost_display']
    list_filter = ['product']
    search_fields = ['order__id', 'product__name']
    readonly_fields = ['price', 'get_cost_display']
    def get_cost_display(self, obj):
        cost = obj.get_cost()
        return f"${cost:.2f}" if cost is not None else "N/A"

    get_cost_display.short_description = 'Item Total'

    def price_display(self, obj):
        return f"${obj.price:.2f}" if obj.price is not None else "N/A"

    price_display.short_description = 'Unit Price'

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