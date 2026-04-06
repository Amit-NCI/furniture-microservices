from django.db import models

class Order(models.Model):
    STATUS_CHOICES = [
        ('cart', 'Cart'),
        ('placed', 'Placed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]

    user_id = models.IntegerField()
    product_id = models.IntegerField()
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='cart')