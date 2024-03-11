import random
import hashlib
import datetime
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import RegexValidator
from apis.faculty.models import Faculty, Department



# Create your models here.
class Applicant(models.Model):

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending'),
    ]

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,13}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 13 digits allowed.")

    applicant_id = models.CharField(max_length=255, blank=False, null=False, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    nationality = models.CharField(max_length=255)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    email = models.EmailField()
    phone = models.CharField(max_length=15, validators=[phone_regex])  
    id_card_number = models.CharField(max_length=20, unique=True)
    scanned_id_document = models.CharField(max_length=255, null=False, blank=False) #FileField(upload_to='scanned_id_documents/')
    profile_picture = models.CharField(max_length=255) 
    primary_location = models.CharField(max_length=255)
    secondary_location = models.CharField(max_length=255, blank=True, null=True)
    guardian1_name = models.CharField(max_length=255)
    guardian1_contact = models.CharField(max_length=15)
    guardian2_name = models.CharField(max_length=255, blank=True, null=True)
    guardian2_contact = models.CharField(max_length=15, blank=True, null=True)
    motivation_letter = models.TextField()
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default="pending")
    is_deleted = models.BooleanField(default=False)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        null=True
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True
    )
    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )


    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = "applicants"


@receiver(post_save, sender=Applicant, dispatch_uid="update_applicant_id")
def update_applicant_id(instance, **kwargs):
    if not instance.applicant_id:
        instance.applicant_id = 'APL_' + str(instance.id).zfill(8)
        instance.save()


class AchievementDocument(models.Model):
    applicant = models.ForeignKey(
        Applicant,
        on_delete=models.CASCADE,
        related_name='applicant_achievements'
    )
    name = models.CharField(max_length=255)
    document = models.CharField(max_length=255) #FileField(upload_to='achievement_documents/')
    description = models.TextField()

    def __str__(self):
        return self.name


