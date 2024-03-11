from .views import CourseViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


# Create a router
router = DefaultRouter()

# Register the StudentViewSet with a base name 'student'
router.register(r'course', CourseViewSet)
router.register(r'library/book', LibraryBookViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('remove_course_material/<int:course_material_id>/', remove_course_material, name='remove_course_material'),
    path('unassign_teacher/<int:teacher_id>/course/<str:course_id>/', unassign_teacher, name='unassign_teacher'),
    path('assign_teacher/<int:teacher_id>/course/<str:course_id>/', assign_teacher, name='assign_teacher'),
    path('add_course_material/<str:course_id>/', add_course_material, name='add_course_material'),
    path('student-search/course/', student_course_search, name='student_course_search'),
    path('tutor-search/course/', tutor_course_search, name='tutor_course_search'),
]