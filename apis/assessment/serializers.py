import logging
import binascii
import cryptography
from .models import *
from django.conf import settings
from cryptography.fernet import Fernet
from rest_framework import serializers
from cryptography.fernet import InvalidToken
from apis.users.serializers import UserSerializer


logger = logging.getLogger("myLogger")


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text', 'is_correct']


class SimplifiedChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'text']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    assessment = serializers.PrimaryKeyRelatedField(
        #queryset=Assessment.objects.all(), #.filter(is_deleted=False),
        allow_null=True,
        allow_empty=True,
        required=False,
        read_only=True
    )

    class Meta:
        model = Question
        fields = ['id', 'assessment', 'text', 'mark_allocated', 'image', 'created_at', 'choices']


class TextQuestionSerializer(serializers.ModelSerializer):
    assessment = serializers.PrimaryKeyRelatedField(
        #queryset=Assessment.objects.all(), #.filter(is_deleted=False),
        allow_null=True,
        allow_empty=True,
        required=False,
        read_only=True
    )

    class Meta:
        model = Question
        fields = ['id', 'assessment', 'text', 'mark_allocated', 'image', 'created_at']



class AssessmentSerializer(serializers.ModelSerializer):
    # questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Assessment
        fields = ['id', 'title', 'description', 'duration', 'structure', 
                  'assessment_type', 'instructor', 'course', 'created_at']
        read_only_fields = ['instructor']


class StudentResponseSerializer(serializers.ModelSerializer):
    student = UserSerializer()
    assessment = AssessmentSerializer()
    question = QuestionSerializer()
    selected_choice = ChoiceSerializer()
    
    class Meta:
        model = StudentResponse
        fields = ['id', 'student', 'assessment', 'question', 'selected_choice', 'text_response', 'recorded_at']
        # fields = ['id', 'assess']


class StudentAssessmentScoreSerializer(serializers.ModelSerializer):
    # student = UserSerializer(fields=['first_name', 'last_name'])#.data['last_name']
    student_first_name = serializers.ReadOnlyField(source='student.first_name')
    student_last_name = serializers.ReadOnlyField(source='student.last_name')
    score = serializers.SerializerMethodField()

    # def get_score(self, obj):
    #     return f"{obj.score}%"

    def get_score(self, obj):
        # Assuming you have a decrypt_string function for decryption
        score = self.decrypt_float(obj.score)
        print(score)
        return f"{score}%"

    def decrypt_float(self, encrypted_text):
        # Decrypt the string and convert it back to a float
        decrypted_string = self.decrypt_string(encrypted_text)
        return float(decrypted_string)
    
    def decrypt_string(self, encrypted_text):
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

    class Meta:
        model = StudentAssessmentScore 
        fields = ['id', 'score', 'student_first_name', 'student_last_name', 'assessment' ]


class StudentStructuralScoreSerializer(serializers.ModelSerializer):
    student = UserSerializer()#.data['last_name']
    # student_first_name = serializers.ReadOnlyField(source='student.first_name')
    # student_last_name = serializers.ReadOnlyField(source='student.last_name')
    # score = serializers.SerializerMethodField()


    class Meta:
        model = StudentAssessmentScore 
        fields = ['id', 'score', 'student', 'question', 'is_graded', 'assessment']



class GradeSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeSystem
        fields = ['id', 'grade', 'max_score', 'min_score']



