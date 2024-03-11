# Import necessary modules
import ssl
import random
import string
import logging
import datetime
from uuid import uuid4
from apis.utils import *
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from core.views import PaginationClass
from apis.students.models import Student
from apis.teachers.models import Teacher
from apis.utils import validate_password
from django.core.mail import EmailMessage
from rest_framework import status, viewsets
from rest_framework.decorators import action
from apis.applicants.models import Applicant
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from apis.users.models import User, AnonymousUser
from core.email_templates import student_accept_html
from apis.courses.models import Course, CourseMaterial
from apis.students.serializers import StudentSerializer
from rest_framework.decorators import permission_classes
from django.contrib.auth.models import Group, Permission
from apis.courses.serializers import CourseMaterialSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.email import send_student_accept_mail, send_student_reject_mail
from apis.users.serializers import UserSerializer, UserPasswordSerializer, UserUpdateSerializer


logger = logging.getLogger("myLogger")

logging.basicConfig(filename='app.log', level=logging.DEBUG) 



class StudentViewSet(viewsets.ModelViewSet):

    # Define the queryset and serializer class
    queryset = Student.objects.all().filter(
                is_deleted=False,
                ).order_by('-created_at')
    pagination_class = PaginationClass
    serializer_class = StudentSerializer

    def get_permissions(self):
        if self.action in ['create']:
            # Allow unauthenticated access for create
            permission_classes = [AllowAny]
        else:
            # Require authentication and permissions for other actions
            permission_classes = [IsAuthenticated]  # You can add more permissions as needed
        return [permission() for permission in permission_classes]


    def list(self, request, *args, **kwargs):

        user = self.request.user

        if not user.is_authenticated:
            logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
            return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        if user.is_admin is False and user.is_superuser is False:
            logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
            return Response( { "error": "You do not have the necessary rights." }, status.HTTP_403_FORBIDDEN )
            
        queryset = self.filter_queryset(self.get_queryset())
            
        # Apply filters based on query parameters
        department = self.request.query_params.get('department', None)
        faculty = self.request.query_params.get('faculty', None)
        gender = self.request.query_params.get('gender', None)
        order = self.request.query_params.get('order', None)
        keyword = request.query_params.get('keyword', None)
        
        
        if gender:
            queryset = queryset.filter(user__gender=gender)

        if faculty:
            queryset = queryset.filter(faculty__name__icontains=faculty)

        if department:
            queryset = queryset.filter(department__name__icontains=department)
        
        if order:
            queryset = queryset.order_by('-created_at') if order == 'desc' else queryset.order_by('created_at')
            
        if keyword is not None:
            # Split the keyword into individual words
            words = keyword.split()

            # Create a Q object for each word in both fields
            name_queries = Q()
            abbrev_queries = Q()

            for word in words: 
                name_queries |= Q(user__first_name__icontains=word)
                abbrev_queries |= Q(user__last_name__icontains=word)

            # Combining the queries with OR conditions
            combined_query = (name_queries | abbrev_queries)

            # Apply the combined query along with other filters
            queryset = Student.objects.filter(
                combined_query,
                is_deleted=False
            ).order_by('-created_at')
            
        if not order:
            queryset = queryset.order_by('-created_at')

        # queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            logger.info(
                "Students list returned successfully.",
                extra={ 'user': user.id } )
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info(
            "Students list returned successfully.",
            extra={ 'user': user.id } )

        return Response(serializer.data)


    def retrieve(self, request, *args, **kwargs):
         
        user = self.request.user
        print(user)
        if not user.is_authenticated:
            logger.error(
                "You must provide valid authentication credentials.",
                extra={
                    'user': request.user.id
                }
            )
            return Response(
                {"error": "You must provide valid authentication credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if user.is_admin is False and user.is_a_student is False:
            logger.error(
                "You do not have the necessary rights.",
                extra={
                    'user': request.user.id
                }
            )
            return Response(
                {
                    "error": "You do not have the necessary rights."
                },
                status.HTTP_403_FORBIDDEN
            )
        
        if user.is_a_student is True and str(user.id) != kwargs['pk']:
            logger.warning(
                "You cannot view another student's information",
                extra={
                    'user': request.user.id
                }
            )
            return Response(
                {"error": "You cannot view another student's information"},
                status.HTTP_403_FORBIDDEN
            )

        instance = Student.objects.get(user=kwargs['pk'])
        serializer = self.get_serializer(instance)
        logger.info(
            "Student details returned successfully!",
            extra={
                'user': request.user.id
            }
        )
        return Response(serializer.data)

    
    def create(self, request, *args, **kwargs):
        
        logger.warning( "Method not allowed", extra={ 'user': "Anonymous" })
        return Response( {"error": "Method not allowed"}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['post'])
    def accept(self, request):
        try:
            with transaction.atomic():
                user = request.user

                reset_token = uuid4()

                # Check if the user making the request is an admin
                if not request.user.is_authenticated or not request.user.is_admin:
                    logger.error("You do not have permission to perform this action.", extra={'user': 'Anonymous'})
                    return Response({'error': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

                # Get applicant information from the request data (assuming 'applicant_id' is provided)
                applicant_id = request.data.get('applicant_id')
                try:
                    applicant = Applicant.objects.get(applicant_id=applicant_id)
                except Applicant.DoesNotExist:
                    logger.error("Applicant Not Found.", extra={'user': user})
                    return Response({'error': 'Applicant not found.'}, status=status.HTTP_404_NOT_FOUND)

                if applicant.status == "accepted":
                    logger.error("Applicant has already been accepted.", extra={'user': user})
                    return Response({'error': 'Applicant has already been accepted.'}, status=status.HTTP_400_BAD_REQUEST)

                if applicant.status == "rejected":
                    logger.error("Unfortunately applicant had earlier been rejected.", extra={'user': user})
                    return Response({'error': 'Unfortunately applicant had earlier been rejected.'}, status=status.HTTP_400_BAD_REQUEST)

                # Create a User instance based on the Applicant data
                user_data = {
                    'first_name': applicant.first_name,
                    'last_name': applicant.last_name,
                    'username': applicant.first_name,
                    'gender': applicant.gender,
                    'email': applicant.email,
                    'phone': applicant.phone,
                    'date_of_birth': applicant.date_of_birth,
                    'picture': applicant.profile_picture,
                    'nationality': applicant.nationality,
                } 

                user_serializer = UserSerializer(data=user_data)
                student_serializer = self.get_serializer(data=user_data)
                
                if user_serializer.is_valid():
                    # Verify uniqueness of email address
                    num = User.objects.all().filter(email=user_serializer.validated_data['email']).count()
                    if num > 0:
                        logger.warning("A student/teacher with this email address already exists.", extra={'user': 'anonymous'})
                        return Response({"error": "A student/teacher with this email address already exists."},
                                        status=status.HTTP_409_CONFLICT)
                    
                    user = user_serializer.save(is_a_student=True, is_active=True)

                    password = User.objects.make_random_password()
                    user.reset_token = reset_token
                    user.password_requested_at = timezone.now()
                    user.set_password(password)
                    user.save()

                    applicant.status = 'accepted'
                    applicant.is_deleted = True
                    applicant.save()

                    # Create a Student instance
                    student_data = {
                        'user_id': user.id,
                        'faculty': applicant.faculty.id,
                        'department': applicant.department.id,
                    }

                    student_serializer = self.get_serializer(data=student_data)
                    
                    if student_serializer.is_valid():

                        student_serializer.save(user_id=user.id)
                       
                        headers = self.get_success_headers(student_serializer.data)

                        # Create or get Student group
                        all_permissions = Permission.objects.all()
                        student_group, created = Group.objects.get_or_create(name='Student')

                        # Add the student to the Student Group
                        user.groups.add(student_group)

                        # Send acceptance email.
                        faculty = applicant.faculty.name
                        department = applicant.department.name
                         
                        try:
                            send_student_accept_mail(user, password, faculty, department)
                        except Exception as e:
                            print(e)
                            logger.error( e,  extra={ 'user': user.id } )
                        
                        logger.info( "Student created successfully!", extra={ 'user': user.id } )
                        return Response(
                            student_serializer.data,
                            status.HTTP_201_CREATED,
                            headers=headers)
                    else:
                        logger.error(
                            str(student_serializer.errors), extra={ 'user': user.id })
                        return Response({'error': student_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    logger.error(
                            str(user_serializer.errors), extra={ 'user': user.id })
                    return Response({'error': user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Rollback transaction and raise validation error
            transaction.rollback()
            logger.error( str(e), extra={ 'user': None } )
            return Response( {"error": str(e)}, status=status.HTTP_412_PRECONDITION_FAILED)


    @action(detail=True, methods=['post'])
    def reject(self, request):
        try:
            with transaction.atomic():
                user = request.user

                # Get applicant information from the request data (assuming 'applicant_id' is provided)
                applicant_id = request.data.get('applicant_id')
                try:
                    applicant = Applicant.objects.get(applicant_id=applicant_id)
                except Applicant.DoesNotExist:
                    logger.error("Applicant Not Found.", extra={'user': user})
                    return Response({'error': 'Applicant not found.'}, status=status.HTTP_404_NOT_FOUND)

                if applicant.status == "accepted":
                    logger.error("Applicant has already been accepted.", extra={'user': user})
                    return Response({'error': 'Applicant has already been accepted.'}, status=status.HTTP_400_BAD_REQUEST)

                if applicant.status == "rejected":
                    logger.error("Unfortunately applicant had earlier been rejected.", extra={'user': user})
                    return Response({'error': 'Unfortunately applicant had earlier been rejected.'}, status=status.HTTP_400_BAD_REQUEST)
                # applicant = self.get_object()

                # Check if the user making the request is an admin
                if not request.user.is_authenticated or not request.user.is_admin:
                    logger.error("You do not have permission to perform this action.", extra={'user': 'Anonymous'})
                    return Response({'error': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

                # Mark the applicant as rejected
                applicant.status = 'rejected'
                applicant.save()

                # Send rejection email.
                faculty = applicant.faculty.name
                department = applicant.department.name
                try:
                    send_student_reject_mail(applicant, faculty, department)
                except Exception as e:
                    print(e)
                    logger.error( e,  extra={ 'user': user.id } )
                
                logger.error("Applicant rejected successfully.", extra={'user': request.user.id})
                return Response({'message': 'Applicant rejected successfully.'}, status=status.HTTP_200_OK)

        except Exception as e:
            # Handle exceptions and return an appropriate response
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def update(self, request, *args, **kwargs):

        user = self.request.user

        if request.user.is_a_student is False:
            logger.warning( "You do not have the necessary rights!",
                extra={ 'user': request.user.id } )
            return Response(
                {"error": "You do not have the necessary rights"},
                status.HTTP_403_FORBIDDEN )
        
        if request.user.id != int(kwargs['pk']):
            logger.error( "You cannot edit another student's information", extra={ 'user': request.user.id } )
            return Response( {"error": "You cannot edit another student's information"}, status.HTTP_400_BAD_REQUEST )

        partial = kwargs.pop('partial', True)
        instance = User.objects.get(id=kwargs['pk'])
        print(instance)
        try:
            student = Student.objects.get(user=kwargs['pk'], is_deleted=False)
        except Student.DoesNotExist:
            logger.warning( "Student not found", extra={ 'user': user.id } )
            return Response( {"error": "Student not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_serializer = UserUpdateSerializer(
            instance, data=request.data,
            partial=partial)
        student_serializer = self.get_serializer(student)
        if user_serializer.is_valid() is True:
            self.perform_update(user_serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            logger.info(
                "Student modified successfully!",
                extra={
                    'user': request.user.id
                }
            )
            return Response(student_serializer.data)
        else:
            logger.error(
                str(user_serializer.errors),
                extra={
                    'user': request.user.id
                }
            )
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
       
        return serializer.save()


    def destroy(self, request, *args, **kwargs):
        
        user = self.request.user
        if not user.is_a_student:
            logger.warning(
                "You do not have the necessary rights!",
                extra={
                    'user': user.id
                }
            )
            return Response(
                {"error": "You do not have the necessary rights"},
                status.HTTP_403_FORBIDDEN
            )
        if user.is_a_student is True and user.id != int(kwargs['pk']):
            logger.warning(
                "You cannot delete another student's account",
                extra={
                    'user': request.user.id
                }
            )
            return Response(
                {"error": "You cannot delete another student's account"},
                status.HTTP_403_FORBIDDEN
            )

        instance = User.objects.get(id=kwargs['pk'])
        print(instance)
        instance.is_active = False
        instance.is_deleted = True
        instance.save()

        student = Student.objects.get(user=instance.id, is_deleted=False)
        print(student)
        student.is_active = False
        student.is_deleted = True
        student.save()

        logger.info(
            "Student marked as deleted successfully",
            extra={
                'user': user.id
            }
        )
        return Response(
            {"message": "Student marked as Deleted"},
            status=status.HTTP_200_OK)


    @action(detail=False, methods=['get'])
    def students_for_course(self, request):
        user = self.request.user

        # Check if the user is a teacher
        if not user.is_authenticated or not user.is_a_teacher:
            logger.error(
                "You do not have the necessary rights. (Not a teacher)",
                extra={'user': request.user.id} )
            return Response(
                {"error": "You do not have the necessary rights (Not a teacher)"},
                status.HTTP_403_FORBIDDEN )

        # Get the course_id from the query parameters
        course_id = request.query_params.get('course_id', None)
        
        if not course_id:
            return Response(
                {"error": "Please provide a valid course_id parameter."},
                status.HTTP_400_BAD_REQUEST )

        try:
            course = Course.objects.get(id=course_id, is_deleted=False)
        except Course.DoesNotExist:
            logger.warning( "Course Not Found", extra={ 'user': request.user.id } )
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Check if the teacher is assigned to the specified course
        try:
            teacher = Teacher.objects.get(user=user, courses__id=course_id)
        except Teacher.DoesNotExist:
            logger.error( "You are not assigned to the specified course.", extra={'user': request.user.id} )
            return Response(
                {"error": "You are not assigned to the specified course."}, status.HTTP_403_FORBIDDEN )

        # Retrieve the students registered for the specified course
        students = Student.objects.filter(registered_courses__id=course_id)

        # Serialize the data and return the response
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)



@api_view(['POST'])
def register_course(request, course_id):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

    if user.is_a_student is False:
        logger.error( "Only students can register courses.", extra={ 'user': user.id } )
        return Response( { "error": "Only students can register courses." }, status.HTTP_403_FORBIDDEN )
    
    try:
        student = Student.objects.get(user=request.user)
        course = Course.objects.get(id=course_id)
    except Student.DoesNotExist:
        logger.info( "Student not found.", extra={ 'user': user.id } )
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        logger.error(
            "Course not found or not open for registration.",
            extra={
                'user': user.id
            }
        )
        return Response({'error': 'Course not found or not open for registration'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the student is registered for the course
    if course in student.registered_courses.all():
        logger.error(
            "Student is already registed for this course.",
            extra={
                'user': user.id
            }
        )
        return Response({'error': 'Student is already registered for this course'}, status=status.HTTP_400_BAD_REQUEST)


    student.registered_courses.add(course)
    student.save()

    serializer = StudentSerializer(student)
    logger.info(
        "Student successfully registered course.",
        extra={
            'user': user.id
        }
    )
    return Response({'message': 'Student successfully registered this course'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def drop_course(request, course_id):
    user = request.user

    if not user.is_authenticated:
        logger.error(
            "You do not have the necessary rights.",
            extra={
                'user': 'Anonymous'
            }
        )
        return Response(
            {'error': "You must provide valid authentication credentials."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if user.is_a_student is False:
        logger.error(
            "Only students can register courses.",
            extra={
                'user': 'Anonymous'
            }
        )
        return Response(
            {
                "error": "Only students can register courses."
            },
            status.HTTP_403_FORBIDDEN
        )
    
    try:
        student = Student.objects.get(user=request.user)
        course = Course.objects.get(id=course_id, course_status='open')
    except Student.DoesNotExist:
        logger.error(
            "Student not found.",
            extra={
                'user': user.id
            }
        )
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    except Course.DoesNotExist:
        logger.error(
            "Course not found or course closed for dropping.",
            extra={
                'user': 'Anonymous'
            }
        )
        return Response({'error': 'Course not found or closed for dropping'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the student is registered for the course
    if course not in student.registered_courses.all():
        logger.error(
            "Student not registed for this course.",
            extra={
                'user': user.id
            }
        )
        return Response({'error': 'Student is not registered for this course'}, status=status.HTTP_400_BAD_REQUEST)

    # If the course is registered, proceed with dropping
    student.registered_courses.remove(course)
    student.save()

    serializer = StudentSerializer(student)
    logger.info(
            "Student successfully dropped course.",
            extra={
                'user': user.id
            }
        )
    return Response({'message': 'Student successfully dropped this course'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_registered_courses(request):
    user = request.user

    if not user.is_authenticated:
        logger.error(
            "You do not have the necessary rights.",
            extra={
                'user': 'Anonymous'
            }
        )
        return Response(
            {'error': "You must provide valid authentication credentials."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if user.is_a_student is False:
        logger.error(
            "Only students view registered courses.",
            extra={
                'user': 'Anonymous'
            }
        )
        return Response(
            {
                "error": "Only students can register courses."
            },
            status.HTTP_403_FORBIDDEN
        )
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        logger.error(
            "Student Not Found.",
            extra={
                'user': user.id
            }
        )
        return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = StudentSerializer(student)
    logger.info(
            "List of Registered courses returned successfully.",
            extra={
                'user': user.id
            }
        )
    return Response(serializer.data['registered_courses'])


@api_view(['GET'])
def view_course_materials(request, course_id):
    user = request.user

    if not user.is_authenticated:
        logger.error(
            "You must provide valid authentication credentials.",
            extra={
                'user': request.user.id
            }
        )
        return Response(
            {"error": "You must provide valid authentication credentials."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        logger.error( "Course Not Found.", extra={ 'user': request.user.id } )
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the authenticated user is a student and is registered for the course
    try:
        student = Student.objects.get(user=request.user, is_deleted=False)
        if course not in student.registered_courses.all():
            logger.error(
                "You are not registered for this course.",
                extra={
                    'user': request.user.id
                }
            )
            logger.error( "You are not registered for this course.", extra={ 'user': request.user.id })
            return Response({'error': 'You are not registered for this course'}, status=status.HTTP_403_FORBIDDEN)
    except Student.DoesNotExist:
        logger.error( "You are not registered for this course.", extra={ 'user': request.user.id })
        return Response({'error': 'You are not registered as a student'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        course_materials = CourseMaterial.objects.filter(course=course)
        serializer = CourseMaterialSerializer(course_materials, many=True)
        logger.info( "Course materials returned successfully.", extra={ 'user': request.user.id } )
        return Response(serializer.data)

    logger.error(
        "Invalid request method.",
        extra={
            'user': request.user.id
        }
    )
    return Response({'error': 'Invalid request method'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def tutor_student_search(request, course_id):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
    
    if not user.is_a_teacher:
        logger.error( "Only tutors can make this request.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "Only tutors can make this request."}, status=status.HTTP_401_UNAUTHORIZED )

    # Get the course associated with the given course ID
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        logger.error( "Course not found.", extra={ 'user': 'Anonymous' } )
        return Response({'error': 'Course not found'}, status=404)

    try:
        tutor = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        logger.warning( "Tutor Not Found", extra={ 'user': request.user.id } )
        return Response({'error': 'Tutor Not Found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if the tutor is assigned to the course
    if not tutor.courses.filter(id=course_id).exists():
        logger.error( "Tutor is not assigned to this course.", extra={ 'user': 'Anonymous' } )
        return Response({'error': 'Tutor is not assigned to this course'}, status=403)

    # Get the students registered for the course
    registered_students = course.students.all()
    print(registered_students)
    
    # Filter students based on any additional search parameters if needed
    keyword = request.query_params.get('keyword', None)

    if keyword is not None:
        # Split the keyword into individual words
        words = keyword.split()

        # Create a Q object for each word in both fields
        name_queries = Q()
        abbrev_queries = Q()

        for word in words: 
            name_queries |= Q(user__first_name__icontains=word)
            abbrev_queries |= Q(user__last_name__icontains=word)

        # Combining the queries with OR conditions
        combined_query = (name_queries | abbrev_queries)

        # Apply the combined query along with other filters
        registered_students = registered_students.filter(
            combined_query
        ).order_by('-created_at')

    # Paginate the results
    paginator = PaginationClass()
    paginated_students = paginator.paginate_queryset(registered_students, request)

    # Serialize the paginated students
    student_serializer = StudentSerializer(paginated_students, many=True)

    # Create the response
    response_data = {
        'count': paginator.page.paginator.count,
        'next': paginator.get_next_link(),
        'previous': paginator.get_previous_link(),
        'students': student_serializer.data,
    }

    return Response(response_data)



