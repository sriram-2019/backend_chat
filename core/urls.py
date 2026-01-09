from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    ChatHistoryView,
    ChatMessageView,
    FeedbackView,
    SavedAnswersView
)
from .admin_views import (
    AdminRegisterView,
    AdminLoginView,
    AdminDashboardView,
    AnalyticsView,
    UnsolvedQuestionsView,
    DocumentsView,
    AdminListView,
    StudentDetailView,
    AdminCollegeDataView,
    RulesView,
    RuleDetailView,
    SyllabusView,
    SyllabusDetailView,
    ExamInformationView,
    ExamInformationDetailView,
    KnowledgeBaseView,
    KnowledgeBaseDetailView,
    KnowledgeBaseApproveView
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # Chat
    path('chat/message/', ChatMessageView.as_view(), name='chat-message'),
    path('chat/history/', ChatHistoryView.as_view(), name='chat-history'),
    
    # Feedback
    path('feedback/', FeedbackView.as_view(), name='feedback'),
    
    # Saved Answers
    path('saved/', SavedAnswersView.as_view(), name='saved-answers'),
    
    # Public Knowledge Base (for students - approved entries only)
    # Must be before admin routes to avoid conflicts
    path('knowledge-base/', KnowledgeBaseView.as_view(), name='public-knowledge-base'),
    
    # Admin Routes
    path('admin/register/', AdminRegisterView.as_view(), name='admin-register'),
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/analytics/', AnalyticsView.as_view(), name='admin-analytics'),
    path('admin/unsolved/', UnsolvedQuestionsView.as_view(), name='admin-unsolved'),
    path('admin/documents/', DocumentsView.as_view(), name='admin-documents'),
    path('admin/list/', AdminListView.as_view(), name='admin-list'),
    path('admin/student/<str:username>/', StudentDetailView.as_view(), name='admin-student-detail'),
    path('admin/college-data/', AdminCollegeDataView.as_view(), name='admin-college-data'),
    
    # Rules Management
    path('admin/rules/', RulesView.as_view(), name='admin-rules'),
    path('admin/rules/<int:rule_id>/', RuleDetailView.as_view(), name='admin-rule-detail'),
    
    # Syllabus Management
    path('admin/syllabus/', SyllabusView.as_view(), name='admin-syllabus'),
    path('admin/syllabus/<int:syllabus_id>/', SyllabusDetailView.as_view(), name='admin-syllabus-detail'),
    
    # Exam Information Management
    path('admin/exams/', ExamInformationView.as_view(), name='admin-exams'),
    path('admin/exams/<int:exam_id>/', ExamInformationDetailView.as_view(), name='admin-exam-detail'),
    
    # Knowledge Base Management
    path('admin/knowledge-base/', KnowledgeBaseView.as_view(), name='admin-knowledge-base'),
    path('admin/knowledge-base/<int:kb_id>/', KnowledgeBaseDetailView.as_view(), name='admin-knowledge-base-detail'),
    path('admin/knowledge-base/<int:kb_id>/approve/', KnowledgeBaseApproveView.as_view(), name='admin-knowledge-base-approve'),
]

