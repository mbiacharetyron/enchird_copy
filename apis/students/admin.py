from django.contrib import admin
from django import forms
from .models import Student
from apis.users.models import User
from django.db.models.signals import pre_delete
from django.dispatch import receiver



@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    # form = StudentAdminForm  # Use the custom form
    list_display = ('user_email', 'user_first_name', 'user_last_name', 'user_date_of_birth', 'student_id', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('user__email', 'student_id', 'user__first_name', 'user__last_name')
    # inlines = [UserInline]  # Include the UserInline inlines

    list_select_related = ('user',)  # Use list_select_related for efficient related field fetching

    def user_email(self, obj):
        return obj.user.email

    def user_first_name(self, obj):
        return obj.user.first_name

    def user_last_name(self, obj):
        return obj.user.last_name

    def user_date_of_birth(self, obj):
        return obj.user.date_of_birth

    user_email.short_description = 'Student Email'  # Customize column header names
    user_first_name.short_description = 'First Name'
    user_last_name.short_description = 'Last Name'
    user_date_of_birth.short_description = 'Date of birth'

    



# admin.site.register(Student, StudentAdmin)

