from django.contrib import admin
from .models import Applicant, AchievementDocument


# Register your models here.

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('applicant_id', 'first_name', 'last_name', 'email', 'is_deleted', 'status', 'created_at')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ( 'is_deleted', 'created_at')

@admin.register(AchievementDocument)
class AchievementDocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'applicant', 'description')
    search_fields = ('name', 'applicant__first_name', 'applicant__last_name')


