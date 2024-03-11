from .models import *
from django.contrib import admin




# Register your models here.

@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'timestamp', 'is_read')
    search_fields = ('sender__username', 'receiver__username', 'content')
    list_filter = ('is_read',)

@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')#, 'course')
    search_fields = ('name', 'code',)# 'course__name')

@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'content', 'timestamp', 'group')
    search_fields = ('sender__username', 'content', 'group__name')
    list_filter = ('group',)
    
@admin.register(ZoomMeeting)
class ZoomMeetingAdmin(admin.ModelAdmin):
    list_display = ('topic', 'course', 'start_time', 'duration', 'join_url', 'password', 'created_by')
    search_fields = ('created_by__username', 'topic')    
    
    