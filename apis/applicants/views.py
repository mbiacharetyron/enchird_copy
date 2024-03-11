import random
import string
import logging
import datetime
import requests
import django_filters
from io import BytesIO
from apis.utils import *
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from core.views import PaginationClass
from rest_framework import status, viewsets
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from apis.users.models import User, AnonymousUser
from .models import Applicant, AchievementDocument
from core.email import send_student_application_email
from apis.students.serializers import StudentSerializer
from rest_framework.decorators import permission_classes
from django.contrib.auth.models import Group, Permission
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import ApplicantSerializer, AchievementDocumentSerializer

logger = logging.getLogger("myLogger")



# Create your views here.
class ApplicantViewSet(viewsets.ModelViewSet):
    
    queryset = Applicant.objects.all().exclude(Q(status='accepted') | Q(is_deleted=True)).order_by('-created_at')
    serializer_class = ApplicantSerializer
    pagination_class = PaginationClass


    def list(self, request, *args, **kwargs):

        user = self.request.user

        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
        
        if not user.is_admin:
            logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
            return Response( {'error': "You do not have the necessary right."}, status=status.HTTP_401_UNAUTHORIZED )

        department_name = request.query_params.get('department_name', None)
        faculty_name = request.query_params.get('faculty_name', None)
        order = self.request.query_params.get('order', None)
        keyword = request.query_params.get('keyword', None)
        status = request.query_params.get('status', None)
        gender = request.query_params.get('gender', None) 
        
        
        queryset = Applicant.objects.exclude(Q(status='accepted') | Q(is_deleted=True))
        
        if order:
            queryset = queryset.order_by('-created_at') if order == 'desc' else queryset.order_by('created_at')

        if faculty_name: 
            queryset = queryset.filter(faculty__name__icontains=faculty_name)

        if department_name:
            queryset = queryset.filter(department__name__icontains=department_name)

        if gender:
            queryset = queryset.filter(gender=gender)
            
        if status:
            queryset = queryset.filter(status=status) 
            
        if keyword is not None:
            # Split the keyword into individual words
            words = keyword.split()

            # Create a Q object for each word in both fields
            name_queries = Q()
            abbrev_queries = Q()

            for word in words: 
                name_queries |= Q(first_name__icontains=word)
                abbrev_queries |= Q(last_name__icontains=word)

            # Combining the queries with OR conditions
            combined_query = (name_queries | abbrev_queries)

            # Apply the combined query along with other filters
            queryset = Applicant.objects.filter(
                combined_query,
                # status__ne='rejected',
                is_deleted=False,
            ).order_by('-created_at')
            
        if not order:
            queryset = queryset.order_by('-created_at')

        queryset = queryset 
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            
            # Include achievement documents in each applicant's serialized data
            for data in serializer.data:
                applicant_id = data['applicant_id']
                achievement_documents = AchievementDocument.objects.filter(applicant__applicant_id=applicant_id)
                data['past_achievement_documents'] = AchievementDocumentSerializer(achievement_documents, many=True).data
            
            logger.info("List of applicants returned successfully.", extra={'user': user.id})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)

        # Include achievement documents in each applicant's serialized data
        for data in serializer.data:
            applicant_id = data['applicant_id']
            achievement_documents = AchievementDocument.objects.filter(applicant__applicant_id=applicant_id)
            data['past_achievement_documents'] = AchievementDocumentSerializer(achievement_documents, many=True).data

        logger.info("List of applicants returned successfully.", extra={'user': user.id})

        return Response(serializer.data)


    def retrieve(self, request, *args, **kwargs):

        user = self.request.user
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        if not user.is_admin:
            logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
            return Response( {'error': "You do not have the necessary right."}, status=status.HTTP_401_UNAUTHORIZED )

        try: 
            instance = Applicant.objects.get(id=kwargs['pk'])
        except Applicant.DoesNotExist:
            logger.error( "Applicant not Found.", extra={ 'user': user.id } )
            return Response( {"error": "Applicant Not Found."}, status=status.HTTP_404_NOT_FOUND )

        # Retrieve achievement documents related to the applicant
        achievement_documents = AchievementDocument.objects.filter(applicant=instance)
        serializer = self.get_serializer(instance)
        serialized_data = serializer.data

        # Include serialized achievement documents in the response
        serialized_data['past_achievement_documents'] = AchievementDocumentSerializer(achievement_documents, many=True).data

        # serializer = self.get_serializer(instance)
        logger.info(
            "Applicant details returned successfully!",
            extra={
                'user': request.user.id
            }
        )
        return Response(serialized_data)

    
    def create(self, request, *args, **kwargs):
        
        user = request.user
        try:
            with transaction.atomic():
                applicant_serializer = self.get_serializer(data=request.data)
                if applicant_serializer.is_valid(raise_exception=True):
                    
                    # Create applicant
                    applicant = applicant_serializer.save(status="pending")

                    scanned_id_document_url = request.data.get("scanned_id_document_url")

                    # Extract documents data from the request
                    documents_data = request.data.get('documents', [])

                    # Verify uniqueness of email address
                    num = User.objects.all().filter(email=applicant_serializer.validated_data['email']).count()
                    if num > 0:
                        logger.warning("An applicant/student/teacher with this email address already exists.", extra={'user': request.user.id})
                        return Response({"error": "An applicant/student/teacher with this email address already exists."},
                                        status=status.HTTP_409_CONFLICT)

                    # Handling documents separately
                    achievement_documents = []
                    for doc_data in documents_data:
                        name = doc_data.get('name')
                        document_path = doc_data.get('document_path')

                        # Create and save AchievementDocument object
                        achievement = AchievementDocument.objects.create(
                            applicant=applicant,
                            document=document_path,
                            name=name
                        )
                        achievement_documents.append(achievement)

                    #Serialize and return response
                    serialized_data = applicant_serializer.data
                    
                    # Include serialized achievement documents in the response
                    serialized_data['documents'] = AchievementDocumentSerializer(achievement_documents, many=True).data

                    headers = self.get_success_headers(applicant_serializer.data)
                    
                    try:
                        send_student_application_email(applicant)
                    except Exception as e:
                        logger.error( e, extra={ 'user': user.id })
                        
                    logger.info( "Applicant created successfully!", extra={ 'user': user.id } )
                    return Response( serialized_data, status.HTTP_201_CREATED, headers=headers)
        
        except Exception as e:
            # Rollback transaction and raise validation error
            transaction.rollback()
            logger.error( str(e), extra={ 'user': None })
            return Response( {"error": str(e)}, status=status.HTTP_412_PRECONDITION_FAILED)


    def update(self, request, *args, **kwargs):
                
        logger.warning( "Method not allowed", extra={ 'user': "Anonymous" })
        return Response( {"error": "Method not allowed"}, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, *args, **kwargs):

        user = self.request.user
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."},
                status=status.HTTP_401_UNAUTHORIZED )

        if not user.is_admin:
            logger.warning( "You do not have the necessary rights!", extra={ 'user': user.id } )
            return Response( {"error": "You do not have the necessary rights"},
                status.HTTP_403_FORBIDDEN )

        try:
            instance = Applicant.objects.get(id=kwargs['pk'])
        except Applicant.DoesNotExist:
            logger.error( "Applicant not Found.", extra={ 'user': user.id })
            return Response( {"error": "Applicant Not Found."},
                status=status.HTTP_404_NOT_FOUND )
        instance.is_deleted = True
        instance.save()

        logger.info( "Applicant marked as deleted successfully", extra={ 'user': user.id } )
        return Response( {"message": "Applicant marked as Deleted"}, status=status.HTTP_200_OK)

