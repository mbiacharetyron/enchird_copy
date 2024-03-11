import logging
import datetime
from uuid import uuid4
# from drf_yasg import openapi
from django.conf import settings
from rest_framework import status
from rest_framework import generics
from rest_framework.response import Response
from django.contrib.auth import get_user_model
# from drf_yasg.utils import swagger_auto_schema
from rest_framework.authtoken.models import Token
from .serializers import ChangePasswordSerializer
from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes

logger = logging.getLogger("myLogger")



class ChangePasswordView(generics.UpdateAPIView):

    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    http_method_names = ['put']

    # @swagger_auto_schema(responses={200: correct_response, 400: bad_request, 412: error_response})
    def put(self, request):
         
        user = request.user
        try:
            serializer = ChangePasswordSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                if not user.check_password(serializer.validated_data['old_password']):
                    logger.error( "Incorrect Password",
                        extra={ 'user': request.user.id } )
                    return Response( {"message": "Incorrect Password" }, status.HTTP_400_BAD_REQUEST )

                new_password = serializer.validated_data['new_password']

                user.set_password(new_password)
                user.password_requested_at = None
                user.save()

                logger.info(
                    "Password Modified Sucessfully", extra={ 'user': request.user.id } )
                return Response(
                    {"message": "Password Modified Sucessfully"}, status=status.HTTP_200_OK )
                
        except Exception as e:
            logger.error(
                str(e), extra={
                    'user': request.user.id } ) 
            
            return Response(
                {'message': str(e)},
                status=status.HTTP_412_PRECONDITION_FAILED)
