from .models import *
from apis.users.models import User
from rest_framework import serializers
from apis.users.serializers import UserSerializer
from apis.courses.serializers import CourseSerializer





class ChatGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatGroup
        fields = ['id', 'name', 'course', 'code', 'created_at']
        read_only_fields = ['code']
        

class GroupMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    group = serializers.PrimaryKeyRelatedField(
        queryset=ChatGroup.objects.all(), 
        allow_null=True,
        allow_empty=True,
        required=False,
        write_only=True
    )
    group_info = serializers.SerializerMethodField(read_only=True)
    response_to_info = serializers.SerializerMethodField(read_only=True)
    # group_info = ChatGroupSerializer(read_only=True)
    
    class Meta:
        model = GroupMessage
        fields = ['id', 'content', 'sender', 'group_info', 'group', 'attachment', 'response_to', 'response_to_info', 'timestamp']
        read_only_fields = ['sender', 'response_to_info']
        write_only_fields = ['response_to']

    def get_group_info(self, obj):
        group = obj.group
        if group:
            return ChatGroupSerializer(group).data
        return None 
    
    def get_response_to_info(self, obj):
        response_to = obj.response_to
        if response_to:
            return self.__class__(response_to).data
        return None



class DirectMessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all().filter(
            is_deleted=False
        ),
        allow_null=False,
        allow_empty=False,
        required=True,
        write_only=True
    )
    receiver = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all().filter(
            is_deleted=False
        ),
        allow_null=False,
        allow_empty=False,
        required=True,
        write_only=True
    )
    sender_profile = serializers.SerializerMethodField(read_only=True)
    receiver_profile = serializers.SerializerMethodField(read_only=True)
    
    
    class Meta:
        model = DirectMessage
        fields = ['id', 'sender', 'receiver', 'sender_profile', 'receiver_profile', 'content', 'attachment', 'is_read', 'timestamp']
        read_only_fields = ['sender_profile', 'receiver_profile']
        write_only_fields = ['sender', 'receiver']
        
    def get_sender_profile(self, obj):
        sender = obj.sender
        if sender:
            return UserSerializer(sender).data
        return None
    
    def get_receiver_profile(self, obj):
        receiver = obj.receiver
        if receiver:
            return UserSerializer(receiver).data
        return None
    
    

class MeetingSerializer(serializers.ModelSerializer):
    course = CourseSerializer()
    created_by = UserSerializer()
    
    class Meta:
        model = ZoomMeeting
        fields = ['id', 'topic', 'course', 'meeting_id', 'start_time', 'duration',
                  'join_url', 'password', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at']


