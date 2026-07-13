from django.db import models
from django.utils import timezone


class Order(models.Model):
    STATUS_CHOICES = [
        ('cart', 'Cart'),
        ('placed', 'Placed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    user_id = models.IntegerField()
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255, default='Unknown Product')
    price_at_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    quantity = models.IntegerField(default=1)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='cart'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} — {self.product_name} ({self.status})"