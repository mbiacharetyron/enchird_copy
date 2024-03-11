import hashlib
import datetime
from django.db import models
from apis.users.models import User
from django.dispatch import receiver
# from apis.teachers.models import Teacher
from django.db.models.signals import post_save
from apis.faculty.models import Faculty, Department



class Course(models.Model):

    course_id = models.CharField(max_length=255, blank=False, null=False, unique=True)
    course_title = models.CharField(max_length=100, blank=False,null=False, unique=True)
    course_code = models.CharField(max_length=10, blank=False,null=False, unique=True)
    description = models.TextField(max_length=255, null=True, blank=True)
    course_level = models.CharField(max_length=4, blank=True, null=True)
    class_schedule = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    term = models.CharField(max_length=50, blank=True, null=True)
    credits = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    course_status = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='course_faculty'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='course_department'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name='course_modifier'
    )
    
    def __str__(self):
        return self.course_title

    class Meta:
        db_table = "course"


@receiver(post_save, sender=Course, dispatch_uid="update_course_id")
def update_course_id(instance, **kwargs):
    if not instance.course_id:
        instance.course_id = 'COUR_' + str(instance.id).zfill(8)
        instance.save()


class CourseMaterial(models.Model):

    def course_material_directory_path(self, filename):

        time = datetime.datetime.now().isoformat()
        plain = str(self.course) + '\0' + time
        return 'Course_Material/{0}/{1}'.format(
            hashlib.sha1(
                plain.encode('utf-8')
            ).hexdigest(),
            filename)

    # material_file = models.FileField(upload_to=course_material_directory_path)
    material_file = models.CharField(max_length=255, null=True, blank=True) 
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_materials')


    def __str__(self):
        return f"CourseMaterial: {self.material_file.name}"


class LibraryBook(models.Model):
    
    book_id = models.CharField(max_length=255, blank=False, null=False, unique=True)
    book_title = models.CharField(max_length=100, blank=False,null=False, unique=True)
    book_file = models.CharField(max_length=255, null=True, blank=True) 
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
    modified_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name='book_modifier'
    )
    
    def __str__(self):
        return self.book_title

    class Meta:
        db_table = "library_book"
    
@receiver(post_save, sender=LibraryBook, dispatch_uid="update_book_id")
def update_book_id(instance, **kwargs):
    if not instance.book_id:
        instance.book_id = 'BK' + str(instance.id).zfill(8)
        instance.save()



