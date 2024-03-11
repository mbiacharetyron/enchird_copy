from django.contrib import admin
from .models import UserPayment



# Register your models here. 

@admin.register(UserPayment)
class UserPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'id', 'has_paid', 'amount', 'status', 'payment_method', 'stripe_checkout_id', 'paypal_checkout_id', 'created_at', 'updated_at')
    search_fields = ('user__username', 'status', 'payment_method')
    

