import uuid
import stripe
import logging
from .models import *
from .serializers import *
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from apis.users.models import User
from django.http import HttpResponse
from core.views import PaginationClass
from .paypal import create_paypal_order
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect, render
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from rest_framework.exceptions import ValidationError

logger = logging.getLogger("myLogger")



# Create your views here.
class StripeCheckoutSession(APIView):
    
    queryset = UserPayment.objects.all().filter()
    serializer_class = UserPaymentSerializer
    allowed_methods = ['post']
    
    def post(self, request, *args, **kwargs): 
        user = request.user 
        print(user)
        
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        if not user.is_a_student:
            logger.error( "Only students can make this request.", extra={ 'user': 'Anonymous' } )
            return Response( {'error': "Only students can make this request."}, status=status.HTTP_401_UNAUTHORIZED )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        serializer = UserPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data['amount']
        
        sucs_url = request.data.get('success_url')
        canc_url = request.data.get('cancel_url')
        
        if not sucs_url or not canc_url:
            error_message = "Both success_url and cancel_url are required in the request body."
            logger.error(error_message, extra={'user': user.id})
            raise ValidationError({'error': error_message}, code=status.HTTP_400_BAD_REQUEST)

        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                        'price_data':{
                            'currency': 'xaf',
                            'unit_amount': int(amount),
                            'product_data':{
                                'name': f'{user.first_name} {user.last_name} - Enchird Fee Payment',
                                },
                            },
                        
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url= sucs_url, #'http://127.0.0.1:8000/api/messaging',
                cancel_url= canc_url, #'http://127.0.0.1:8000/api/messaging',
                customer_email=user.email,
                
            )
            # Create a new UserPayment instance
            user_payment = UserPayment(user=user)
            user_payment.amount = amount
            user_payment.payment_method = "stripe"
            user_payment.stripe_checkout_id = checkout_session.id
            
            # Save the instance to the database
            user_payment.save()
            response_data = {
                'checkout_session_id': checkout_session.id,
                'checkout_session_url': checkout_session.url,
            }
            # return redirect(checkout_session.url, code=303)
            return Response(response_data)
            # client_secret = checkout_session.client_secret
            
            # return Response({'client_secret': client_secret})
        except Exception as e:
            logger.error( str(e), extra={ 'user': user.id })
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@csrf_exempt
def stripe_webhook_view(request):
    user = request.user
    print(user)
    
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.WEBHOOK_SECRET
    event = None

    try:
        event = stripe.Webhook.construct_event(
        payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        logger.error( str(e), extra={ 'user': 'Anonymous' } )
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error( str(e), extra={ 'user': 'Anonymous' } )
        return HttpResponse(status=400)
    
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        # Retrieve the session. If you require line items in the response, you may include them by expanding line_items.
        session = event['data']['object'] #['id']
        customer_email = session['customer_details']['email']
        checkout_id = session['id']
        
        try:
            user = User.objects.get(email=customer_email)
            user_payment = UserPayment.objects.get(stripe_checkout_id=checkout_id)
            
            user_payment.has_paid = True
            user_payment.status = "successful"
            user_payment.save()
            
        except User.DoesNotExist:
            logger.error( "User not Found.", extra={ 'Anonymous' } )
            # return Response( {"error": "Applicant Not Found."}, status=status.HTTP_404_NOT_FOUND )
        except UserPayment.DoesNotExist:
            logger.error( "User did not initiate a payment.", extra={ 'user': user.id } )
            

        print(session)
        
    if event['type'] == 'checkout.session.expired':
        session = event['data']['object']  
        customer_email = session['customer_details']['email']
        checkout_id = session['id']
        
        try:
            user = User.objects.get(email=customer_email)
            user_payment = UserPayment.objects.get(stripe_checkout_id=checkout_id)
            
            user_payment.status = "failed"
            user_payment.save()
            
        except User.DoesNotExist:
            logger.error( "User not Found.", extra={ 'Anonymous' })
            # return Response( {"error": "Applicant Not Found."}, status=status.HTTP_404_NOT_FOUND )
        except UserPayment.DoesNotExist:
            logger.error( "User did not initiate a payment.", extra={ 'user': user.id } )
            

    # Passed signature verification
    return HttpResponse(status=200)


@api_view(['GET'])
def successful_payments(request):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
    
    if not user.is_admin:
        logger.error( "Only admins can make this request.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "Only admins can make this request."}, status=status.HTTP_401_UNAUTHORIZED )

    queryset = UserPayment.objects.filter(
        status="successful", 
        has_paid=True).order_by('-created_at')
    
    # Paginate the results
    paginator = PaginationClass()
    paginated_payments = paginator.paginate_queryset(queryset, request)

    # Serialize the paginated students
    payment_serializer = UserPaymentSerializer(paginated_payments, many=True)

    # Create the response
    response_data = {
        'count': paginator.page.paginator.count,
        'next': paginator.get_next_link(),
        'previous': paginator.get_previous_link(),
        'courses': payment_serializer.data,
    }

    return Response(response_data)



class PayPalPaymentView(APIView):
    
    queryset = UserPayment.objects.all().filter()
    serializer_class = UserPaymentSerializer
    allowed_methods = ['post']
    
    def post(self, request, *args, **kwargs):
        serializer = PayPalPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        print(user)
        
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        if not user.is_a_student:
            logger.error( "Only students can make this request.", extra={ 'user': 'Anonymous' } )
            return Response( {'error': "Only students can make this request."}, status=status.HTTP_401_UNAUTHORIZED )

        
        # host = request.get_host()
        amount = serializer.validated_data['amount']
        
        rtn_url = request.data.get('return_url')
        canc_url = request.data.get('cancel_url')
        
        if not rtn_url or not canc_url:
            error_message = "Both return_url and cancel_url are required in the request body."
            logger.error(error_message, extra={'user': user.id})
            raise ValidationError({'error': error_message}, code=status.HTTP_400_BAD_REQUEST)
        
        client_id = settings.PAYPAL_CLIENT_ID
        client_secret = settings.PAYPAL_CLIENT_SECRET
        
        order_resp = create_paypal_order(user=user, client_id=client_id, client_secret=client_secret, amount=amount, return_url=rtn_url, cancel_url=canc_url)
        print(order_resp)
        order_response = order_resp.json()
        print(order_response.get("id"))
        
        if order_resp.status_code == 201:
            user_payment = UserPayment(user=user)
            user_payment.amount = amount
            user_payment.payment_method = "paypal"
            user_payment.paypal_checkout_id = order_response.get("id")
            
            user_payment.save()
            
        # print(token_resp)
        # print(order_resp)

        return Response(order_response, status=status.HTTP_200_OK)





