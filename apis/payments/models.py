from django.db import models
from apis.users.models import User



# Create your models here.
class UserPayment(models.Model):
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'Paypal'),
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT)
    has_paid = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='stripe')
    stripe_checkout_id = models.CharField(max_length=300, null=True, blank=True)
    paypal_checkout_id = models.CharField(max_length=300, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

