import random
import hashlib
import datetime
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from rest_framework import permissions
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, AnonymousUser, PermissionsMixin


class UserManager(BaseUserManager):

    def update_user(self, password, user):

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, last_name, role, first_name, is_teacher, is_student):
        
        if not email:
            raise ValueError('User must have an email address')

        new_user = self.model(
            email=self.normalize_email(email),
            last_name=last_name,
            first_name=first_name,
            role=role,
            is_a_student=is_student,
            is_a_teacher=is_teacher,
        )

        new_user.save(using=self._db)

        return new_user

    def create_superuser(self, last_name, first_name, password, email):
        """Docstring for function."""
        if password is None:
            raise ValueError('The Password field must be set')

        new_user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role="superadmin",
            is_student=False,
            is_teacher=False
        )
        new_user.is_active = True
        new_user.is_admin = True
        new_user.is_staff = True
        new_user.is_superuser = True

        if password:
            new_user.set_password(password)  # Set the password if provided
        
        new_user.save(using=self._db)

        # Create a group with all permissions
        all_permissions = Permission.objects.all()
        superuser_group, created = Group.objects.get_or_create(name='Superuser')
        superuser_group.permissions.set(all_permissions)

        # Add the superuser to the Superuser Group
        new_user.groups.add(superuser_group)

        return new_user


    def make_random_password(self, length=10,
                             allowed_chars='abcdefghjkmnpqrstuvwxyz'
                                           'ABCDEFGHJKLMNPQRSTUVWXYZ'
                                           '23456789'):

        characters = list('abcdefghijklmnopqrstuvwxyz')

        characters.extend(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))

        characters.extend(list('0123456789'))

        characters.extend(list('!@#%^&*()?><:;'))

        password = ''
        for x in range(length):
            password += random.choice(characters)
        return password


class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ("superadmin", "Superadmin"),
        ("student", "Student"),
        ("faculty", "Faculty_Member"),
        ("teacher", "Teacher")
    )
    GENDERS = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'other'),
    )

    def user_directory_path(self, filename):

        time = datetime.datetime.now().isoformat()
        plain = str(self.phone) + '\0' + time
        return 'User/{0}/{1}'.format(
            hashlib.sha1(
                plain.encode('utf-8')
            ).hexdigest(),
            filename)

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,13}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 13 digits allowed.")

    reference = models.CharField(max_length=255, blank=True, null=True, unique=True)
    email = models.EmailField(max_length=100, unique=True, null=False, blank=False)
    username = models.CharField(max_length=50, unique=True, null=True, blank=True, default=None)
    picture = models.CharField(max_length=255, null=True, blank=True) #ImageField(default=None, null=True, upload_to=user_directory_path)
    phone = models.CharField(validators=[phone_regex], max_length=17, null=True, blank=True, default=None)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    is_a_student = models.BooleanField(default=False)
    is_a_teacher = models.BooleanField(default=False)
    nationality = models.CharField(max_length=255)
    is_faculty_member = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        choices=GENDERS,
        max_length=10
    )
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    role = models.CharField(
        choices=ROLE_CHOICES,
        default="student",
        max_length=10
    )
    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        db_column="modification_date",
        auto_now=True
    )
    password_requested_at = models.DateTimeField(null=True, blank=True)
    reset_token = models.CharField(max_length=255, null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name',]

    auto_create_schema = True

    def __str__(self):
        """Docstring for function."""
        return self.email if self.email else self.reference


    def is_super(self):
        """Docstring for function."""
        return self.is_admin and self.is_superuser

    def is_user(self):
        """Docstring for function."""
        return self.is_active 

    def is_student(self):
        """Docstring for function."""
        return self.is_student

    def is_teacher(self):
        return self.is_teacher

    def has_module_perms(self, app_label):
        """Docstring for function."""
        return self.is_admin

    def requested_token_valid(self):
        """Docstring for function."""
        time = timezone.now()
        second = self.password_requested_at + datetime.timedelta(hours=24)
        if time > second:
            return False
        return True

    class Meta:
        db_table = "users"



class CustomAnonymousUser(AnonymousUser):
    pass



@receiver(post_save, sender=User, dispatch_uid="update_user_reference")
def update_user_reference(instance, **kwargs):
    if not instance.reference:
        instance.reference = 'USR_' + str(instance.id).zfill(8)
        instance.save()







