from django.urls import path
from .views import home, dashboard, cart_view, orders_view, checkout_view
from django.shortcuts import render

urlpatterns = [
    path('', home),
    path('dashboard/', dashboard),
    path('login/', lambda request: render(request, 'login.html')),
    path('register/', lambda request: render(request, 'register.html')),
    path('checkout/', checkout_view),
]