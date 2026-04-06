"""
URL configuration for order_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from orders.views import ClearCart, CreateOrder, GetUserOrders, CartList, Checkout, OrderHistory, CheckoutView, RemoveSelectedItems, UpdateQuantity
from orders.views import DeleteCartItem
urlpatterns = [
    path('admin/', admin.site.urls),

    # Add to cart (POST)
    path('api/orders/', CreateOrder.as_view()),

    # Get orders by user
    path('api/orders/<int:user_id>/', GetUserOrders.as_view()),

    # Get cart items
    path('api/cart/', CartList.as_view()),

     # ✅ NEW CHECKOUT API
    path('api/checkout/<int:user_id>/', Checkout.as_view()),
    

     # ✅ NEW
    path('api/orders/history/<int:user_id>/', OrderHistory.as_view()),
    # ✅ NEW DELETE CART ITEM
    path('api/cart/<int:order_id>/', DeleteCartItem.as_view()),

    path('api/cart/update/<int:order_id>/', UpdateQuantity.as_view()),

    path('api/cart/remove-selected/<int:user_id>/', RemoveSelectedItems.as_view()),
    path('api/cart/clear/<int:user_id>/', ClearCart.as_view()),
]