from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from apis.users.models import User

# Create your models here.
class Level(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    

class Faculty(models.Model):

    faculty_id = models.CharField(max_length=255, blank=False, null=False, unique=True)
    name = models.CharField(max_length=100, blank=False,null=False, unique=True)
    abbrev = models.CharField(max_length=10, blank=False, null=False)
    description = models.CharField(max_length=244, blank=True, null=True)
    about = models.CharField(max_length=244, blank=True, null=True)
    levels = models.ManyToManyField(Level, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True
    )
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = "faculty"


@receiver(post_save, sender=Faculty, dispatch_uid="update_faculty_id")
def update_faculty_id(instance, **kwargs):
    if not instance.faculty_id:
        instance.faculty_id = 'FAC_' + str(instance.id).zfill(8)
        instance.save()


class Department(models.Model):
    department_id = models.CharField(max_length=255, blank=False, null=False, unique=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    abbrev = models.CharField(max_length=10, blank=False, null=False)
    description = models.CharField(max_length=244, blank=True, null=True)
    about = models.CharField(max_length=244, blank=True, null=True)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='departments'
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True
    )

    def __str__(self):
        return f"{self.name} of {self.faculty.name}"

    class Meta:
        db_table = "department"

@receiver(post_save, sender=Department, dispatch_uid="update_department_id")
def update_department_id(instance, **kwargs):
    if not instance.department_id:
        instance.department_id = 'DEP_' + str(instance.id).zfill(8)
        instance.save()


class Faculty_Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    faculty_member_id = models.CharField(max_length=255, blank=False, null=False, unique=True)
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    highest_degree = models.CharField(max_length=100, blank=True, null=True)
    post_at_faculty = models.CharField(max_length=100, blank=True, null=True)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='faculty_member'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name='faculty_member_creator'
    )

    def __str__(self):
        return self.department_id

    class Meta:
        db_table = "faculty_members"

@receiver(post_save, sender=Faculty_Member, dispatch_uid="update_faculty_member_id")
def update_faculty_member_id(instance, **kwargs):
    if not instance.faculty_member_id:
        instance.faculty_member_id = 'FM' + str(instance.id).zfill(8)
        instance.save()


class Job(models.Model):
    POSITION_CHOICES = [
        ('remote', 'Remote'),
        ('on_site', 'On Site'),
        ('hybrid', 'Hybrid'),
    ]

    EMPLOYMENT_CHOICES = [
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('full_time', 'Full-Time'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=200, null=True, blank=True)
    salary = models.CharField(max_length=100, null=True, blank=True)
    link = models.CharField(max_length=100, null=True, blank=True)
    experience = models.CharField(max_length=100, null=True, blank=True)
    position_type = models.CharField(max_length=20, choices=POSITION_CHOICES)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name='opportunity_creator'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = "opportunities"
    
    