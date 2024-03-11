import logging
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import status
from .serializers import LogoutSerializer


logger = logging.getLogger("myLogger")


class Logout(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        request.user.auth_token.delete()
        logger.info(
            "Logout successful",
            extra={
                'user': request.user.id
            }
        )
        return Response({'message': "Logout Successful"}, status=status.HTTP_200_OK)


