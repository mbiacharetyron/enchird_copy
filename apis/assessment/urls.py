from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

# Create a router
router = DefaultRouter()

# Register the GradeSystemViewSet
router.register(r'admin/grade-system', GradeSystemViewSet)
# router.register(r'courses/student/grades', CourseGradeViewSet, basename='course-grades')


urlpatterns = [
    path('', include(router.urls)),
    path('assessments/<int:assessment_id>/grade/<int:student_id>/', get_student_assessment_grade, name='get_student_assessment_grade'),
    path('assessments/<int:assessment_id>/record-score/<int:student_id>/', record_student_score, name='record_student_score'),
    path('assessments/<int:assessment_id>/add_text_question/', create_structural_question, name='add_structural_question'),
    path('assessments/<int:assessment_id>/mcq-submit/', submit_assessment_responses, name='submit_assessment_responses'),
    path('assessment-submissions/<int:assessment_id>/', get_assessment_submissions, name='get_assessment_submissions'),
    path('assessments/<int:assessment_id>/add_mcq_question/', create_question_with_choices, name='add_mcq_question'),
    path('assessments/<int:assessment_id>/submit/', submit_structural_responses, name='submit_structural_responses'),
    path('assessment-results/<int:assessment_id>/', get_assessment_results, name='get_assessment_results'),
    path('courses/<int:course_id>/grades', get_all_students_scores, name='get-all-students-course-grade'),
    path('courses/<int:course_id>/student/grades', calculate_student_grade, name='student-course-grade'),
    path('assessments/<int:assessment_id>/<int:question_id>/', update_question, name='update_question'),
    path('list-assessments/<str:type>/', list_assessment_results, name='list-ca-assessments'),
    path('assessments/<int:assessment_id>/', get_assessment_details, name='get_assessment'),
    path('create_assessment/', create_assessment, name='create_assessment'),
    path('list-assessments/', list_assessments, name='list-assessments'),

]