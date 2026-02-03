from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.show_catalog, name='catalog'), 
    path('<slug:slug>/', views.show_product, name='product'),
]