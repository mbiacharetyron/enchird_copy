from apis.faculty.models import *
from apis.users.models import User
from apis.faculty.serializers import *
from rest_framework import serializers
from apis.students.models import Student
from apis.users.serializers import UserSerializer
from apis.courses.serializers import CourseSerializer
from drf_writable_nested import WritableNestedModelSerializer



class StudentSerializer(WritableNestedModelSerializer):

    user = UserSerializer(read_only=True)
    faculty = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all().filter(
            is_deleted=False
        ),
        allow_null=True,
        allow_empty=True,
        required=False,
        write_only=True
    )
    faculty_details = FacultySerializer(source='faculty', read_only=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all().filter(
            is_deleted=False
        ),
        allow_null=True,
        allow_empty=True,
        required=False,
        write_only=True
    )
    department_details = DepartmentSerializer(source='department', read_only=True)
    registered_courses = CourseSerializer(many=True, read_only=True)

    class Meta:

        model = Student
        fields = ['user', 'student_id', 'faculty', 'faculty_details', 'department', 
                    'department_details', 'registered_courses', 'is_deleted', 'created_at']
        read_only_fields = ['user', 'student_id', 'faculty_details', 'department_details']



