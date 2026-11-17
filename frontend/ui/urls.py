from django.urls import path
from .views import home, dashboard, cart_view, orders_view, checkout_view, management_dashboard, management_login, management_authenticate, management_logout, management_products, management_product_create, management_product_edit, management_product_delete
from django.shortcuts import render

urlpatterns = [
    path(
        "management/products/<int:product_id>/delete/",
        management_product_delete,
        name="management-product-delete",
    ),

    path("management/products/", management_products, name="management-products"),
    path(
        "management/products/<int:product_id>/edit/",
        management_product_edit,
        name="management-product-edit",
    ),
    path("management/products/create/", management_product_create, name="management-product-create"),
    path("management/login/", management_login, name="management-login"),
    path("management/authenticate/", management_authenticate, name="management-authenticate"),
    path("management/logout/", management_logout, name="management-logout"),
    path('management/', management_dashboard, name='management-dashboard'),
    path('', home),
    path('dashboard/', dashboard),
    path('login/', lambda request: render(request, 'login.html')),
    path('register/', lambda request: render(request, 'register.html')),
    path('checkout/', checkout_view),
]