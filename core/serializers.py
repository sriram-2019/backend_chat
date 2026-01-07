from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import (
    StudentProfile, ChatHistory, Feedback, 
    AdminProfile, UnsolvedQuestion, Document, Analytics,
    Rule, Syllabus, ExamInformation, KnowledgeBase
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'full_name', 'roll_no', 'email', 'phone', 'course', 'year', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def to_representation(self, instance):
        # Handle old profiles that might not have full_name or email
        data = super().to_representation(instance)
        if not data.get('full_name'):
            data['full_name'] = instance.user.get_full_name() or instance.user.username
        if not data.get('email'):
            data['email'] = instance.user.email
        return data

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=200)
    roll_no = serializers.CharField(max_length=50)
    phone = serializers.CharField(max_length=15)
    course = serializers.CharField(max_length=100)
    year = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'full_name', 'roll_no', 'phone', 'course', 'year']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        
        if StudentProfile.objects.filter(roll_no=attrs['roll_no']).exists():
            raise serializers.ValidationError({"roll_no": "This roll number is already registered"})
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "This email is already registered"})
        
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        password_confirm = validated_data.pop('password_confirm')
        full_name = validated_data.pop('full_name')
        roll_no = validated_data.pop('roll_no')
        phone = validated_data.pop('phone')
        course = validated_data.pop('course')
        year = validated_data.pop('year')
        email = validated_data['email']
        
        # Create username from email if not provided
        username = validated_data.get('username') or email.split('@')[0]
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create student profile with all fields stored as-is
        StudentProfile.objects.create(
            user=user,
            full_name=full_name,
            roll_no=roll_no,
            email=email,
            phone=phone,
            course=course,
            year=year
        )
        
        return user

class ChatHistorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True, allow_null=True)
    
    class Meta:
        model = ChatHistory
        fields = ['id', 'user_id', 'username', 'message', 'response', 'sender', 'intent', 'timestamp', 'session_id', 'is_saved']
        read_only_fields = ['timestamp']

class ChatHistoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['message', 'response', 'sender', 'session_id']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'chat_history', 'rating', 'comment', 'timestamp']
        read_only_fields = ['timestamp']

class AdminProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AdminProfile
        fields = ['id', 'user', 'full_name', 'email', 'prof_id', 'phone', 'department', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class UnsolvedQuestionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = UnsolvedQuestion
        fields = ['id', 'user', 'user_name', 'question', 'chat_history', 'status', 
                  'resolved_by', 'resolved_by_name', 'resolved_answer', 'resolved_at', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'document_type', 'file_path', 'file_name', 'file_size',
                  'description', 'uploaded_by', 'uploaded_by_name', 'extracted_text',
                  'metadata', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'uploaded_by']

class AnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analytics
        fields = ['id', 'date', 'total_questions', 'total_users', 'kb_matches',
                  'ai_fallbacks', 'helpful_feedback', 'not_helpful_feedback',
                  'unsolved_questions', 'created_at']
        read_only_fields = ['created_at']

class RuleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Rule
        fields = ['id', 'title', 'rule_text', 'applicability', 'status', 'category',
                  'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class SyllabusSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Syllabus
        fields = ['id', 'department', 'course', 'semester', 'subject_code', 'subject_name',
                  'units', 'credits', 'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class ExamInformationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ExamInformation
        fields = ['id', 'exam_name', 'course', 'semester', 'exam_date', 'duration',
                  'instructions', 'venue', 'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class KnowledgeBaseSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = KnowledgeBase
        fields = ['id', 'question', 'answer', 'type', 'approved', 'approved_by', 'approved_by_name',
                  'approved_at', 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'approved_at']
