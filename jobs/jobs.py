import os
import logging
import tempfile
from io import BytesIO
from django.conf import settings
from django.utils import timezone
from apis.users.models import User
from datetime import datetime, timedelta
from apis.payments.models import UserPayment
from apis.payments.paypal import check_paypal_order



logger = logging.getLogger("myLogger")


def check_paypal_payments():
    # retention_period = timedelta(days=30)
    pending_paypal_payments = UserPayment.objects.filter(has_paid=False, status="pending", payment_method="paypal")

    for payment in pending_paypal_payments:
        print(payment)
        txn_id = payment.paypal_checkout_id
        
        client_id = settings.PAYPAL_CLIENT_ID
        client_secret = settings.PAYPAL_CLIENT_SECRET
        
        response = check_paypal_order(client_id=client_id, client_secret=client_secret, order_id=txn_id)
        
        if response.status_code == 200:
            order_details = response.json()
            print("Order Details:")
            print(order_details)
            # Check if the status is "CREATED"
            if order_details.get('status') == 'APPROVED':
                print("Payment status is COMPLETED.")
                logger.info( "Payment status is COMPLETED", extra={ 'user': 'Anonymous' })
                payment.status = "successful"
                payment.has_paid = True
                payment.save() 
            
        elif response.status_code == 404:
            print(f"Order with ID {txn_id} not found.")
            logger.error(f"Order with ID {txn_id} not found.", extra={ 'user': 'Anonymous' })
            payment.status = "failed"
            payment.has_paid = False
            payment.save() 
        else:
            print(f"Failed to retrieve order details. Status code: {response.status_code}")
            logger.error(f"Failed to retrieve order details. Status code: {response.status_code}", extra={ 'user': 'Anonymous' })
            return None
        
        
        




