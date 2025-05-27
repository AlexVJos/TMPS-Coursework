from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent_name']  # Добавил parent_name для наглядности
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

    def parent_name(self, obj):
        return obj.parent.name if obj.parent else None

    parent_name.short_description = 'Parent Category'  # Название колонки в админке


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category_name', 'price', 'stock', 'available', 'created_at', 'updated_at']
    list_filter = ['available', 'created_at', 'updated_at', 'category']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'category__name']  # Поиск также по имени категории

    def category_name(self, obj):
        return obj.category.name

    category_name.short_description = 'Category'  # Название колонки