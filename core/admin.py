from django.contrib import admin
from .models import (
    StudentProfile, ChatHistory, Feedback, KnowledgeBase,
    AdminProfile, UnsolvedQuestion, Document, Analytics
)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'roll_no', 'email', 'course', 'year', 'phone', 'created_at']
    list_filter = ['course', 'year', 'created_at']
    search_fields = ['full_name', 'roll_no', 'email', 'phone']

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'department', 'created_at']
    list_filter = ['department', 'created_at']
    search_fields = ['full_name', 'email']

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['question', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'sender', 'intent', 'timestamp', 'is_saved']
    list_filter = ['sender', 'intent', 'is_saved', 'timestamp']
    search_fields = ['message', 'response', 'user__username']
    readonly_fields = ['timestamp']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['chat_history', 'user', 'rating', 'timestamp']
    list_filter = ['rating', 'timestamp']
    search_fields = ['comment', 'user__username']

@admin.register(UnsolvedQuestion)
class UnsolvedQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'user', 'status', 'resolved_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['question', 'resolved_answer']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'uploaded_by', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['title', 'description', 'extracted_text']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_questions', 'total_users', 'kb_matches', 'ai_fallbacks']
    list_filter = ['date']
    readonly_fields = ['created_at']

