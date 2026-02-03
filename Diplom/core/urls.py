from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserLoginView, UserRegistrationView, ProductListView,
    BasketView, ContactViewSet, OrderConfirmView, OrderListView,
    OrderDetailView, PartnerUpdate, PartnerState, PartnerOrders
)
from .views import ConfirmEmailView

router = DefaultRouter()
router.register(r'contacts', ContactViewSet, basename='contact')

app_name = 'core'

urlpatterns = [
    # Аутентификация
    path('user/login/', UserLoginView.as_view(), name='user-login'),
    path('user/register/', UserRegistrationView.as_view(), name='user-register'),
    path('user/confirm-email/', ConfirmEmailView.as_view(), name='confirm-email'),
    # Товары
    path('products/', ProductListView.as_view(), name='product-list'),
    
    # Корзина
    path('basket/', BasketView.as_view(), name='basket'),
    
    # Контакты
    path('', include(router.urls)),
    
    # Заказы
    path('order/confirm/', OrderConfirmView.as_view(), name='order-confirm'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    
    # Партнерские endpoints
    path('partner/update/', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state/', PartnerState.as_view(), name='partner-state'),
    path('partner/orders/', PartnerOrders.as_view(), name='partner-orders'),
    
]