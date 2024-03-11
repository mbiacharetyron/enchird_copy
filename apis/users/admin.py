from django.contrib import admin
from .models import User


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'is_active', 'role', 'is_a_student', 'is_a_teacher')
    list_filter = ('role', 'is_a_student', 'is_a_teacher')
    search_fields = ('email', 'first_name', 'last_name')


    