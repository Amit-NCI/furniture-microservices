from django.urls import path

from .views import (
    ProductList,
    ProductDetail,
    ProductUpdate,
    ProductDelete,
    AdminProductList,
    AdminProductUpdate,
)

urlpatterns = [
    # Public APIs
    path("admin/", AdminProductList.as_view(), name="admin-product-list"),
    path(
        "admin/<int:pk>/",
        AdminProductUpdate.as_view(),
        name="admin-product-update",
    ),
    path("", ProductList.as_view()),
    path("<int:pk>/", ProductDetail.as_view()),

    # Staff APIs
    path("update/<int:pk>/", ProductUpdate.as_view()),
    path("delete/<int:pk>/", ProductDelete.as_view()),
]