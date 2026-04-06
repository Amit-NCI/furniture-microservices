# users/admin.py
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'is_approved')
    list_filter = ('role', 'is_approved')