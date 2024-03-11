import logging
from rest_framework import permissions
from apis.courses.models import Course
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import BasePermission


logger = logging.getLogger("myLogger")


class IsStudentOrInstructorOfCourse(permissions.BasePermission):
    """
    Custom permission to allow only students registered to a course and
    instructors assigned to a course to make requests.
    """

    def has_permission(self, request, view):
        # Check if the user is a student or an instructor
        is_student = request.user.is_a_student
        is_instructor = request.user.is_a_teacher

        if not is_student and not is_instructor:
            return False

        # If it's a student, check if they are registered to the course
        if is_student:
            course_id = view.kwargs.get('course_id')
            return request.user.student.registered_courses.filter(id=course_id).exists()

        
        # If it's an instructor, check if they are assigned to the course
        if is_instructor:
            course_id = view.kwargs.get('course_id')

            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                logger.warning(
                    "Course Not Found",
                    extra={
                        'user': request.user.id
                    }
                )
                return Response({'error': 'Course Not Found'}, status=status.HTTP_404_NOT_FOUND)
                
            if is_instructor in course.instructors.all():
                print("true")
                return True
            # return request.user.teacher.assigned_courses.filter(id=course_id).exists()

        return False

