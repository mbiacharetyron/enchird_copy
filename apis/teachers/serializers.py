from apis.faculty.models import *
from apis.users.models import User
from apis.faculty.serializers import *
from rest_framework import serializers
from apis.courses.models import Course
from apis.teachers.models import Teacher
from apis.users.serializers import UserSerializer
from apis.courses.serializers import CourseSerializer
from drf_writable_nested import WritableNestedModelSerializer



class TeacherSerializer(WritableNestedModelSerializer):

    user = UserSerializer(read_only=True)
    courses = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all().filter(
            is_deleted=False
        ),
        allow_null=True,
        allow_empty=True,
        required=False,
        many=True,
        write_only=True,
        # read_only=True
    )
    faculties = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all().filter(
            is_deleted=False
        ),
        allow_null=True,
        allow_empty=True,
        required=False,
        many=True,
        write_only=True
    )
    departments = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all().filter(
            is_deleted=False
        ),
        allow_null=True,
        allow_empty=True,
        required=False,
        many=True,
        write_only=True
    )
    courses_detail = CourseSerializer(many=True, read_only=True)
    faculties_detail = FacultySerializer(many=True, read_only=True, source='faculty')
    departments_detail = DepartmentSerializer(many=True, read_only=True)

    class Meta:

        model = Teacher
        fields = ['user', 'teacher_id', 'highest_degree', 'about', 'description', 'departments', 'faculties',
                   'courses', 'is_deleted', 'created_at', 'departments_detail', 'courses_detail', 'faculties_detail']
        read_only_fields = ['user', 'teacher_id', 'courses_detail', 'faculty_details']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        # Fetch detailed information for ManyToMany relationships
        data['courses_detail'] = CourseSerializer(instance.courses.all(), many=True).data
        data['faculties_detail'] = FacultySerializer(instance.faculties.all(), many=True).data
        data['departments_detail'] = DepartmentSerializer(instance.departments.all(), many=True).data

        return data


