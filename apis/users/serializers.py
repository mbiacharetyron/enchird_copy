from apis.users.models import User
from rest_framework import serializers
from apis.teachers.models import Teacher
from apis.utils import validate_password
from django.contrib.auth.models import Permission


class UserSerializer(serializers.ModelSerializer):

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    picture = serializers.CharField(allow_null=True, required=False)
    email = serializers.EmailField(required=True, allow_null=False, allow_blank=False)
    groups = serializers.SerializerMethodField()
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    username = serializers.CharField(max_length=100, required=True)

    class Meta:

        model = User
        fields = ['id', 'reference', 'phone', 'email', 'username', 'first_name', 'nationality',
                   'last_name', 'gender', 'date_of_birth', 'is_active', 'is_admin', 'role',
                   'is_a_student', 'is_a_teacher', 'groups', 'picture', 'is_faculty_member']
        read_only_fields = ['is_active', 'reference', 'is_a_student', 'is_a_teacher', 'is_admin', 'is_superuser']
    
    def get_groups(self, obj):
        return [group.name for group in obj.groups.all()]
    
    def to_representation(self, instance):
        if isinstance(instance, Teacher):
            # Handle Teacher instance
            return {
                'email': instance.user.email
            }
        return super(UserSerializer, self).to_representation(instance)


class UserUpdateSerializer(serializers.ModelSerializer):
    

    first_name = serializers.CharField(required=True)
    picture = serializers.CharField(allow_null=True, required=False)
    last_name = serializers.CharField(required=True)
    groups = serializers.SerializerMethodField()
    date_of_birth = serializers.DateField(required=False, allow_null=True)

    class Meta:

        model = User
        fields = ['id', 'reference', 'phone', 'picture', 'first_name', 
                   'last_name', 'date_of_birth', 'is_active', 'is_admin',
                  'is_a_student', 'is_a_teacher', 'groups', 'email']
        read_only_fields = ['is_active', 'reference', 'is_a_student', 'is_a_teacher']


class UserPasswordSerializer(serializers.Serializer):

    password = serializers.CharField(
        max_length=100,
        # validators=[validate_password]
    )


class LoginSerializer(serializers.Serializer):
    """Docstring for class."""

    email = serializers.CharField(max_length=100, required=True)
    password = serializers.CharField(max_length=100, required=True)


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']


class LogoutSerializer(serializers.ModelSerializer):
    pass


class ResetPasswordSerializer(serializers.Serializer):

    email = serializers.CharField(max_length=100, required=True)


class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(max_length=100)
    new_password = serializers.CharField(max_length=100)
    

