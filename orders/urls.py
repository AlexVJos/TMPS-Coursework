from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('created/', views.order_created_success, name='order_created_success'),

    # URL-ы для "админки" управления заказами (для демонстрации паттерна Состояние)
    path('admin/order/<int:order_id>/', views.admin_order_detail_view, name='admin_order_detail'),
    path('admin/orders/', views.admin_order_list, name='admin_order_list'),
]