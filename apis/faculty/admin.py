from django.contrib import admin 
from .models import Faculty, Department, Faculty_Member


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('faculty_id', 'name', 'abbrev', 'is_deleted', 'created_at', 'created_by')
    search_fields = ['faculty_id', 'name', 'abbrev']
    list_filter = ['is_deleted']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_id', 'name', 'faculty', 'is_deleted', 'created_at', 'created_by')
    search_fields = ['department_id', 'name', 'faculty']
    list_filter = ['is_deleted']


@admin.register(Faculty_Member)
class FacultyMemberAdmin(admin.ModelAdmin):

    list_display = ('user_email', 'user_first_name', 'user_last_name', 'user_date_of_birth', 'faculty_member_id', 'highest_degree', 'post_at_faculty', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('user__email', 'faculty_member_id', 'user__first_name', 'user__last_name')
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

    user_email.short_description = 'Faculty Member Email'  # Customize column header names
    user_first_name.short_description = 'First Name'
    user_last_name.short_description = 'Last Name'
    user_date_of_birth.short_description = 'Date of birth'


