from .models import *
from apis.users.models import User
from rest_framework import serializers
from apis.users.serializers import UserSerializer




class UserPaymentSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(
    #     queryset=User.objects.all().filter(
    #         is_deleted=False
    #     ),
    #     allow_null=False,
    #     allow_empty=False,
    #     required=True,
    #     write_only=True
    # )
    user_profile = serializers.SerializerMethodField(read_only=True)
    
    
    class Meta:
        model = UserPayment
        fields = ['id', 'user', 'user_profile', 'has_paid', 'amount', 'stripe_checkout_id', 'paypal_checkout_id']
        read_only_fields = ['user_profile', 'user', 'stripe_checkout_id', 'paypal_checkout_id', 'has_paid']
        # write_only_fields = ['user']
        # depth = 1
        
    def get_user_profile(self, obj):
        sender = obj.user
        if sender:
            return UserSerializer(sender).data
        return None
    
    
    
class PayPalPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


