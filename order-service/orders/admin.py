from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'product_id', 'quantity', 'status']
    list_editable = ['status']   # 👈 allows inline editing
    