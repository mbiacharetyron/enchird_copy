from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApplicantViewSet

# Create a router
router = DefaultRouter()

# Register the TeacherViewSet
router.register(r'applicant', ApplicantViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

