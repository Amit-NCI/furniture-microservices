from django.urls import path

from .views import (
    ProductList,
    ProductDetail,
    ProductUpdate,
    ProductDelete,
)

urlpatterns = [
    # Public APIs
    path("", ProductList.as_view()),
    path("<int:pk>/", ProductDetail.as_view()),

    # Staff APIs
    path("update/<int:pk>/", ProductUpdate.as_view()),
    path("delete/<int:pk>/", ProductDelete.as_view()),
]