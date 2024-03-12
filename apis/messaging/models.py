import random
import string
from django.db import models
from apis.users.models import User
from apis.courses.models import Course



# Create your models here.
class DirectMessage(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    attachment = models.CharField(max_length=255, null=True, blank=True) 
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp'] 

    def __str__(self):
        return f"{self.sender} to {self.receiver} - {self.timestamp}"



class ChatGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chat_groups')
    code = models.CharField(max_length=10, unique=True, blank=False, null=False)
    members = models.ManyToManyField(User, blank=True, related_name='chat_groups')
    created_at = models.DateTimeField(
        db_column="creation_date",
        auto_now_add=True
    )
    
    def save(self, *args, **kwargs):
        # Generate a random code when a group is created
        if not self.code:
            self.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name


class GroupMessage(models.Model):
    content = models.TextField()
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    # sender = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages')
    attachment = models.CharField(max_length=255, null=True, blank=True)
    # response_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='responses')

    def __str__(self):
        # return f'{self.sender.username}: {self.content}'
        return f'{self.sender}: {self.content}'
    
    class Meta:
        db_table = "group_messages"
        
    
class ZoomMeeting(models.Model):
    topic = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=False, blank=False)
    meeting_id = models.CharField(max_length=255, unique=True)
    start_time = models.DateTimeField()
    duration = models.IntegerField()  # in minutes
    join_url = models.URLField()
    password = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name='meeting_creator'
    )


    def __str__(self):
        return self.topic  
    
    
