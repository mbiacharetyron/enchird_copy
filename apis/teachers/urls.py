from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet

# Create a router
router = DefaultRouter()

# Register the TeacherViewSet
router.register(r'teacher', TeacherViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

