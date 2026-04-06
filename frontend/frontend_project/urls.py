"""
URL configuration for frontend_project project.

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
from django.urls import path, include
from ui import views
from ui.views import checkout_view 

urlpatterns = [
    path('admin/', admin.site.urls),

    # Connect UI app
    path('', include('ui.urls')),
     # ✅ ADD THIS
    path('cart/', views.cart_view),
    # ✅ NEW: checkout page
    path('orders/', views.orders_view),
    # ✅ ADD THIS
    path('checkout/', checkout_view),
]