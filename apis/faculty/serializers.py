from .models import *
from apis.users.models import User
from rest_framework import serializers
from apis.users.serializers import UserSerializer
from drf_writable_nested import WritableNestedModelSerializer



class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'name']
        
        

class FacultySerializer(WritableNestedModelSerializer):

    name = serializers.CharField(allow_null=False, required=True)
    abbrev = serializers.CharField(required=True)
    levels = LevelSerializer(many=True, required=False, read_only=True)

    class Meta:

        model = Faculty
        fields = ['id', 'name', 'faculty_id', 'abbrev', 'description',
                   'levels', 'about', 'is_deleted', 'created_at']
        read_only_fields = ['id', 'faculty_id', 'created_at', 'levels']



class DepartmentSerializer(serializers.ModelSerializer):
    faculty = serializers.PrimaryKeyRelatedField(
        queryset=Faculty.objects.all().filter(
            is_deleted=False
        ),
        allow_null=True,
        allow_empty=True,
        required=False,
        write_only=True
    )
    abbrev = serializers.CharField(required=True)
    faculty_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'department_id', 'faculty_details', 'abbrev',
                  'faculty', 'about', 'description', 'is_deleted', 'created_at']
        read_only_fields = ['id', 'department_id', 'created_at', 'faculty_details']

    def get_faculty_details(self, obj):
        faculty = obj.faculty
        if faculty:
            return FacultySerializer(faculty).data
        return None


class FacultyMemberSerializer(WritableNestedModelSerializer):

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

    class Meta:

        model = Faculty_Member
        fields = ['user', 'faculty_member_id', 'highest_degree', 'post_at_faculty', 'faculty', 'faculty_details', 'department', 'department_details', 'is_deleted', 'created_at']
        read_only_fields = ['user', 'faculty_member_id', 'faculty_details', 'department_details']


class JobSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'location', 'position_type', 'employment_type', 
                  'company', 'city', 'salary', 'experience', 'link', 'created_by', 'created_at']
        read_only_fields = ['id']


