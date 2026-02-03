from django.urls import path
from .views import PartnerUpdate, PartnerState, PartnerOrders

app_name = 'core'

urlpatterns = [
    path('partner/update/', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state/', PartnerState.as_view(), name='partner-state'),
    path('partner/orders/', PartnerOrders.as_view(), name='partner-orders'),
]