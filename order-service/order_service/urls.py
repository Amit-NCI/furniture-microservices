from django.contrib import admin
from django.urls import path
from orders.views import (
    CreateOrder,
    GetUserOrders,
    CartList,
    Checkout,
    OrderHistory,
    DeleteCartItem,
    UpdateQuantity,
    RemoveSelectedItems,
    ClearCart,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/orders/', CreateOrder.as_view()),
    path('api/orders/<int:user_id>/', GetUserOrders.as_view()),
    path('api/cart/', CartList.as_view()),
    path('api/checkout/<int:user_id>/', Checkout.as_view()),
    path('api/orders/history/<int:user_id>/', OrderHistory.as_view()),
    path('api/cart/<int:order_id>/', DeleteCartItem.as_view()),
    path('api/cart/update/<int:order_id>/', UpdateQuantity.as_view()),
    path('api/cart/remove-selected/<int:user_id>/', RemoveSelectedItems.as_view()),
    path('api/cart/clear/<int:user_id>/', ClearCart.as_view()),
]
