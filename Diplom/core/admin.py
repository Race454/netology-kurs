from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Shop, Category, Product, ProductInfo, 
    Parameter, ProductParameter, Contact, Order, 
    OrderItem, ConfirmEmailToken
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'type', 'is_staff')
    list_filter = ('type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'company', 'position', 'type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'type'),
        }),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'user', 'state')
    list_filter = ('state',)
    search_fields = ('name', 'url')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('shops',)
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'price', 'quantity', 'external_id')
    list_filter = ('shop',)
    search_fields = ('product__name', 'model')


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ('product_info', 'parameter', 'value')
    list_filter = ('parameter',)
    search_fields = ('value', 'parameter__name')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'value')
    list_filter = ('type',)
    search_fields = ('user__email', 'value')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'status_badge', 'get_total_price')
    list_filter = ('status', 'dt', 'user__type')
    search_fields = ('user__email', 'id')
    readonly_fields = ('dt',)
    list_select_related = ('user', 'contact')
    
    def status_badge(self, obj):
        """Отображение статуса в виде цветного бейджа"""
        colors = {
            'basket': '#95a5a6',
            'new': '#3498db', 
            'confirmed': '#2ecc71',
            'assembled': '#f39c12',
            'sent': '#9b59b6',
            'delivered': '#27ae60',
            'canceled': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: 500;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def get_total_price(self, obj):
        # Отображение общей суммы заказа
        total = obj.get_total_price()
        return f'{total:,} ₽'.replace(',', ' ')
    get_total_price.short_description = 'Сумма'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'shop', 'quantity', 'get_item_price')
    list_filter = ('shop',)
    search_fields = ('product__name', 'order__id')
    
    def get_item_price(self, obj):
        price = obj.get_item_price()
        return f'{price:,} ₽'.replace(',', ' ')
    get_item_price.short_description = 'Сумма'


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    search_fields = ('user__email', 'key')