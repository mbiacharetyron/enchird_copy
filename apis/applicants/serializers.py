from apis.faculty.models import *
from apis.faculty.serializers import *
from rest_framework import serializers
from django.contrib.auth.models import Permission
from .models import Applicant, AchievementDocument



class AchievementDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AchievementDocument
        fields = ['id', 'name', 'document', 'description']


class ApplicantSerializer(serializers.ModelSerializer):

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True, allow_null=False, allow_blank=False)
    nationality = serializers.CharField(required=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    primary_location = serializers.CharField(max_length=100, required=True)
    past_achievement_documents = AchievementDocumentSerializer(many=True, required=False)
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
        model = Applicant
        fields = ['id', 'applicant_id', 'first_name', 'last_name', 'nationality', 'gender', 'email', 'faculty',
                   'department', 'primary_location', 'secondary_location', 'guardian1_name', 'guardian1_contact', 'status', 
                   'date_of_birth', 'phone', 'id_card_number', 'scanned_id_document', 'profile_picture', 'faculty_details',
                   'department_details', 'guardian2_name', 'guardian2_contact', 'motivation_letter', 'past_achievement_documents']
        read_only_fields = ['applicant_id', 'past_achievement_documents', 'faculty_details', 'department_details', 'status']



