import datetime
import hashlib
from django.db import models
from apis.users.models import User
from django.dispatch import receiver
from apis.courses.models import Course
from django.db.models.signals import post_save
from apis.faculty.models import Faculty, Department



class Student(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=255, blank=False, null=False, unique=True)
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
    registered_courses = models.ManyToManyField(Course, related_name='students', blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )
    

    def __str__(self):
        return self.student_id

    class Meta:
        db_table = "students"


@receiver(post_save, sender=Student, dispatch_uid="update_student_reference")
def update_student_reference(instance, **kwargs):
    if not instance.student_id:
        instance.student_id = 'STU_' + str(instance.id).zfill(8)
        instance.save()
        
        