from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

# Create a router
router = DefaultRouter()

# Register the FacultyViewSet
router.register(r'admin/faculty', FacultyViewSet, basename='faculty')
router.register(r'department', DepartmentViewSet)
router.register(r'admin/faculty-member', FacultyMemberViewSet)
router.register(r'opportunities', JobViewSet)

urlpatterns = [
    path('', include(router.urls)),
]