import logging
from django.db.models import Q
from apis.courses.models import Course
from apis.teachers.models import Teacher
from apis.students.models import Student
from rest_framework.views import APIView
from apis.messaging.models import ChatGroup
from rest_framework import status, viewsets
from apis.applicants.models import Applicant
from rest_framework.response import Response
from rest_framework.decorators import api_view
from apis.faculty.models import Faculty, Department
from apis.courses.serializers import CourseSerializer
from apis.teachers.serializers import TeacherSerializer
from apis.students.serializers import StudentSerializer
from apis.messaging.serializers import ChatGroupSerializer
from apis.applicants.serializers import ApplicantSerializer
from apis.faculty.serializers import FacultySerializer, DepartmentSerializer
from .models import User  # Replace with your user model


logger = logging.getLogger("myLogger")


class EmailVerificationView(APIView):

    def get(self, request, verification_token):
        try:
            user = User.objects.get(reset_token=verification_token)
        except User.DoesNotExist:
            logger.error(
                "Invalid verification token.",
                extra={
                    'user': 'Anonymous'
                }
            )
            return Response(
                {'error': "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.reset_token = None
        user.save()
        logger.error(
            "Email Verified Successfully.",
            extra={
                'user': user.id
            }
        )

        return Response({"message": "Email verified successfully"})


@api_view(['GET'])
def admin_general_search(request):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
    
    if not user.is_admin:
        logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You do not have the necessary right."}, status=status.HTTP_401_UNAUTHORIZED )

    keyword = request.query_params.get('keyword', None)
    
    # Split the keyword into individual words
    keywords = keyword.split()
    
    # Create Q objects for each model and field
    course_queries = Q()
    teacher_queries = Q()
    student_queries = Q()
    faculty_queries = Q()
    applicant_queries = Q()
    department_queries = Q()
        
    for word in keywords:
        faculty_queries |= Q(name__icontains=word)
        department_queries |= Q(name__icontains=word)
        course_queries |= Q(course_title__icontains=word)
        teacher_queries |= Q(user__first_name__icontains=word) | Q(user__last_name__icontains=word)
        student_queries |= Q(user__first_name__icontains=word) | Q(user__last_name__icontains=word)
        applicant_queries |= Q(first_name__icontains=word) | Q(last_name__icontains=word)
    
    # Apply the combined queries along with other filters
    course_queryset = Course.objects.filter(course_queries, is_deleted=False).order_by('-created_at')
    applicant_queryset = Applicant.objects.filter(applicant_queries, is_deleted=False).order_by('-created_at')
    teacher_queryset = Teacher.objects.filter(teacher_queries, is_deleted=False).order_by('-created_at')
    student_queryset = Student.objects.filter(student_queries, is_deleted=False).order_by('-created_at')
    faculty_queryset = Faculty.objects.filter(faculty_queries, is_deleted=False).order_by('-created_at')
    department_queryset = Department.objects.filter(department_queries, is_deleted=False).order_by('-created_at')
    
    # Serialize the results
    course_serializer = CourseSerializer(course_queryset, many=True)
    teacher_serializer = TeacherSerializer(teacher_queryset, many=True)
    student_serializer = StudentSerializer(student_queryset, many=True)
    faculty_serializer = FacultySerializer(faculty_queryset, many=True)
    applicant_serializer = ApplicantSerializer(applicant_queryset, many=True)
    department_serializer = DepartmentSerializer(department_queryset, many=True)

    # Create the response
    response_data = {
        'teachers': teacher_serializer.data,
        'students': student_serializer.data,
        'courses': course_serializer.data,
        'applicants': applicant_serializer.data,
        'faculties': faculty_serializer.data,
        'departments': department_serializer.data,
    }

    return Response(response_data)


@api_view(['GET'])
def tutor_general_search(request):
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
        logger.warning( "Tutor Not Found", extra={ 'user': request.user.id } )
        return Response({'error': 'Tutor Not Found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get groups created by the tutor
    created_groups = ChatGroup.objects.filter(course__tutors=tutor)

    # Get the courses assigned to the tutor
    assigned_courses = tutor.courses.all()
    
    # Get the students registered to the tutor's courses
    registered_students = Student.objects.filter(registered_courses__in=assigned_courses)

    keyword = request.query_params.get('keyword', None)
    
    # Split the keyword into individual words
    keywords = keyword.split()
    
    # Create Q objects for each model and field
    group_queries = Q()
    course_queries = Q()
    student_queries = Q()
        
    for word in keywords:
        group_queries |= Q(name__icontains=word)
        course_queries |= Q(course_title__icontains=word)
        student_queries |= Q(user__first_name__icontains=word) | Q(user__last_name__icontains=word)
    
    # Apply the combined queries along with other filters
    group_queryset = created_groups.filter(group_queries).order_by('-created_at')
    course_queryset = assigned_courses.filter(course_queries, is_deleted=False).order_by('-created_at')
    student_queryset = registered_students.filter(student_queries, is_deleted=False).order_by('-created_at')
    
    # Serialize the results
    course_serializer = CourseSerializer(course_queryset, many=True)
    group_serializer = ChatGroupSerializer(group_queryset, many=True)
    student_serializer = StudentSerializer(student_queryset, many=True)

    # Create the response
    response_data = {
        'students': student_serializer.data,
        'courses': course_serializer.data,
        'groups': group_serializer.data,
    }

    return Response(response_data)





