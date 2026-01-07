from django.db import models
from django.contrib.auth.models import User

class StudentProfile(models.Model):
    COURSE_CHOICES = [
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Electronics', 'Electronics'),
        ('Mechanical', 'Mechanical'),
        ('Civil', 'Civil'),
        ('Electrical', 'Electrical'),
    ]
    
    YEAR_CHOICES = [
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=200, verbose_name='Full Name')
    roll_no = models.CharField(max_length=50, unique=True, verbose_name='Roll Number')
    email = models.EmailField(verbose_name='Email Address')
    phone = models.CharField(max_length=15, verbose_name='Phone Number')
    course = models.CharField(max_length=100, choices=COURSE_CHOICES)
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def __str__(self):
        return f"{self.full_name} - {self.roll_no}"

class KnowledgeBase(models.Model):
    """Knowledge Base for storing Q&A pairs"""
    TYPE_CHOICES = [
        ('rule', 'Rule'),
        ('syllabus', 'Syllabus'),
        ('exam', 'Exam Information'),
        ('faq', 'FAQ'),
        ('general', 'General'),
    ]
    
    question = models.TextField(verbose_name='Question')
    answer = models.TextField(verbose_name='Answer')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general', help_text='Type of knowledge base entry')
    approved = models.BooleanField(default=False, help_text='Whether this entry is approved by admin')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_kb_entries')
    approved_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_kb_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Knowledge Base'
        verbose_name_plural = 'Knowledge Base'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"KB: {self.question[:50]}..."

class ChatHistory(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    INTENT_CHOICES = [
        ('kb_match', 'Knowledge Base Match'),
        ('ai_fallback', 'AI Fallback'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_history', null=True, blank=True)
    message = models.TextField()
    response = models.TextField(blank=True, null=True)
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES, default='user')
    intent = models.CharField(max_length=20, choices=INTENT_CHOICES, blank=True, null=True, help_text='Response intent/source')
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True, null=True, help_text='To group messages in a conversation')
    is_saved = models.BooleanField(default=False, help_text='Whether this answer is saved by user')
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Chat History'
        verbose_name_plural = 'Chat Histories'

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"Chat by {username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class Feedback(models.Model):
    RATING_CHOICES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
    ]
    
    chat_history = models.ForeignKey(ChatHistory, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks', null=True, blank=True)
    rating = models.CharField(max_length=20, choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Feedback for chat {self.chat_history.id}: {self.rating}"

class AdminProfile(models.Model):
    """Admin user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    prof_id = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='Professor ID')
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Admin Profile'
        verbose_name_plural = 'Admin Profiles'
    
    def __str__(self):
        return f"Admin: {self.full_name}"

class UnsolvedQuestion(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('archived', 'Archived'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unsolved_questions', null=True, blank=True)
    question = models.TextField()
    chat_history = models.ForeignKey(ChatHistory, on_delete=models.SET_NULL, null=True, blank=True, related_name='unsolved_question')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_questions')
    resolved_answer = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Unsolved Question'
        verbose_name_plural = 'Unsolved Questions'
    
    def __str__(self):
        return f"Unsolved: {self.question[:50]}..."

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('syllabus', 'Syllabus'),
        ('exam_info', 'Exam Information'),
        ('rules', 'Rules & Regulations'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file_path = models.CharField(max_length=500, help_text='Path to uploaded file')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text='File size in bytes', default=0)
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')
    extracted_text = models.TextField(blank=True, null=True, help_text='Text extracted from document for chatbot')
    metadata = models.JSONField(default=dict, blank=True, help_text='Additional metadata')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
    
    def __str__(self):
        return f"{self.title} ({self.document_type})"

class Analytics(models.Model):
    """Store analytics data"""
    date = models.DateField()
    total_questions = models.IntegerField(default=0)
    total_users = models.IntegerField(default=0)
    kb_matches = models.IntegerField(default=0)
    ai_fallbacks = models.IntegerField(default=0)
    helpful_feedback = models.IntegerField(default=0)
    not_helpful_feedback = models.IntegerField(default=0)
    unsolved_questions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date']
        verbose_name = 'Analytics'
        verbose_name_plural = 'Analytics'
    
    def __str__(self):
        return f"Analytics for {self.date}"

class Rule(models.Model):
    """Rules & Regulations"""
    APPLICABILITY_CHOICES = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('All', 'All Students'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    title = models.CharField(max_length=200)
    rule_text = models.TextField(verbose_name='Rule Content')
    applicability = models.CharField(max_length=10, choices=APPLICABILITY_CHOICES, default='All')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    category = models.CharField(max_length=100, blank=True, null=True, help_text='Rule category (e.g., Attendance, Discipline)')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_rules')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_rules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Rule'
        verbose_name_plural = 'Rules'
    
    def __str__(self):
        return f"{self.title} ({self.applicability})"

class Syllabus(models.Model):
    """Syllabus Information"""
    COURSE_CHOICES = [
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Electronics', 'Electronics'),
        ('Mechanical', 'Mechanical'),
        ('Civil', 'Civil'),
        ('Electrical', 'Electrical'),
    ]
    
    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
        ('7', 'Semester 7'),
        ('8', 'Semester 8'),
    ]
    
    department = models.CharField(max_length=100)
    course = models.CharField(max_length=100, choices=COURSE_CHOICES)
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    subject_code = models.CharField(max_length=50)
    subject_name = models.CharField(max_length=200)
    units = models.TextField(help_text='Units/Modules (one per line or JSON)')
    credits = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_syllabi')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_syllabi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'semester', 'subject_code']
        verbose_name = 'Syllabus'
        verbose_name_plural = 'Syllabi'
        unique_together = ['course', 'semester', 'subject_code']
    
    def __str__(self):
        return f"{self.subject_code} - {self.subject_name} ({self.course}, Sem {self.semester})"

class ExamInformation(models.Model):
    """Examination Information"""
    COURSE_CHOICES = [
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Electronics', 'Electronics'),
        ('Mechanical', 'Mechanical'),
        ('Civil', 'Civil'),
        ('Electrical', 'Electrical'),
        ('All', 'All Courses'),
    ]
    
    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
        ('7', 'Semester 7'),
        ('8', 'Semester 8'),
        ('All', 'All Semesters'),
    ]
    
    exam_name = models.CharField(max_length=200)
    course = models.CharField(max_length=100, choices=COURSE_CHOICES)
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    exam_date = models.DateField()
    duration = models.CharField(max_length=50, help_text='Duration (e.g., "3 hours", "2 hours 30 minutes")')
    instructions = models.TextField(help_text='Exam instructions and guidelines')
    venue = models.CharField(max_length=200, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_exams')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_exams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-exam_date', 'course', 'semester']
        verbose_name = 'Exam Information'
        verbose_name_plural = 'Exam Information'
    
    def __str__(self):
        return f"{self.exam_name} - {self.course} (Sem {self.semester})"