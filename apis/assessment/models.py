import datetime
from django.db import models
from django.contrib import admin
from apis.users.models import User
from django.dispatch import receiver
from apis.courses.models import Course
from django.db.models.signals import post_save



# Register your models here.

class Assessment(models.Model):


    STRUCTURE_CHOICES = [
        ('text', 'Text'),
        ('mixed', 'Mixed'),
        ('mcq', 'Multiple Choice'),
    ]
    
    ASSESSMENT_TYPE_CHOICES = [
        ('exam', 'Exam'),
        ('ca', 'CA'),
    ]

    assessment_id = models.CharField(max_length=255, blank=False, null=False, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    structure = models.CharField(max_length=20, choices=STRUCTURE_CHOICES, default="mcq")
    duration = models.CharField(max_length=20, blank=True, null=True)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES, default="ca")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.assessment_id

    class Meta:
        db_table = "assessments"

@receiver(post_save, sender=Assessment, dispatch_uid="update_assessment_id")
def update_assessment_id(instance, **kwargs):
    if not instance.assessment_id:
        instance.assessment_id = 'ASM_' + str(instance.id).zfill(8)
        instance.save()


class Question(models.Model):

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    mark_allocated = models.CharField(max_length=20, null=True, blank=True)
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" Question for Assessment: {self.assessment.title}"


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Choice: {self.text} for Question: {self.question.text}"


class StudentResponse(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.PROTECT)
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    selected_choice = models.ForeignKey(Choice, on_delete=models.PROTECT, null=True, blank=True)
    text_response = models.TextField(null=True, blank=True)
    recorded_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )

    def __str__(self):
        return f"Response by {self.student.username} for Question: {self.question.text}"


class StudentAssessmentScore(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.PROTECT, null=True, blank=True)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    score = models.CharField(max_length=255)  # Assuming the score is an integer
    is_graded = models.BooleanField(default=False)

    def __str__(self):
        return f"Score for {self.student.username} in {self.assessment.title}"


class GradeSystem(models.Model):
    grade = models.CharField(unique=True, max_length=10)
    min_score = models.IntegerField()
    max_score = models.IntegerField()

    def __str__(self):
        return f"{self.grade}: {self.min_score}-{self.max_score}"





