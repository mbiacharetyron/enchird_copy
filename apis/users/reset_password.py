import logging
from uuid import uuid4
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import get_user_model
from apis.users.models import User
from django.conf import settings
from django.template.loader import render_to_string
from apis.users.serializers import ResetPasswordSerializer
from rest_framework import generics
from core.email import send_reset_password_email
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

logger = logging.getLogger("myLogger")



class ResetPasswordView(generics.CreateAPIView):
    """Docstring for class."""

    serializer_class = ResetPasswordSerializer

    def post(self, request):
        try:
            reset_token = uuid4()

            serializer = ResetPasswordSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                email = serializer.validated_data['email']

                try:
                    user = get_user_model().objects.get(
                        email=email,
                        is_active=True,
                        is_deleted=False
                    )
                except User.DoesNotExist:
                    logger.error(
                        "This user does not exist!",
                        extra={
                            'user': None
                        }
                    )
                    return Response(
                        {
                            "message": "User does not exist."
                        },
                        status.HTTP_404_NOT_FOUND
                    )

                # Generate token and send email
                uid = urlsafe_base64_encode(force_bytes(user.id))
                user.password_requested_at = None
                user.reset_token = reset_token
                user.save() 

                try:
                    send_reset_password_email(user, reset_token, uid)
                except Exception as e:
                    print(e)
                    logger.error(
                        e,
                        extra={
                            'user': user.id
                        }
                    )
                
                logger.info(
                    "Reset password link sent to email.",
                    extra={ 
                        'user': user.id
                    }
                )
                return Response(
                    {
                        "message": "Reset password link sent to email."
                    }
                )
        except Exception as e:
            logger.error(
                str(e),
                extra={
                    'user': None
                }
            )
            return Response(
                {'message': str(e)},
                status=status.HTTP_412_PRECONDITION_FAILED)


class VerifyResetTokenView(APIView):

    def post(self, request):

        request.data.get("reset_token")
        try:
            user = User.objects.get(reset_token=reset_token)
        except User.DoesNotExist:
            logger.error(
                "Invalid reset token.",
                extra={
                    'user': 'Anonymous'
                }
            )
            return Response(
                {'error': "Invalid reset token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'message': ""})

        logger.error(
            "Tokem Verified Successfully.",
            extra={
                'user': user.id
            }
        )

        return Response({"message": "Token verified successfully"}, status=status.HTTP_200_OK)


