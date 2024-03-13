from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


# Create a router
router = DefaultRouter()

# Register the StudentViewSet with a base name 'student'
# router.register(r'course', CourseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('messaging/', CreateRoom, name='create-room'),
    path('chat-messaging/<str:other_user>/<str:token>/', MessageView, name='chat'),
    path('group-messaging/<str:group_id>/<str:token>/', GroupMessageView, name='room'),
    
    path('send-direct-message/<int:receiver_id>/', send_direct_message, name='send_direct_message'),
    path('groups/<int:group_id>/messages/', MessageListAPIView.as_view(), name='message-list'),
    path('zoom/meeting/<int:meeting_id>/', get_meeting_details, name='get_meeting_details'),
    path('zoom/create-meeting/<int:course_id>/', create_meeting, name='create_meeting'),
    path('courses/<int:course_id>/create-group/', create_group, name='create_group'),
    path('student-search/group/', student_group_search, name='student_group_search'),
    path('groups/<int:group_id>/send-message/', send_message, name='send_message'),
    path('messages/<int:user_id>/', list_user_messages, name='list_user_messages'),
    path('tutor-search/group/', tutor_group_search, name='tutor_group_search'),
    path('zoom/meeting/', list_meetings, name='list_meetings'),
    path('inbox/', inbox_messages, name='inbox_messages'),
    path('join-group/', join_group, name='join_group'),
]