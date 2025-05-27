from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from .models import Order
from .forms import OrderCreateForm
from cart.cart import Cart

from services.order_builder import OrderBuilder
from services.notification_service import order_notifier
from services.order_state_machine import OrderContext
from services.discount_strategies import (
    DefaultOrderDiscountAllocator,
    PromoCodeDiscountAllocator,
    NoDiscountStrategy
)


def order_create(request):
    cart = Cart(request)
    if not cart:  # Если корзина пуста
        return redirect('catalog:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # Используем Строителя для создания заказа
            builder = OrderBuilder()

            # 1. Устанавливаем детали клиента
            builder.set_customer_details(
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data['address'],
                postal_code=form.cleaned_data['postal_code'],
                city=form.cleaned_data['city']
            )

            # 2. Устанавливаем корзину
            builder.set_cart(cart)

            # 3. Устанавливаем стратегию скидки (пример)
            current_total = cart.get_total_price()  # Это Decimal
            cart_items_for_discount = [  # Упрощенное представление корзины для стратегий
                {'product_id': item['product_obj'].id, 'price': item['price'], 'quantity': item['quantity']}
                for item in cart
            ]

            selected_discount_strategy = None

            # Пример: если введен промокод (предположим, он есть в форме)
            promo_code_value = form.cleaned_data.get('promo_code')  # Нужно добавить поле в OrderCreateForm

            if promo_code_value:
                promo_allocator = PromoCodeDiscountAllocator(promo_code=promo_code_value)
                strategy_from_promo = promo_allocator.get_discount_strategy(current_total, cart_items_for_discount)
                # Применяем скидку от промокода, если она не NoDiscountStrategy
                if not isinstance(strategy_from_promo, NoDiscountStrategy):
                    selected_discount_strategy = strategy_from_promo

            # Если промокод не дал скидку или не был введен, применяем стандартные скидки
            if not selected_discount_strategy:
                default_allocator = DefaultOrderDiscountAllocator()
                selected_discount_strategy = default_allocator.get_discount_strategy(current_total,
                                                                                     cart_items_for_discount)

            if selected_discount_strategy and not isinstance(selected_discount_strategy, NoDiscountStrategy):
                builder.set_discount_strategy(selected_discount_strategy)

            # 4. Строим заказ
            try:
                order = builder.build()

                # 5. Уведомляем наблюдателей о создании заказа
                order_notifier.notify(order, 'created')

                # 6. Очищаем корзину
                cart.clear()

                # Сохраняем ID заказа в сессии для страницы "Спасибо"
                request.session['order_id'] = order.id
                # Редирект на страницу оплаты или "спасибо"
                return redirect(reverse('orders:order_created_success'))

            except ValueError as e:
                # Обработка ошибок от строителя (например, пустая корзина)
                # Хотя мы проверяем корзину выше, но для полноты
                form.add_error(None, str(e))  # Добавляем ошибку к форме

    else:  # GET request
        form = OrderCreateForm()
        # Можно передать начальные данные, если пользователь авторизован
        # if request.user.is_authenticated:
        #     form = OrderCreateForm(initial={
        #         'first_name': request.user.first_name,
        #         'last_name': request.user.last_name,
        #         'email': request.user.email,
        #     })

    # Для отображения текущей корзины и общей суммы на странице оформления
    context = {
        'cart': cart,
        'form': form
    }
    return render(request, 'orders/order/create.html', context)


def order_created_success(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('catalog:product_list')  # Если нет ID заказа, что-то пошло не так

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        # Обработка случая, если заказ не найден (маловероятно, но возможно)
        return redirect('catalog:product_list')

    # Можно очистить order_id из сессии, если он больше не нужен
    # del request.session['order_id']

    return render(request, 'orders/order/created.html', {'order': order})


# Пример view для админа для изменения статуса заказа (демонстрация паттерна Состояние)
@staff_member_required  # Только для персонала/администраторов
def admin_order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_context = OrderContext(order)  # Используем OrderContext для управления состоянием

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'process_next':
            order_context.process_next_step()
        elif action == 'cancel':
            order_context.cancel_order()
        return redirect('orders:admin_order_detail', order_id=order.id)

    context = {
        'order': order,
        'order_context': order_context  # Передаем контекст для отображения возможных действий
    }
    return render(request, 'orders/admin/order_detail.html', context)


# Список заказов для админа (очень простой)
@staff_member_required
def admin_order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'orders/admin/order_list.html', {'orders': orders})