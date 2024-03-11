import logging
from uuid import uuid4
from django.utils import timezone
from rest_framework.response import Response
from django.contrib.auth.models import Permission
from rest_framework.views import APIView
from django.db import models
from rest_framework import status, serializers
from django.contrib.auth import get_user_model
from apis.users.models import User, Group
from knox.views import AuthToken, LoginView
from apis.users.serializers import UserSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import AuthenticationFailed
from urllib.parse import urlsplit
from apis.utils import *
from rest_framework.authtoken.serializers import AuthTokenSerializer
from apis.users.serializers import LoginSerializer, PermissionSerializer
from core.authtokenserializer import CustomAuthTokenSerializer


logger = logging.getLogger("myLogger")



class LoginView(APIView):
     
    serializer_class = CustomAuthTokenSerializer


    def post(self, request,  *args, **kwargs):
         
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            data = {
                "username": serializer.validated_data['email'],
                "password": serializer.validated_data['password']
            }

            serializer = self.serializer_class(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            
            user = serializer.validated_data['user']

            user.reset_token = None

            if user.reset_token is not None:
                logger.error(
                    "Please validate your account",
                    extra={ 'user': user.id } )
                return Response(
                    { "message": "Please validate your account" }, status.HTTP_400_BAD_REQUEST )
            
            user.last_login = timezone.now()
            user.save()

            _, token = AuthToken.objects.create(user=user)

            # Serializing the user object
            user_serializer = UserSerializer(user)

            logger.info(
                "User Logged in sucessfully.",
                extra={
                    'user': user.id
                }
            )
            return Response({
                'Token': str(token),
                'user': user_serializer.data
            })

        except serializers.ValidationError as e:
            # Handle validation errors from the serializer
            error_message = e.detail.get('non_field_errors', [''])[0]
            logger.error(
                error_message,
                extra={
                    'user': None
                }
            )
            return Response(
                {'error': error_message},
                status=status.HTTP_412_PRECONDITION_FAILED
            )
        
        except Exception as e:
            logger.error( str(e), extra={ 'user': None } ) 
            return Response(
                {'error': str(e)},
                status=status.HTTP_412_PRECONDITION_FAILED)


