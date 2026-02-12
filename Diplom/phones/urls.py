from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.show_catalog, name='catalog'), 
    path('basket/', views.basket_view, name='basket'),
    path('<slug:slug>/', views.show_product, name='product'),
]