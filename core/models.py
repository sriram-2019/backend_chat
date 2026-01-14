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
    confidence_score = models.FloatField(default=0.0, help_text='Response confidence score (0-100)')
    source_details = models.JSONField(default=dict, blank=True, help_text='Details about response source (KB ID, matching score, etc.)')
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
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    ROLE_CHOICES = [
        ('department_admin', 'Department Admin'),
        ('super_admin', 'Super Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    prof_id = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='Professor ID')
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='department_admin')
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_admin_profiles')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    permissions = models.JSONField(default=dict, blank=True, help_text='Role-based permissions')
    is_active = models.BooleanField(default=True)
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
    
    VISIBILITY_CHOICES = [
        ('public', 'Public - All Users'),
        ('department', 'Department Only'),
        ('private', 'Private - Admin Only'),
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
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    target_departments = models.JSONField(default=list, blank=True, help_text='List of department names for department visibility')
    target_user_groups = models.JSONField(default=list, blank=True, help_text='Specific user groups who can access')
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


class UserSettings(models.Model):
    """User settings including dark mode and notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    dark_mode = models.BooleanField(default=False)
    push_notifications_enabled = models.BooleanField(default=True)
    voice_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'
    
    def __str__(self):
        return f"Settings for {self.user.username}"


class ImageQuery(models.Model):
    """Image queries with AI-based responses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='image_queries', null=True, blank=True)
    image = models.ImageField(upload_to='image_queries/')
    query_text = models.TextField(blank=True, null=True, help_text='Optional text query about the image')
    ai_response = models.TextField(blank=True, null=True)
    confidence_score = models.FloatField(default=0.0, help_text='AI confidence score (0-100)')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Image Query'
        verbose_name_plural = 'Image Queries'
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"Image query by {username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class AdminActivityLog(models.Model):
    """Track admin activities for monitoring"""
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('upload', 'Document Upload'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('create', 'Create'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('notification', 'Send Notification'),
    ]
    
    TARGET_TYPE_CHOICES = [
        ('document', 'Document'),
        ('kb_entry', 'Knowledge Base Entry'),
        ('user', 'User'),
        ('admin', 'Admin'),
        ('rule', 'Rule'),
        ('syllabus', 'Syllabus'),
        ('exam', 'Exam Information'),
        ('notification', 'Notification'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50, choices=TARGET_TYPE_CHOICES)
    target_id = models.IntegerField(null=True, blank=True)
    target_title = models.CharField(max_length=255, blank=True, null=True, help_text='Human readable title of target')
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Activity Log'
        verbose_name_plural = 'Admin Activity Logs'
    
    def __str__(self):
        return f"{self.admin.username} - {self.action} - {self.target_type} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Notification(models.Model):
    """Push notifications for users"""
    NOTIFICATION_TYPES = [
        ('document', 'New Document'),
        ('announcement', 'Announcement'),
        ('update', 'Content Update'),
        ('system', 'System Notification'),
        ('reminder', 'Reminder'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='announcement')
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True, help_text='Additional data like document ID, link, etc.')
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"Notification to {self.user.username}: {self.title}"


class SystemReport(models.Model):
    """Generated system reports for download"""
    REPORT_TYPES = [
        ('user_activity', 'User Activity Report'),
        ('admin_activity', 'Admin Activity Report'),
        ('ai_usage', 'AI Usage Report'),
        ('system_performance', 'System Performance Report'),
        ('analytics', 'Analytics Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
    ]
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    report_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_reports')
    parameters = models.JSONField(default=dict, blank=True, help_text='Report generation parameters')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'System Report'
        verbose_name_plural = 'System Reports'
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.created_at.strftime('%Y-%m-%d')}"