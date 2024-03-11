from .models import *
from apis.faculty.models import *
from apis.faculty.serializers import *
from rest_framework import serializers
from apis.users.serializers import UserSerializer
# from apis.courses.serializers import CourseSerializer




class CourseSerializer(serializers.ModelSerializer):
    
    instructor_details = UserSerializer(many=True, read_only=True, source='tutors') 
    faculty_details = serializers.SerializerMethodField(read_only=True)
    faculty = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all().filter(
            is_deleted=False
        ),
        allow_null=True,
        allow_empty=True,
        required=False,
        write_only=True
    )
    department_details = serializers.SerializerMethodField(read_only=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all().filter(
            is_deleted=False
        ),
        allow_null=True,
        allow_empty=True,
        required=False,
        write_only=True
    )

    class Meta:
        model = Course
        fields = ['id', 'course_id', 'course_code', 'course_title', 'faculty_details', 
                    'faculty', 'instructor_details', 'class_schedule', 'description', #'course_materials', 
                    'course_level', 'term', 'department', 'department_details', 'location', 'credits',
                    'is_deleted', 'course_status', 'created_at', 'created_by', 'modified_by']
        read_only_fields = ['id', 'course_id', 'instructor_details'] 

    def get_faculty_details(self, obj):
        faculty = obj.faculty
        if faculty:
            return FacultySerializer(faculty).data
        return None
    
    def get_department_details(self, obj):
        department = obj.department
        if department:
            return DepartmentSerializer(department).data
        return None

    def to_representation(self, instance):
        representation = super(CourseSerializer, self).to_representation(instance)

        # Override the created_by field to only include the user's email
        representation['created_by'] = instance.created_by.email if instance.created_by else None
        representation['modified_by'] = instance.modified_by.email if instance.modified_by else None

        return representation


class CourseMaterialSerializer(serializers.ModelSerializer):
    material_file = serializers.FileField(required=True)
    course = CourseSerializer(read_only=True)
    class Meta:
        model = CourseMaterial
        fields = ['id', 'material_file', 'description', 'course', 'uploaded_by', 'uploaded_at']

    def to_representation(self, instance):
        representation = super(CourseMaterialSerializer, self).to_representation(instance)

        # Override the course field to only include the course title
        representation['course'] = instance.course.course_title if instance.course else None

        return representation


class LibraryBookSerializer(serializers.ModelSerializer):

    class Meta:
        model = LibraryBook
        fields = ['id', 'book_id', 'book_title', 'is_deleted', 'book_file',
                    'created_at', 'created_by', 'modified_by']
        read_only_fields = ['id', 'book_id'] 

    def to_representation(self, instance):
        representation = super(LibraryBookSerializer, self).to_representation(instance)

        # Override the created_by field to only include the user's email
        representation['created_by'] = instance.created_by.email if instance.created_by else None
        representation['modified_by'] = instance.modified_by.email if instance.modified_by else None

        return representation


