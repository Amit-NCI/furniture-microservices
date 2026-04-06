from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    is_approved = models.BooleanField(default=False)