import random
import string
import logging
import datetime
from .models import *
from apis.utils import *
from .serializers import *
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from apis.users.serializers import *
from core.views import PaginationClass
from apis.teachers.models import Teacher
from apis.students.models import Student
from rest_framework import status, viewsets
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from apis.users.models import User, AnonymousUser
from rest_framework.decorators import permission_classes
from django.contrib.auth.models import Group, Permission
from rest_framework.permissions import IsAuthenticated, AllowAny


logger = logging.getLogger("myLogger")

logging.basicConfig(filename='app.log', level=logging.DEBUG) 



class CourseViewSet(viewsets.ModelViewSet):

    queryset = Course.objects.all().filter(
                is_deleted=False,
                ).order_by('-created_at')
    pagination_class = PaginationClass
    serializer_class = CourseSerializer


    def list(self, request, *args, **kwargs):

        user = self.request.user

        if not user.is_authenticated:
            logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' })
            return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
            
        faculty_name = request.query_params.get('faculty_name', None)
        department_name = request.query_params.get('department_name', None)
        course_level = request.query_params.get('course_level', None)
        keyword = request.query_params.get('keyword', None)

        queryset = Course.objects.filter(is_deleted=False)

        if faculty_name:
            queryset = queryset.filter(faculty__name__icontains=faculty_name)

        if department_name: 
            
            queryset = queryset.filter(department__name__icontains=department_name)

        if course_level:
            queryset = queryset.filter(course_level=course_level)
            
        if keyword is not None:
            queryset = Course.objects.all().filter( 
                course_title__icontains=keyword,
                is_deleted=False
            ).order_by('-created_at')

        queryset = queryset.order_by('-created_at')


        # queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            logger.info("List of courses returned successfully.", extra={'user': user.id})
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info("List of courses returned successfully.", extra={'user': user.id})
        return Response(serializer.data)


    def retrieve(self, request, *args, **kwargs):

        user = self.request.user
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        try: 
            instance = Course.objects.get(id=kwargs['pk'])
        except Course.DoesNotExist:
            logger.error( "Course not Found.", extra={ 'user': user.id } )
            return Response( {"error": "Course Not Found."}, status=status.HTTP_404_NOT_FOUND )

        serializer = self.get_serializer(instance)
        logger.info( "Course details returned successfully!", extra={ 'user': request.user.id } )
        return Response(serializer.data)

    
    def create(self, request, *args, **kwargs):
        
        user = request.user
        if not user.is_authenticated:
            logger.error(
                "You must provide valid authentication credentials.",
                extra={
                    'user': 'Anonymous'
                }
            )
            return Response( {"error": "You must provide valid authentication credentials."},
                status=status.HTTP_401_UNAUTHORIZED )

        if user.is_admin is False:
            logger.error(
                "You do not have the necessary rights/Not an Admin.",
                extra={
                    'user': user.id
                }
            )
            return Response(
                {
                    "error": "You do not have the necessary rights/Not an Admin."
                },
                status.HTTP_403_FORBIDDEN
            )
        
        try:
            with transaction.atomic():
                course_serializer = self.get_serializer(data=request.data)
                print(course_serializer) 
                if course_serializer.is_valid(raise_exception=True):
                    # Verify uniqueness of course title
                    title_num = Course.objects.all().filter(
                            course_title=course_serializer.validated_data['course_title']
                        ).count()
                    if title_num > 0:
                        logger.warning( "A course with this name already exists.", 
                            extra={ 'user': 'anonymous' } )
                        return Response({"error": "A course with this name already exists."},
                                        status=status.HTTP_409_CONFLICT)

                    # Verify uniqueness of course code
                    code_num = Course.objects.all().filter(
                            course_code=course_serializer.validated_data['course_code']
                        ).count()
                    if code_num > 0:
                        logger.warning(
                            "A course with this code already exists.",
                            extra={
                                'user': 'anonymous'
                            }
                        )
                        return Response({"error": "A course with this code already exists."},
                                        status=status.HTTP_409_CONFLICT)
                    
                    # Create course
                    logging.debug('Your message here')
                    course = course_serializer.save(created_by=user)
                    
                    headers = self.get_success_headers(course_serializer.data)
                    
                    logger.info( "Course created successfully!", extra={ 'user': user.id } )
                    return Response(
                        course_serializer.data,
                        status.HTTP_201_CREATED,
                        headers=headers)
        
        except Exception as e:
            # Rollback transaction and raise validation error
            transaction.rollback()
            logger.error( str(e), extra={ 'user': request.user.id } )
            return Response(
                {"error": str(e)},
                status=status.HTTP_412_PRECONDITION_FAILED)


    def update(self, request, *args, **kwargs):
        
        user = self.request.user
        if not user.is_authenticated:
            logger.error(
                "You must provide valid authentication credentials.",
                extra={
                    'user': 'Anonymous'
                }
            )
            return Response(
                {"error": "You must provide valid authentication credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )


        if request.user.is_admin is False:
            logger.warning(
                "You do not have the necessary rights!",
                extra={
                    'user': request.user.id
                }
            )
            return Response(
                {"error": "You do not have the necessary rights"},
                status.HTTP_403_FORBIDDEN
            )

        partial = kwargs.pop('partial', True)
        try:
            instance = Course.objects.get(id=kwargs['pk'])
        except Course.DoesNotExist:
            logger.error(
                "Course not Found.",
                extra={
                    'user': user.id
                }
            )
            return Response(
                {"error": "Course Not Found."},
                status=status.HTTP_404_NOT_FOUND
            )
        print(instance)
        
        course_serializer = self.get_serializer(instance, 
                data=request.data,
                partial=partial)
        if course_serializer.is_valid() is True:

            number = Course.objects.all().filter(
                ~Q(id=kwargs['pk']),
                course_title=course_serializer.validated_data['course_title'],
                is_deleted=False
            ).count()
            if number >= 1:
                logger.error(
                    "A Course already exists with this name.",
                    extra={
                        'user': request.user.id
                    }
                )
                return Response(
                    {'message': "A Course already exists with this name."},
                    status=status.HTTP_409_CONFLICT)

            num = Course.objects.all().filter(
                ~Q(id=kwargs['pk']),
                course_code=course_serializer.validated_data['course_code'],
                is_deleted=False
            ).count()
            if num >= 1:
                logger.error(
                    "A Course already exists with this code.",
                    extra={
                        'user': request.user.id
                    }
                )
                return Response(
                    {'message': "A Course already exists with this code."},
                    status=status.HTTP_409_CONFLICT)

            course_serializer.save(modified_by=user)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            logger.info(
                "Course Info modified successfully!",
                extra={
                    'user': request.user.id
                }
            )
            return Response(course_serializer.data)
        else:
            logger.error(
                str(course_serializer.errors),
                extra={
                    'user': request.user.id
                }
            )
            return Response(course_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, *args, **kwargs):

        user = self.request.user
        if not user.is_authenticated:
            logger.error(
                "You must provide valid authentication credentials.",
                extra={
                    'user': 'Anonymous'
                }
            )
            return Response(
                {"error": "You must provide valid authentication credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_admin:
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

        try:
            instance = Course.objects.get(id=kwargs['pk'])
        except Course.DoesNotExist:
            logger.error(
                "Course not Found.",
                extra={
                    'user': user.id
                }
            )
            return Response(
                {"error": "Course Not Found."},
                status=status.HTTP_404_NOT_FOUND
            )
        instance.is_deleted = True
        instance.save()

        logger.info(
            "Course marked as deleted successfully",
            extra={
                'user': user.id
            }
        )
        return Response(
            {"message": "Course marked as Deleted"},
            status=status.HTTP_200_OK)


class LibraryBookViewSet(viewsets.ModelViewSet):
    
    queryset = LibraryBook.objects.all().filter(
                is_deleted=False,
                ).order_by('-created_at')
    pagination_class = PaginationClass
    serializer_class = LibraryBookSerializer


    def list(self, request, *args, **kwargs):

        user = self.request.user

        if not user.is_authenticated:
            logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' })
            return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
            
        keyword = request.query_params.get('keyword', None)

        queryset = LibraryBook.objects.filter(is_deleted=False)

        if keyword is not None:
            queryset = LibraryBook.objects.all().filter( 
                book_title__icontains=keyword,
                is_deleted=False
            ).order_by('-created_at')

        queryset = queryset.order_by('-created_at')


        # queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            logger.info("List of books returned successfully.", extra={'user': user.id})
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info("List of books returned successfully.", extra={'user': user.id})
        return Response(serializer.data)


    def retrieve(self, request, *args, **kwargs):

        user = self.request.user
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        try: 
            instance = LibraryBook.objects.get(id=kwargs['pk'])
        except LibraryBook.DoesNotExist:
            logger.error( "Book not Found.", extra={ 'user': user.id } )
            return Response( {"error": "Book Not Found."}, status=status.HTTP_404_NOT_FOUND )


        serializer = self.get_serializer(instance)
        logger.info(
            "Book details returned successfully!",
            extra={ 'user': request.user.id } )
        return Response(serializer.data)

    
    def create(self, request, *args, **kwargs):
        
        user = request.user
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={'user': 'Anonymous' })
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        if user.is_admin is False and user.is_a_teacher is False:
            logger.error( "You do not have the necessary rights/Not an Admin.", extra={ 'user': user.id } )
            return Response( { "error": "You do not have the necessary rights/Not an Admin." }, status.HTTP_403_FORBIDDEN )
        
        try:
            with transaction.atomic():
                book_serializer = self.get_serializer(data=request.data)
                print(book_serializer) 
                if book_serializer.is_valid(raise_exception=True):
                    # Verify uniqueness of book title
                    title_num = LibraryBook.objects.all().filter(
                            book_title=book_serializer.validated_data['book_title']
                        ).count()
                    if title_num > 0:
                        logger.warning( "A book with this name already exists.", 
                            extra={ 'user': 'anonymous' } )
                        return Response({"error": "A book with this name already exists."},
                                        status=status.HTTP_409_CONFLICT)

                    # Create course
                    logging.debug('Your message here')
                    book = book_serializer.save(created_by=user)
                    
                    headers = self.get_success_headers(book_serializer.data)
                    
                    logger.info( "Book created successfully!", extra={ 'user': user.id } )
                    return Response(
                        book_serializer.data,
                        status.HTTP_201_CREATED,
                        headers=headers)
        
        except Exception as e:
            # Rollback transaction and raise validation error
            transaction.rollback()
            logger.error( str(e), extra={ 'user': request.user.id } )
            return Response(
                {"error": str(e)},
                status=status.HTTP_412_PRECONDITION_FAILED)


    def update(self, request, *args, **kwargs):
        
        user = self.request.user
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )


        if request.user.is_admin is False and not user.is_a_teacher:
            logger.warning( "You do not have the necessary rights!", extra={ 'user': request.user.id } )
            return Response( {"error": "You do not have the necessary rights"}, status.HTTP_403_FORBIDDEN )
        
        try:
            instance = LibraryBook.objects.get(id=kwargs['pk'])
        except LibraryBook.DoesNotExist:
            logger.error( "Library Book not Found.",  extra={ 'user': user.id } )
            return Response( {"error": "Library Book Not Found."}, status=status.HTTP_404_NOT_FOUND )
        print(instance)

        if request.user.id != instance.created_by.id: #int(kwargs['pk']):
            logger.error( "You cannot edit a document uploaded by another tutor/admin", extra={ 'user': request.user.id } )
            return Response( {"error": "You cannot edit a document uploaded by another tutor/admin"}, status.HTTP_400_BAD_REQUEST )

        partial = kwargs.pop('partial', True)
        
        book_serializer = self.get_serializer(instance, 
                data=request.data,
                partial=partial)
        if book_serializer.is_valid() is True:

            number = LibraryBook.objects.all().filter(
                ~Q(id=kwargs['pk']),
                book_title=book_serializer.validated_data['book_title'],
                is_deleted=False
            ).count()
            if number >= 1:
                logger.error( "A book already exists with this name.", extra={ 'user': request.user.id } )
                return Response( {'message': "A book already exists with this name."}, status=status.HTTP_409_CONFLICT)

            book_serializer.save(modified_by=user)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            logger.info( "Book Info modified successfully!", extra={ 'user': request.user.id } )
            return Response(book_serializer.data)
        else:
            logger.error( str(book_serializer.errors), extra={ 'user': request.user.id } )
            return Response(book_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def destroy(self, request, *args, **kwargs):

        user = self.request.user
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_admin and not user.is_a_teacher:
            logger.warning( "You do not have the necessary rights!", extra={ 'user': user.id } )
            return Response( {"error": "You do not have the necessary rights"}, status.HTTP_403_FORBIDDEN )

        try:
            instance = LibraryBook.objects.get(id=kwargs['pk'])
        except LibraryBook.DoesNotExist:
            logger.error( "Library Book not Found.", extra={ 'user': user.id } )
            return Response( {"error": "Library Book Not Found."}, status=status.HTTP_404_NOT_FOUND )
        
        if request.user.id != instance.created_by.id: #int(kwargs['pk']):
            logger.error( "You cannot delete a document uploaded by another tutor/admin", extra={ 'user': request.user.id } )
            return Response( {"error": "You cannot delete a document uploaded by another tutor/admin"}, status.HTTP_400_BAD_REQUEST )

        instance.is_deleted = True
        instance.save()

        logger.info( "Library Book marked as deleted successfully", extra={ 'user': user.id } )
        return Response(
            {"message": "Course marked as Deleted"},
            status=status.HTTP_200_OK)




@api_view(['POST'])
def assign_teacher(request, course_id, teacher_id):
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

    if request.user.is_admin is False:
        logger.warning(
            "You do not have the necessary rights! (Not admin)",
            extra={
                'user': request.user.id } )
        return Response(
            {"error": "You do not have the necessary rights (Not admin)"},
            status.HTTP_403_FORBIDDEN
        )

    try:
        course = Course.objects.get(id=course_id, is_deleted=False)
        teacher = Teacher.objects.get(user__id=teacher_id, user__is_deleted=False, user__is_a_teacher=True, user__is_active=True)
    except Course.DoesNotExist:
        logger.warning( "Course Not Found", extra={ 'user': request.user.id } )
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        logger.warning( "Teacher not found or is not an active teacher", extra={ 'user': request.user.id } )
        return Response({'error': 'Teacher not found or is not an active teacher'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the teacher is already assigned to the course
    if teacher.courses.filter(id=course_id).exists():
        logger.error( "Teacher is already assigned to the course.", extra={ 'user': request.user.id } )
        return Response({'error': 'Teacher is already assigned to the course'}, status=status.HTTP_400_BAD_REQUEST)

    teacher.courses.add(course)
    teacher.save()

    serializer = CourseSerializer(course)
    return Response(serializer.data)


@api_view(['POST'])
def unassign_teacher(request, course_id, teacher_id):
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

    if request.user.is_admin is False:
        logger.warning(
            "You do not have the necessary rights! (Not admin)",
            extra={
                'user': request.user.id
            }
        )
        return Response(
            {"error": "You do not have the necessary rights (Not admin)"},
            status.HTTP_403_FORBIDDEN
        )

    try:
        course = Course.objects.get(id=course_id, is_deleted=False)
        teacher = Teacher.objects.get(user__id=teacher_id, user__is_deleted=False, user__is_a_teacher=True, user__is_active=True)
        
        # teacher = User.objects.get(id=teacher_id, is_deleted=False, is_a_teacher=True, is_active=True)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        return Response({'error': 'Teacher not found or is not an active teacher'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the teacher is assigned to the course before attempting to remove
    if not teacher.courses.filter(id=course_id).exists():
        logger.error( "Tutor is not assigned to the course.", extra={ 'user': request.user.id } )
        return Response({'error': 'Tutor is not assigned to the course'}, status=status.HTTP_400_BAD_REQUEST)

    teacher.courses.remove(course)
    teacher.save()

    serializer = CourseSerializer(course)
    return Response(serializer.data)


@api_view(['POST'])
def add_course_material(request, course_id):
    user = request.user

    if not user.is_authenticated:
        logger.error(
            "You must provide valid authentication credentials.", extra={ 'user': request.user.id } )
        return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )


    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        logger.warning( "Course Not Found", extra={ 'user': request.user.id } )
        return Response({'error': 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)
    
    if user.is_a_teacher is False:
        logger.warning( "You do not have the necessary rights! (Not a lecturer)", extra={ 'user': request.user.id } )
        return Response( {"error": "You do not have the necessary rights (Not a lecturer)"}, status.HTTP_403_FORBIDDEN )

    if user not in course.instructors.all():
        logger.warning( "You are not a lecturer of this course", extra={ 'user': request.user.id } )
        return Response( {"error": "You are not a lecturer of this course."}, status.HTTP_403_FORBIDDEN )
    
    if request.method == 'POST':
        material_file = request.FILES.get('material')
        description = request.data.get('description')  # If you have a description field

        if material_file:
            # Create a new CourseMaterial instance and associate it with the course
            course_material = CourseMaterial.objects.create(
                material_file=material_file,
                description=description,
                uploaded_by=request.user,
                course=course
            )

            serializer = CourseMaterialSerializer(course_material)
            return Response(serializer.data)
        else:
            logger.error(
                "No file or invalid file sent in request",
                extra={
                    'user': request.user.id
                }
            )
            return Response({'error': 'No file or invalid sent in request'}, status=status.HTTP_400_BAD_REQUEST)

    logger.warning(
        "Invalid request method.",
        extra={
            'user': request.user.id
        }
    )
    return Response({'error': 'Invalid request method'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def remove_course_material(request, course_material_id):
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
        course_material = CourseMaterial.objects.get(pk=course_material_id)
    except CourseMaterial.DoesNotExist:
        logger.warning(
            "Course material not found.",
            extra={
                'user': request.user.id
            }
        )
        return Response({'error': 'Course material not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the authenticated user is the one who uploaded the material or is an admin/teacher with appropriate permissions
    if request.user != course_material.uploaded_by and not request.user.is_staff:
        logger.warning(
            "You do not have permission to remove this course material.",
            extra={
                'user': request.user.id
            }
        )
        return Response({'error': 'You do not have permission to remove this course material'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        course_material.delete()
        logger.info(
            "Course material deleted successfully.",
            extra={
                'user': request.user.id
            }
        )
        return Response({'message': 'Course material deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    logger.error(
            "Invalid request method.",
            extra={
                'user': request.user.id
            }
        )
    return Response({'error': 'Invalid request method'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def tutor_course_search(request):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
    
    if not user.is_a_teacher:
        logger.error( "Only tutors can make this request.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "Only tutors can make this request."}, status=status.HTTP_401_UNAUTHORIZED )

    try:
        tutor = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        logger.error( "Teacher Not Found", extra={ 'user': request.user.id } )
        return Response({'error': 'Teacher Not Found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get courses assigned to the tutor
    assigned_courses = tutor.courses.all()

    # Filter courses based on any additional search parameters if needed
    keyword = request.query_params.get('keyword', None)
    
    if keyword:
        assigned_courses = assigned_courses.filter(course_title__icontains=keyword)
        
    # Paginate the results
    paginator = PaginationClass()
    paginated_courses = paginator.paginate_queryset(assigned_courses, request)


    # Serialize the courses
    course_serializer = CourseSerializer(paginated_courses, many=True)

    # Create the response
    response_data = {
        'count': paginator.page.paginator.count,
        'next': paginator.get_next_link(),
        'previous': paginator.get_previous_link(),
        'courses': course_serializer.data,
    }

    return Response(response_data)

    
@api_view(['GET'])
def student_course_search(request):
    user = request.user
    
    if not user.is_authenticated:
        logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
    
    if not user.is_a_student:
        logger.error( "Only students can make this request.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "Only students can make this request."}, status=status.HTTP_401_UNAUTHORIZED )

    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        logger.error( "Student Not Found", extra={ 'user': request.user.id } )
        return Response({'error': 'Student not found'}, status=404)
    
    # Get courses registered by the student
    registered_courses = student.registered_courses.all()

    # Filter courses based on the keyword if provided
    keyword = request.query_params.get('keyword')
    
    if keyword:
        query = Q()
        for word in keyword.split():
            query |= Q(course_title__icontains=word) | Q(course_code__icontains=word)
        registered_courses = registered_courses.filter(query)

    # Perform pagination
    paginator = PaginationClass()
    paginated_courses = paginator.paginate_queryset(registered_courses, request)

    # Serialize the courses
    course_serializer = CourseSerializer(paginated_courses, many=True)

    # Create the response
    response_data = {
        'count': paginator.page.paginator.count,
        'next': paginator.get_next_link(),
        'previous': paginator.get_previous_link(),
        'courses': course_serializer.data,
    }
    
    return Response(response_data)
    
    



