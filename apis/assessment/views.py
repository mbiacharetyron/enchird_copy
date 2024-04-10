import base64
import hashlib
import logging
import binascii
import cryptography
import pandas as pd
from .models import *
from .serializers import *
from django.conf import settings
from django.db import transaction
from django.shortcuts import render
from django.db.models import Sum, F
from apis.courses.models import Course 
from cryptography.fernet import Fernet
from apis.students.models import Student
from apis.teachers.models import Teacher
from rest_framework import status, viewsets
from rest_framework.response import Response
from cryptography.fernet import InvalidToken
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import permission_classes
from apis.assessment.serializers import AssessmentSerializer


logger = logging.getLogger("myLogger")

# Create your views here.

@api_view(['POST'])
def create_assessment(request):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."},
            status=status.HTTP_401_UNAUTHORIZED )

    if user.is_a_teacher is False:
        logger.error(
            "Only teachers can create assessments.",
            extra={ 'user': user.id } )
        return Response( { "error": "Only teachers can create assessments." },
            status.HTTP_403_FORBIDDEN )
    
    serializer = AssessmentSerializer(data=request.data)

    if serializer.is_valid():
        
        serializer.save(instructor=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def encrypt_float(float_value):
    # Convert the float to a string for encryption
    input_string = str(float_value)
    return encrypt_string(input_string)


def decrypt_float(encrypted_text):
    # Decrypt the string and convert it back to a float
    decrypted_string = decrypt_string(encrypted_text)
    return float(decrypted_string)


def encrypt_string(input_string):
    cipher_suite = Fernet(settings.FERNET_KEY.encode('utf-8'))

    # Ensure input_string is converted to bytes
    input_bytes = input_string.encode('utf-8')
    print(input_bytes)

    # Encrypt the bytes
    encrypted_bytes = cipher_suite.encrypt(input_bytes)
    print(encrypted_bytes)

    # Convert encrypted bytes to base64-encoded string
    encrypted_string = encrypted_bytes.decode('utf-8')
    print(encrypted_string) 

    return encrypted_string


def decrypt_string(encrypted_text):
    try:
        cipher_suite = Fernet(settings.FERNET_KEY.encode('utf-8'))

        # Ensure encrypted_text is converted to bytes
        encrypted_bytes = encrypted_text.encode('utf-8')
        
        # Decrypt the bytes
        decrypted_text = cipher_suite.decrypt(encrypted_bytes).decode('utf-8')
        
        return decrypted_text
    except (binascii.Error, cryptography.fernet.InvalidToken) as e:
        # Log the error for troubleshooting
        logger.error(f"Decryption error: {str(e)}", extra={'user': 'Anonymous'})
        raise


@api_view(['POST'])
def create_question_with_choices(request, assessment_id):
    user = request.user
    if not user.is_authenticated:
        logger.error( "You do not have the necessary rights.", extra={'user': 'Anonymous'} )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

    if user.is_a_teacher is False:
        logger.error("Only teachers can add questions.", extra={'user': user.id})
        return Response(  {"error": "Only teachers can add questions."}, status.HTTP_403_FORBIDDEN )

    try:
        print(assessment_id)
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error("Assessment Not Found.", extra={'user': user.id})
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    if assessment.structure != "mcq":
        logger.error("This assessment is not an mcq assessment.", extra={'user': user.id})
        return Response({'error': 'This assessment is not an mcq assessment'}, status=status.HTTP_404_NOT_FOUND)

    if 'file' in request.data:
        try:
            with transaction.atomic():
                file = request.data['file']
                df = pd.read_excel(file)

                for index, row in df.iterrows():
                    question_text = row['Question']
                    choices = [row['Choice1'], row['Choice2'], row['Choice3'], row['Choice4']]
                    correct_choice = row['CorrectChoice']

                    # Encrypt question text
                    encrypted_question_text = encrypt_string(question_text)
                    print(encrypted_question_text) 
                     
                    # Save the question first
                    question_data = {'text': encrypted_question_text, 'assessment': assessment.id}
                    question_serializer = QuestionSerializer(data=question_data)
                    if question_serializer.is_valid():
                        question = question_serializer.save(assessment=assessment)

                        # Save choices for the question
                        for choice_text in choices:
                             
                            # Encrypt choice text
                            encrypted_choice_text = encrypt_string(choice_text) 


                            # Check if the choice is correct
                            is_correct = choice_text == correct_choice

                            choice_data = {'question': question.id, 'text': encrypted_choice_text, 'is_correct': is_correct}
                            choice_serializer = ChoiceSerializer(data=choice_data)
                            if choice_serializer.is_valid():
                                choice_serializer.save(question=question)
                            else:
                                # Handle choice serializer validation errors
                                logger.info(str(choice_serializer.errors), extra={'user': user.id})
                                raise serializers.ValidationError(choice_serializer.errors)
                    else:
                        # Handle question serializer validation errors
                        logger.info(str(question_serializer.errors), extra={'user': user.id})
                        raise serializers.ValidationError(question_serializer.errors)

            logger.info('Questions and choices created successfully', extra={'user': user.id})
            return Response({'message': 'Questions and choices created successfully'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error( str(e), extra={ 'user': None } )
            return Response( {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    if 'file' not in request.data:
        try:
            with transaction.atomic():
                question_data = request.data.get('question', {})
                choices_data = request.data.get('choices', [])

                # Encrypt question text
                encrypted_question_text = encrypt_string(question_data.get('text', ''))

                question_serializer = QuestionSerializer(data={'text': encrypted_question_text, 'assessment': assessment.id})
                if question_serializer.is_valid():
                    # Save the question first
                    question = question_serializer.save(assessment=assessment)

                    # Save choices for the question
                    for choice_data in choices_data:
                        # Encrypt choice text
                        encrypted_choice_text = encrypt_string(choice_data.get('text', ''))

                        # Check if the choice is correct
                        is_correct = choice_data.get('is_correct', False)

                        # Associate the choice with the saved question
                        choice_data['question'] = question.id
                        choice_data['text'] = encrypted_choice_text
                        choice_data['is_correct'] = is_correct

                        choice_serializer = ChoiceSerializer(data=choice_data)
                        if choice_serializer.is_valid():
                            choice_serializer.save(question=question)

                    logger.info("Question and choices created successfully.", extra={'user': user.id})
                    return Response({'message': 'Question and choices created successfully'}, status=status.HTTP_201_CREATED)

                logger.info(str(question_serializer.errors), extra={'user': user.id})
                return Response({'error': question_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Rollback transaction and raise validation error
            transaction.rollback()
            logger.error(
                str(e),
                extra={
                    'user': None
                }
            )
            return Response(
                {"error": str(e)},
                status=status.HTTP_412_PRECONDITION_FAILED)


@api_view(['POST'])
def create_structural_question(request, assessment_id):
    user = request.user
    if not user.is_authenticated:
        logger.error( "You do not have the necessary rights.", extra={'user': 'Anonymous'} )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

    if user.is_a_teacher is False:
        logger.error("Only teachers can add questions.", extra={'user': user.id})
        return Response(  {"error": "Only teachers can add questions."}, status.HTTP_403_FORBIDDEN )

    try:
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error("Assessment Not Found.", extra={'user': user.id})
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    if assessment.structure != "text":
        logger.error("This assessment is not a structural assessment.", extra={'user': user.id})
        return Response({'error': 'This assessment is not a structural assessment'}, status=status.HTTP_404_NOT_FOUND)

    try:
        with transaction.atomic():
            question_serializer = TextQuestionSerializer(data=request.data)
            if question_serializer.is_valid(raise_exception=True):
                
                question_data = question_serializer.validated_data['text']
                
                # Check if question_data is not an empty string
                if not question_data.strip():
                    logger.error("Empty question text for structural question.", extra={'user': user.id})
                    return Response({'error': 'Empty question text for structural question'},
                                    status=status.HTTP_400_BAD_REQUEST)
                
                # Encrypt question text
                encrypted_question_text = encrypt_string(question_data)
            
                # Save the question first
                question = question_serializer.save(assessment=assessment, text=encrypted_question_text)

                logger.info("Question added to assessment successfully.", extra={'user': user.id})
                return Response({'message': 'Question added to assessment successfully'}, status=status.HTTP_201_CREATED)

            logger.error(str(question_serializer.errors), extra={'user': user.id})
            return Response({'error': question_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        # Rollback transaction and raise validation error
        transaction.rollback()
        logger.error( str(e), extra={ 'user': None } )
        return Response( {"error": str(e)}, status=status.HTTP_412_PRECONDITION_FAILED)


@api_view(['PUT'])
def update_question(request, assessment_id, question_id):
    user = request.user

    if not user.is_authenticated:
        logger.error("You must provide valid authentication credentials.", extra={'user': 'Anonymous'})
        return Response({'error': "You must provide valid authentication credentials."},
                        status=status.HTTP_401_UNAUTHORIZED)

    if user.is_a_teacher is False:
        logger.error("Only teachers can update questions.", extra={'user': user.id})
        return Response({"error": "Only teachers can update questions."}, status.HTTP_403_FORBIDDEN)

    try:
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error("Assessment Not Found.", extra={'user': user.id})
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        with transaction.atomic():
            # Retrieve the existing question
            question = Question.objects.get(pk=question_id, assessment=assessment)

            # Check the structure of the assessment to determine the serializer to use
            if assessment.structure == "mcq":
                serializer_class = QuestionSerializer
                choices_serializer_class = ChoiceSerializer
            elif assessment.structure == "text":
                serializer_class = TextQuestionSerializer
                choices_serializer_class = None
            else:
                # Handle other assessment structures if needed
                logger.error("Unsupported assessment structure.", extra={'user': user.id})
                return Response({'error': 'Unsupported assessment structure'}, status=status.HTTP_400_BAD_REQUEST)

            # Create a serializer instance based on the assessment structure
            question_serializer = serializer_class(data=request.data, instance=question, partial=True)
            print(question_serializer)
            if question_serializer.is_valid(raise_exception=True):
                # Encrypt the updated question text if applicable
                if assessment.structure == "text" and 'text' in request.data:
                    encrypted_question_text = encrypt_string(request.data['text'])
                    question_serializer.validated_data['text'] = encrypted_question_text

                    # Save the updated question
                    updated_question = question_serializer.save()
                
                
                # Handle updating choices for MCQ questions
                if assessment.structure == "mcq":
                    question_data = request.data.get('question', {})
                    choices_data = request.data.get('choices', [])
                    
                    # Encrypt question text
                    encrypted_question_text = encrypt_string(question_data.get('text', ''))
                    question_serializer.validated_data['text'] = encrypted_question_text
                    question_serializer.save()
                    
                    if 'choices' in request.data:
                        choices_data = request.data['choices']

                        # Delete choices not updated or created
                        updated_choice_ids = set(choice_data.get('id') for choice_data in choices_data if 'id' in choice_data)
                        question.choices.exclude(pk__in=updated_choice_ids).delete()
                        
                        # Iterate through choices and update/create them
                        for choice_data in choices_data:
                            choice_id = choice_data.get('id')
                            if choice_id:
                                # Update existing choice
                                choice = Choice.objects.get(pk=choice_id, question=question)
                                choice_serializer = ChoiceSerializer(data=choice_data, instance=choice)
                            else:
                                # Create new choice
                                choice_data['question_id'] = question.id
                                choice_serializer = ChoiceSerializer(data=choice_data)
                                print(choice_serializer)

                            if choice_serializer.is_valid(raise_exception=True):
                                # Encrypt the updated choice text if applicable
                                if 'text' in choice_data:
                                    encrypted_choice_text = encrypt_string(choice_data['text'])
                                    choice_serializer.validated_data['text'] = encrypted_choice_text
                                    choice_serializer.validated_data['question_id'] = question.id
                                    

                                choice_serializer.save()

                logger.info("Question updated successfully.", extra={'user': user.id})
                return Response({'message': 'Question updated successfully'},
                                status=status.HTTP_200_OK)

            logger.error(str(question_serializer.errors), extra={'user': user.id})
            return Response({'error': question_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        # Rollback transaction and raise validation error
        transaction.rollback()
        logger.error(str(e), extra={'user': None})
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@transaction.atomic
def get_assessment_details(request, assessment_id):
    user = request.user

    is_student = request.user.is_a_student
    is_instructor = request.user.is_a_teacher
    if not user.is_authenticated:
        logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
        return Response(
            {'error': "You must provide valid authentication credentials."},
            status=status.HTTP_401_UNAUTHORIZED )

    if user.is_a_teacher is False and user.is_a_student is False:
        logger.warning(
            "You do not have the necessary rights! (Not a lecturer nor student)",
            extra={ 'user': request.user.id } )
        return Response(
            {"error": "You do not have the necessary rights (Not a lecturer nor student)"},
            status.HTTP_403_FORBIDDEN
        )
   
    try:
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error(  "Assessment not Found.", extra={ 'user': user.id } )
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    if is_instructor:
        tutor = Teacher.objects.get(user=user)

        if assessment.course not in tutor.courses.all():
            # if user not in assessment.course.instructors.all():
            logger.warning( "You are not a lecturer of this course",
                extra={ 'user': request.user.id } )
            return Response( {"error": "You are not a lecturer of this course."},
                status.HTTP_403_FORBIDDEN )
        
    if is_student:
        try:
            student = Student.objects.get(user=user)
        except Student.DoesNotExist:
            logger.error(
                "Student not Found.",
                extra={
                    'user': user.id
                }
            )
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        if assessment.course not in student.registered_courses.all():
            logger.error(
                "Student not registed for this course.",
                extra={
                    'user': user.id
                }
            )
            return Response({'error': 'Student is not registered for this course'}, status=status.HTTP_400_BAD_REQUEST)

    assessment_serializer = AssessmentSerializer(assessment)
    questions = Question.objects.filter(assessment=assessment)
    question_serializer = QuestionSerializer(questions, many=True)
    structural_question_serializer = TextQuestionSerializer(questions, many=True)
    
    
    if assessment.structure == "mcq":
        # Retrieve only questions and choices without correct responses
        question_data = question_serializer.data
        print("mcq")
        for question in question_data:
            choices = Choice.objects.filter(question=question['id'])
            choice_serializer = SimplifiedChoiceSerializer(choices, many=True)
            # question['choices'] = choice_serializer.data
            decrypted_choices = []

            for choice in choice_serializer.data:
                # Assuming 'text' is the encrypted field, decrypt it
                decrypted_choice_text = decrypt_string(choice['text'])
                choice['text'] = decrypted_choice_text
                decrypted_choices.append(choice)

            question['choices'] = decrypted_choices

            # Decrypt question text
            decrypted_question_text = decrypt_string(question['text'])
            question['text'] = decrypted_question_text
        
    elif assessment.structure == "text":
        # Retrieve only questions
        question_data = structural_question_serializer.data
        print("structural")
    
        for question in question_data:

            # Decrypt question text
            decrypted_question_text = decrypt_string(question['text'])
            question['text'] = decrypted_question_text
        
    # You can customize the structure of the response based on your needs
    response_data = {
        'assessment_details': assessment_serializer.data,
        'questions': question_data,
        # Add other relevant information if needed
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
def list_assessments(request):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
        return Response(
            {'error': "You must provide valid authentication credentials."},
            status=status.HTTP_401_UNAUTHORIZED )
        
    if user.is_a_teacher is False and user.is_a_student is False:
        logger.warning(
            "You do not have the necessary rights! (Not a lecturer nor student)",
            extra={
                'user': request.user.id
            }
        )
        return Response(
            {"error": "You do not have the necessary rights (Not a lecturer nor student)"},
            status.HTTP_403_FORBIDDEN
        )
    if user.is_a_teacher:
        assessments = Assessment.objects.filter(instructor=user)
        serializer = AssessmentSerializer(assessments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif user.is_a_student:
        try:
            student = Student.objects.get(user=user)
        # except Student.DoesNotExist:
            
            registered_courses = student.registered_courses.all()
            assessments = Assessment.objects.filter(course__in=registered_courses)
            serializer = AssessmentSerializer(assessments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
       
        except Student.DoesNotExist:
            logger.error(
                "Student not Found.",
                extra={ 'user': user.id })
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
    
    else:
        logger.error(
            "You do not have the necessary rights",
            extra={ 'user': user.id })
        return Response({'error': 'You do not have the necessary rights.'}, status=status.HTTP_403_FORBIDDEN)
       

@api_view(['POST'])
@transaction.atomic
def submit_assessment_responses(request, assessment_id):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

    if user.is_a_student is False:
        logger.error( "Only students can register courses.", extra={ 'user': request.user.id } )
        return Response( {
                "error": "Only students can register courses."
            },
            status.HTTP_403_FORBIDDEN )
    
    try:
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error( "Assessment not found.", extra={ 'user': user.id } )
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)
    try:
        with transaction.atomic():
            # Check if responses already exist for the assessment by the student
            existing_responses = StudentResponse.objects.filter(student=user, assessment=assessment)
            if existing_responses.exists():
                logger.error( "Responses for this assessment already submitted.", extra={  'user': user.id } )
                return Response({'error': 'Responses for this assessment already submitted'}, status=status.HTTP_400_BAD_REQUEST)

            responses_data = request.data.get('responses', [])

            total_score = 0

            # Assuming the 'responses' data is a list of dictionaries with question_id and selected_choice_id
            for response_data in responses_data:
                question_id = response_data.get('question_id')
                selected_choice_id = response_data.get('selected_choice_id')

                try:
                    question = Question.objects.get(pk=question_id)
                    selected_choice = Choice.objects.get(pk=selected_choice_id)

                    # Check if the selected choice is a valid choice for the given question
                    if selected_choice.question != question:
                        logger.error("Selected choice is not valid for the given question.", extra={'user': user.id})
                        return Response({'error': 'Selected choice is not valid for the given question'}, status=status.HTTP_400_BAD_REQUEST)

                except Question.DoesNotExist:
                    logger.error( "Invalid Question ID.", extra={ 'user': user.id })
                    return Response({'error': 'Invalid question ID'}, status=status.HTTP_400_BAD_REQUEST)
                except Choice.DoesNotExist:
                    logger.error( "Invalid Choice ID.", extra={ 'user': user.id })
                    return Response({'error': 'Invalid Choice ID'}, status=status.HTTP_400_BAD_REQUEST)

                # Check if the selected choice is correct
                is_correct = selected_choice.is_correct

                # Update the total score
                if is_correct:
                    total_score += 1  

                # Create or update the student response
                response, created = StudentResponse.objects.get_or_create(
                    student=user,
                    assessment=assessment,
                    question=question,
                    defaults={'selected_choice': selected_choice}
                )

                if not created:
                    # Update the selected choice if the response already exists
                    response.selected_choice = selected_choice
                    response.save()

            # Calculate the percentage score
            total_questions = Question.objects.filter(assessment=assessment).count()
            percentage_score = (total_score / total_questions) * 100
            encrypted_score = encrypt_float(percentage_score)

            student_score, created = StudentAssessmentScore.objects.get_or_create(
                student=user,
                assessment=assessment,
                defaults={'score': encrypted_score}
            )

            return Response({'message': 'Responses submitted successfully', 'total_score': f'{percentage_score}%'}, status=status.HTTP_200_OK)

    except Exception as e:
        # Rollback transaction and raise validation error
        transaction.rollback()
        logger.error(
            str(e),
            extra={
                'user': None
            }
        )
        return Response(
            {"error": str(e)},
            status=status.HTTP_412_PRECONDITION_FAILED)


@api_view(['POST'])
@transaction.atomic
def submit_structural_responses(request, assessment_id):
    user = request.user

    if not user.is_authenticated:
        logger.error("You do not have the necessary rights.", extra={'user': 'Anonymous'})
        return Response({'error': "You must provide valid authentication credentials."},
                        status=status.HTTP_401_UNAUTHORIZED)

    if user.is_a_student is False:
        logger.error("Only students can submit responses.", extra={'user': user.id})
        return Response({"error": "Only students can submit responses."},
                        status.HTTP_403_FORBIDDEN)

    try:
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error("Assessment not found.", extra={'user': user.id})
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        with transaction.atomic():
            # Check if responses already exist for the assessment by the student
            existing_responses = StudentResponse.objects.filter(student=user, assessment=assessment)
            if existing_responses.exists():
                logger.error("Responses for this assessment already submitted.", extra={'user': user.id})
                return Response({'error': 'Responses for this assessment already submitted'},
                                status=status.HTTP_400_BAD_REQUEST)

            responses_data = request.data.get('responses', [])

            for response_data in responses_data:
                question_id = response_data.get('question_id')
                text_response = response_data.get('text_response')

                try:
                    question = Question.objects.get(pk=question_id)

                    # Check if the question is a structural question
                    if question.assessment.structure != "text":
                        logger.error("Invalid question type for structural responses.", extra={'user': user.id})
                        return Response({'error': 'Invalid question type for structural responses'},
                                        status=status.HTTP_400_BAD_REQUEST)

                except Question.DoesNotExist:
                    logger.error("Invalid Question ID.", extra={'user': user.id})
                    return Response({'error': 'Invalid question ID'}, status=status.HTTP_400_BAD_REQUEST)

                # Create or update the student response for structural questions
                response, created = StudentResponse.objects.get_or_create(
                    student=user,
                    assessment=assessment,
                    question=question,
                    defaults={'text_response': text_response}
                )

                if not created:
                    # Update the text response if the response already exists
                    response.text_response = text_response
                    response.save()

            return Response({'message': 'Structural responses submitted successfully'},
                            status=status.HTTP_200_OK)

    except Exception as e:
        # Rollback transaction and raise validation error
        transaction.rollback()
        logger.error(str(e), extra={'user': None})
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def get_assessment_submissions(request, assessment_id):
    user = request.user
    
    if not user.is_authenticated:
        logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
    
    try:
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error( "Assessment not found.", extra={ 'user': request.user.id } )
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the requesting user is the tutor who created the assessment
    if user.is_a_teacher is True:
        teacher = Teacher.objects.get(user=user)
        course = assessment.course
        if course not in teacher.courses.all():
            logger.error( "You are not assigned to this course.", extra={ 'user': user.id } )
            return Response({'error': 'You are not assigned to this course.'}, status=status.HTTP_403_FORBIDDEN)
    else:
        logger.error( "You do not have permission to view responses for this assessment.", extra={ 'user': request.user.id } )
        return Response({'error': 'You do not have permission to view responses for this assessment'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get all student responses for the assessment
    responses = StudentResponse.objects.filter(assessment=assessment)
    
    response_serializer = StudentResponseSerializer(responses, many=True)
    print(response_serializer.instance)
        
    # Serialize the data only if it's a StudentResponse instance
    logger.info( "Asessment submissions returned successfully.", extra={ 'user': user.id } )
    return Response({'responses': response_serializer.data}, status=status.HTTP_200_OK)
    


@api_view(['GET']) 
def get_assessment_results(request, assessment_id):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You do not have the necessary rights.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
    
    if user.is_a_student is False and user.is_a_teacher is False:
        logger.error( "You do not have access to this endpoint.", extra={ 'user': request.user.id } )
        return Response(  { "error": "You do not have access to this endpoint."}, status.HTTP_403_FORBIDDEN )

    try:
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error( "Assessment not found.", extra={ 'user': user.id } )
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    if user.is_a_student is True:
        try:
            assessment_results = StudentStructuralScore.objects.filter(assessment_id=assessment_id, student=request.user)
            serializer = StudentStructuralScoreSerializer(assessment_results, many=True)
            
            logger.info( "Score returned successfully.", extra={ 'user': user.id } )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StudentAssessmentScore.DoesNotExist:
            logger.error( "Accessment results not found.", extra={ 'user': user.id } )
            return Response({'error': 'Assessment results not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if teacher is assigned to course
    if user.is_a_teacher is True:
        try:
            teacher = Teacher.objects.get(user=user)
            assessment_results = StudentAssessmentScore.objects.filter(assessment_id=assessment_id)
            course = assessment.course
            if course not in teacher.courses.all():
                logger.error( "You are not assigned to this course.", extra={ 'user': user.id } )
                return Response({'error': 'You are not assigned to this course.'}, status=status.HTTP_403_FORBIDDEN)

            serializer = StudentStructuralScoreSerializer(assessment_results, many=True)
            
            logger.info( "Score returned successfully.", extra={ 'user': user.id } )
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except StudentAssessmentScore.DoesNotExist:
            logger.error( "Assessment results not found.", extra={ 'user': user.id } )
            return Response({'error': 'Assessment results not found'}, status=status.HTTP_404_NOT_FOUND)



@api_view(['POST'])
def record_student_score(request, assessment_id, student_id):
    user = request.user
    
    if not user.is_authenticated:
        logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
        return Response( {'error': "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )
    
    try:
        assessment = Assessment.objects.get(pk=assessment_id)
    except Assessment.DoesNotExist:
        logger.error( "Assessment not found.", extra={ 'user': request.user.id } )
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the requesting user is the tutor who created the assessment
    if assessment.instructor != user:
        logger.error( "You do not have permission to record scores for this assessment.", extra={ 'user': request.user.id } )
        return Response({'error': 'You do not have permission to record scores for this assessment'}, status=status.HTTP_403_FORBIDDEN)
    
    # Check if the student is registered for the course
    try:
        student = Student.objects.get(user=student_id, registered_courses=assessment.course)
    except Student.DoesNotExist:
        logger.error('Student is not registered for the course associated with this assessment.', extra={ 'user': request.user.id } )
        return Response({'error': 'Student is not registered for the course associated with this assessment.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        scores_data = request.data.get('scores', [])

        if not scores_data:
            logger.error( "Please provide a non-empty array of scores in the request data.", extra={ 'user': request.user.id } )
            return Response({'error': 'Please provide a non-empty array of scores in the request data.'}, status=status.HTTP_400_BAD_REQUEST)
        
        recorded_scores = []

        for score_data in scores_data:
            question_id = score_data.get('question_id')
            score = score_data.get('score')

            if question_id is None or score is None:
                logger.error( "Each score in the array should have both question_id and score.", extra={ 'user': request.user.id } )
                return Response({'error': 'Each score in the array should have both question_id and score.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                question = Question.objects.get(pk=question_id)
            except Question.DoesNotExist:
                logger.error( f'Question with ID {question_id} not found.', extra={ 'user': request.user.id } )
                return Response({'error': f'Question with ID {question_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Check that the score is not greater than the mark allocated for the question
            if question.mark_allocated is not None:
                if score > int(question.mark_allocated):
                    logger.error( f'Score for Question {question_id} cannot exceed the mark allocated.', extra={ 'user': request.user.id } )
                    return Response({'error': f'Score for Question {question_id} cannot exceed the mark allocated.'}, status=status.HTTP_400_BAD_REQUEST)

            else:
                logger.error( f'No mark was allocated for {question_id}.', extra={ 'user': request.user.id } )
                return Response({'error': f'No mark was allocated for {question_id}.'}, status=status.HTTP_400_BAD_REQUEST)


            assessment_score, created = StudentStructuralScore.objects.get_or_create(
                assessment_id=assessment_id,
                student_id=student_id,
                question=question,
                defaults={'score': score, 'is_graded': True}
            )
            
            # If a score object already exists, update the score
            if not created:
                assessment_score.score = score
                assessment_score.is_graded = True
                assessment_score.save()
                
            # Add the recorded score to the list
            recorded_scores.append(StudentStructuralScoreSerializer(assessment_score).data)
            
        # Return the array of recorded scores
        logger.info( "Assessment Score recorded successfully.", extra={ 'user': user.id } )
        return Response({'recorded_scores': recorded_scores}, status=status.HTTP_201_CREATED)
    except ValidationError as ve:
        logger.error(ve.detail, extra={ 'user': request.user.id } )
        return Response({'error': ve.detail}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error( str(e), extra={ 'user': request.user.id } )
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def get_student_assessment_grade(request, assessment_id, student_id):
    user = request.user

    if not user.is_authenticated:
        logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
        return Response({'error': 'You must provide valid authentication credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        assessment = Assessment.objects.get(pk=assessment_id)
        # Check if the student is registered for the course
        student = get_object_or_404(Student, user=student_id, registered_courses=assessment.course)

        if user.is_a_teacher is True:
            teacher = Teacher.objects.get(user=user)
            course = assessment.course
            if course not in teacher.courses.all():
                logger.error( "You are not assigned to this course.", extra={ 'user': user.id } )
                return Response({'error': 'You are not assigned to this course.'}, status=status.HTTP_403_FORBIDDEN)

            
        # Check if the requesting user is the tutor who created the assessment
        if user.is_a_student:
            if student.user != user:
                logger.error( "You do not have permission to view grade for this assessment.", extra={ 'user': request.user.id } )
                return Response({'error': 'You do not have permission to view grade for this assessment'}, status=status.HTTP_403_FORBIDDEN)
        
        # Check if the student has an existing score for this assessment
        student_a_score_exists = StudentAssessmentScore.objects.filter(assessment=assessment, student=student.user).exists()

        student_s_score_exists = StudentStructuralScore.objects.filter(assessment=assessment, student=student.user).exists()


        if not student_a_score_exists and student_s_score_exists:
            # Calculate the assessment score from StudentStructuralScore and save it to StudentAssessmentScore
            total_score = StudentStructuralScore.objects.filter(assessment=assessment, student=student.user).aggregate(total_score=Sum('score'))['total_score'] or 0
            # Create or update the score in StudentAssessmentScore
            student_assessment_score, created = StudentAssessmentScore.objects.update_or_create(
                assessment=assessment,
                student=student.user,
                defaults={'score': total_score}
            )
            # Log the event
            if created:
                logger.info(f"Student assessment score created for user {user.id} and assessment {assessment_id}.")
            else:
                logger.info(f"Student assessment score updated for user {user.id} and assessment {assessment_id}.")

        
        student_scores = StudentAssessmentScore.objects.filter(assessment=assessment, student_id=student_id)
        print(student_scores) 
        
        # Calculate the total score for the student in this assessment
        total_score = student_scores.aggregate(total_score=Sum('score'))['total_score']
        print(total_score)
        
        if total_score is None:
            logger.error("Student score not found for this assessment", extra={'user': user.id})
            return Response({'error': 'Student score not found for this assessment'}, status=status.HTTP_404_NOT_FOUND)

        
        # Calculate the total mark allocation for all questions in this assessment
        total_mark_allocation = Question.objects.filter(assessment=assessment).aggregate(total_mark_allocation=Sum('mark_allocated'))['total_mark_allocation']
        print(total_mark_allocation)

        # Calculate the percentage score
        percentage_score = (total_score / total_mark_allocation) * 100 if total_mark_allocation != 0 else 0
        print(percentage_score)

        # Determine the grade based on your grading system
        grade = calculate_grade(percentage_score)

        return Response({'total_score': total_score, 'percentage_score': percentage_score, 'grade': grade}, status=status.HTTP_200_OK)

    except Assessment.DoesNotExist:
        logger.error('Assessment not found', extra={ 'user': user.id })
        return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

    except StudentAssessmentScore.DoesNotExist:
        logger.error('Student score not found for this assessment', extra={ 'user': user.id })
        return Response({'error': 'Student score not found for this assessment'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error( str(e), extra={ 'user': user.id })
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def calculate_grade(percentage_score):
    # Grading logic 
    if percentage_score >= 80:
        return 'A'
    elif 70 <= percentage_score < 80:
        return 'B+'
    elif 60 <= percentage_score < 70:
        return 'B'
    elif 56 <= percentage_score < 60:
        return 'C+'
    elif 50 <= percentage_score < 56:
        return 'C'
    elif 46 <= percentage_score < 50:
        return 'D+'
    elif 40 <= percentage_score < 46:
        return 'D'
    else:
        return 'F'



class GradeSystemViewSet(viewsets.ModelViewSet):

    queryset = GradeSystem.objects.all()
    serializer_class = GradeSystemSerializer


    def list(self, request, *args, **kwargs):
        
        user = self.request.user

        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        logger.info( "Grade System returned successfully.", extra={ 'user': user.id } )

        return Response(serializer.data)


    def retrieve(self, request, *args, **kwargs):
        
        user = self.request.user
        
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        if user.is_admin is False:
            logger.error( "You do not have the necessary rights/Not an Admin.", extra={ 'user': user.id } )
            return Response({ "error": "You do not have the necessary rights/Not an Admin."}, status.HTTP_403_FORBIDDEN )
        
        instance = GradeSystem.objects.get(id=kwargs['pk'])
        serializer = self.get_serializer(instance)
        logger.info( "Grade details returned successfully!", extra={ 'user': request.user.id } )

        return Response(serializer.data)


    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        if user.is_admin is False:
            logger.error( "You do not have the necessary rights/Not an Admin.", extra={ 'user': user.id } )
            return Response({ "error": "You do not have the necessary rights/Not an Admin."}, status.HTTP_403_FORBIDDEN )
        
        try:
            with transaction.atomic():
                print("1")
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                
                logger.info( "Grading system recorded successfully!", extra={ 'user': user.id  } )
                return Response( serializer.data, status.HTTP_201_CREATED, headers=headers)
    
        except Exception as e:
            # Rollback transaction and raise validation error
            transaction.rollback()
            logger.error( str(e), extra={ 'user': None } )
            return Response( {"error": str(e)}, status=status.HTTP_412_PRECONDITION_FAILED)


    def update(self, request, *args, **kwargs):

        user = self.request.user

        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        if user.is_admin is False:
            logger.error( "You do not have the necessary rights/Not an Admin.", extra={ 'user': user.id } )
            return Response({ "error": "You do not have the necessary rights/Not an Admin."}, status.HTTP_403_FORBIDDEN )

        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            print(instance)
            serializer = self.get_serializer( instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}

            logger.info( "Grade details Modified successfully!", extra={ 'user': user.id } )
            return Response(serializer.data)

        except Exception as e:
            logger.error( str(e), extra={ 'user': user.id } )
            return Response( {'message': str(e)}, status=status.HTTP_412_PRECONDITION_FAILED)
            
        
    def perform_update(self, serializer):
        
        return serializer.save()


    def destroy(self, request, *args, **kwargs):
        
        logger.warning( "Method not allowed", extra={ 'user': "Anonymous" })
        return Response( {"error": "Method not allowed"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET']) 
def calculate_student_grade(request, course_id):
    try:
        user = request.user
        
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': request.user.id } )
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED )

        # Retrieve the course
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            logger.error( "Course Not Found.", extra={ 'user': request.user.id } )
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the authenticated user is a student and is registered for the course
        try:
            student = Student.objects.get(user=request.user, is_deleted=False)
            if course not in student.registered_courses.all():
                logger.error( "You are not registered for this course.", extra={ 'user': request.user.id } )
                return Response({'error': 'You are not registered for this course'}, status=status.HTTP_403_FORBIDDEN)
        
        except Student.DoesNotExist:
            logger.error( "You are not registered as a student.", extra={ 'user': request.user.id } )
            return Response({'error': 'You are not registered as a student'}, status=status.HTTP_403_FORBIDDEN)

        # Get all assessments for the given course
        assessments = Assessment.objects.filter(course=course)
        print(assessments)

        # Retrieve all student's assessments score for the given course
        assessment_scores = StudentAssessmentScore.objects.filter(student_id=user.id, assessment__course_id=course_id)
        print(assessment_scores)

        # Check if there are assessments
        if not assessments.exists():
            logger.error( "No assessments found for the student in this course.", extra={ 'user': request.user.id } )
            return Response({"error": "No assessments found for the student in this course."}, status=status.HTTP_404_NOT_FOUND)

        # Calculate the average score
        # average_score = student_scores.aggregate(Avg('score'))['score__avg']
        total_score = sum(decrypt_float(assessment.score) for assessment in assessment_scores)
        average_score = total_score / len(assessments)

        # Retrieve the corresponding grade based on the average score
        grade = get_grade_for_score(average_score)

        response_data = {
            "student": user.first_name + " " + user.last_name,
            "course_id": course.course_title,
            "average_score": average_score,
            "grade": grade,
        }

        logger.info( "Student Course Grade info returned successfully .", extra={ 'user': request.user.id } )
        return Response(response_data, status=status.HTTP_200_OK)

    except Course.DoesNotExist:
        logger.error( "Course not found.", extra={ 'user': request.user.id } )
        return Response({'error': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)


def get_grade_for_score(score):
    # Get the grade based on the given score
    try:
        grade_system = GradeSystem.objects.get(min_score__lte=score, max_score__gte=score)
        return grade_system.grade
    except GradeSystem.DoesNotExist:
        return 'Unknown'


@api_view(['GET'])
def get_all_students_scores(request, course_id):
    try:
        user = request.user
        
        #Check if user is authenticated
        if not user.is_authenticated:
            logger.error( "You must provide valid authentication credentials.", extra={ 'user': 'Anonymous' })
            return Response( {"error": "You must provide valid authentication credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        #Check if user is admin or lecturer
        if user.is_admin is False and user.is_a_teacher is False:
            logger.error( "You do not have access to this endpoint.", extra={ 'user': user.id })
            return Response(  { "error": "You do not have access to this endpoint."}, status.HTTP_403_FORBIDDEN )

        # Retrieve the course
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            logger.error( "Course Not Found.", extra={ 'user': request.user.id } )
            return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if teacher is assigned to course
        if user.is_a_teacher is True:
            tutor = Teacher.objects.get(user=user)
            
            if course not in tutor.courses.all():
            # if user not in course.instructors.all(): 
                logger.error( "You do not have access to this endpoint.", extra={ 'user': request.user.id })
                return Response({'error': 'You are not assigned to this course.'}, status=status.HTTP_403_FORBIDDEN)

        # Get all assessments for the given course
        assessments = Assessment.objects.filter(course=course)
        print(assessments)
        
        # Get all students registered for the course
        students = Student.objects.filter(registered_courses=course)
        print(students)

        # Create a list to store each student's information
        students_data = []

        # Check if the student has an existing score for this assessment
        # student_a_score_exists = StudentAssessmentScore.objects.filter(assessment=assessment, student=student.user).exists()

        # student_s_score_exists = StudentStructuralScore.objects.filter(assessment=assessment, student=student.user).exists()

        # if not student_a_score_exists and student_s_score_exists:
        #     # Calculate the assessment score from StudentStructuralScore and save it to StudentAssessmentScore
        #     total_score = StudentStructuralScore.objects.filter(assessment=assessment, student=student.user).aggregate(total_score=Sum('score'))['total_score'] or 0
        #     # Create or update the score in StudentAssessmentScore
        #     student_assessment_score, created = StudentAssessmentScore.objects.update_or_create(
        #         assessment=assessment,
        #         student=student.user,
        #         defaults={'score': total_score}
        #     )
        #     # Log the event
        #     if created:
        #         logger.info(f"Student assessment score created for user {user.id} and assessment {assessment}.")
        #     else:
        #         logger.info(f"Student assessment score updated for user {user.id} and assessment {assessment}.")


        # Iterate through each student and retrieve their scores
        for student in students:
            student_data = {
                "student_reference": student.student_id,
                "student_name": f"{student.user.first_name} {student.user.last_name}",
                "average_score": None,  # Initializing the average score field
                "grade": None,  # Initializing the grade field
                "assessment_scores": []
            }

            # Retrieve all student's assessments score for the given course
            assessment_scores = StudentAssessmentScore.objects.filter(student_id=student.user.id, assessment__course_id=course_id)
            print(assessment_scores)

            # Retrieve the student's scores for each assessment in the course
            for assessment in course.assessment_set.all():
                try:
                    score = StudentAssessmentScore.objects.get(student=student.user, assessment=assessment)
                    # print(type(score.score))
                    # print(score.score)
                    # Decrypt the score before adding it to the list
                    # decrypted_score = decrypt_float(score.score)
                    student_data["assessment_scores"].append({
                        "assessment_title": assessment.title,
                        "score": score.score
                        # "score": decrypted_score
                    })
                except StudentAssessmentScore.DoesNotExist:
                    # Handle the case where the student has no score for the assessment
                    student_data["assessment_scores"].append({
                        "assessment_title": assessment.title,
                        "score": None
                    })
                    
                    if not StudentStructuralScore.objects.filter(assessment=assessment, student=student.user).exists():
                        continue

                    total_score = StudentStructuralScore.objects.filter(assessment=assessment, student=student.user).aggregate(total_score=Sum('score'))['total_score'] or 0
                    student_assessment_score, _ = StudentAssessmentScore.objects.update_or_create(
                        assessment=assessment,
                        student=student.user,
                        defaults={'score': total_score}
                    )

            # Calculate and append the student's avewrage score and grade
            total_score_sum = sum(int(score.score) for score in assessment_scores)
            # total_score = sum(decrypt_float(assessment.score) for assessment in assessment_scores)
            print(total_score_sum)

            average_score = total_score_sum / len(assessments) if assessments else 0
            print(average_score)
            student_data["average_score"] = average_score
            student_data["grade"] = get_grade_for_score(average_score)            

            students_data.append(student_data)

        response_data = {
            "course_id": course.course_title,
            "students": students_data
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Course.DoesNotExist:
        logger.error( "Cpourse not found.", extra={ 'user': user.id })
        return Response({'error': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)



# @api_view(['GET'])
# def get_all_students_assessment_grades(request, assessment_id):
#     user = request.user

#     if not user.is_authenticated:
#         logger.error("You must provide valid authentication credentials.", extra={'user': 'Anonymous'})
#         return Response({'error': 'You must provide valid authentication credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
    
#     #Check if user is admin or lecturer
#     if user.is_admin is False and user.is_a_teacher is False:
#         logger.error( "You do not have access to this endpoint.", extra={ 'user': user.id })
#         return Response(  { "error": "You do not have access to this endpoint."}, status.HTTP_403_FORBIDDEN )

#     try:
#         assessment = Assessment.objects.get(pk=assessment_id)

#         if user.is_a_teacher:
#             teacher = Teacher.objects.get(user=user)
#             course = assessment.course
#             if course not in teacher.courses.all():
#                 logger.error("You are not assigned to this course.", extra={'user': user.id})
#                 return Response({'error': 'You are not assigned to this course.'}, status=status.HTTP_403_FORBIDDEN)

#         # Retrieve all students enrolled in the course related to the assessment
#         enrolled_students = Student.objects.filter(registered_courses=assessment.course)

#         student_grades = []
#         for student in enrolled_students:
#             student_scores = StudentAssessmentScore.objects.filter(assessment=assessment, student=student)

#             # Calculate the total score for the student in this assessment
#             total_score = student_scores.aggregate(total_score=Sum('score'))['total_score']
#             if total_score is None:
#                 logger.error(f"Student score not found for assessment {assessment_id} for student {student.id}", extra={'user': user.id})
#                 continue

#             # Calculate the total mark allocation for all questions in this assessment
#             total_mark_allocation = Question.objects.filter(assessment=assessment).aggregate(total_mark_allocation=Sum('mark_allocated'))['total_mark_allocation']

#             # Calculate the percentage score
#             percentage_score = (total_score / total_mark_allocation) * 100 if total_mark_allocation != 0 else 0

#             # Determine the grade based on your grading system
#             grade = calculate_grade(percentage_score)

#             # Append the student's grade to the list
#             student_grades.append({
#                 'student_id': student.id,
#                 'total_score': total_score,
#                 'percentage_score': percentage_score,
#                 'grade': grade
#             })

#         return Response(student_grades, status=status.HTTP_200_OK)

#     except Assessment.DoesNotExist:
#         logger.error('Assessment not found', extra={'user': user.id})
#         return Response({'error': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

#     except Exception as e:
#         logger.error(str(e), extra={'user': user.id})
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def list_ca_assessment_results(request, type, *args, **kwargs):
    user = request.user

    if not user.is_authenticated:
        logger.error("You must provide valid authentication credentials.", extra={'user': 'Anonymous'})
        return Response({"error": "You must provide valid authentication credentials."},
                        status=status.HTTP_401_UNAUTHORIZED)

    try:
        student = Student.objects.get(user=user, is_deleted=False)
    except Student.DoesNotExist:
        logger.error("You are not registered as a student.", extra={'user': user.id})
        return Response({'error': 'You are not registered as a student'}, status=status.HTTP_403_FORBIDDEN)

    assessment_results = StudentAssessmentScore.objects.filter(student=student.user,
                                                                assessment__assessment_type=type)

    serializer = StudentStructuralScoreSerializer(assessment_results, many=True)

    logger.info("CA Assessment results returned successfully.", extra={'user': user.id})
    return Response(serializer.data, status=status.HTTP_200_OK)



