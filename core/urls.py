from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    ChatHistoryView,
    ChatMessageView,
    FeedbackView,
    SavedAnswersView,
    UserSettingsView,
    SearchView,
    ImageQueryView,
    NotificationView,
    VoiceToTextView
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
    KnowledgeBaseApproveView,
    SuperAdminDashboardView,
    SuperAdminPendingRequestsView,
    SuperAdminApproveRequestView,
    SuperAdminRejectRequestView,
    SuperAdminManageUserView,
    SuperAdminActivityLogsView,
    SuperAdminSystemAnalyticsView,
    SuperAdminAssignRoleView
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User Profile
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # User Settings (Dark Mode, Notifications, etc.)
    path('settings/', UserSettingsView.as_view(), name='user-settings'),
    
    # Search
    path('search/', SearchView.as_view(), name='search'),
    
    # Image Query
    path('image-query/', ImageQueryView.as_view(), name='image-query'),
    
    # Voice to Text
    path('voice-to-text/', VoiceToTextView.as_view(), name='voice-to-text'),
    
    # Notifications
    path('notifications/', NotificationView.as_view(), name='notifications'),
    
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
    
    # Super Admin Routes
    path('super-admin/dashboard/', SuperAdminDashboardView.as_view(), name='super-admin-dashboard'),
    path('super-admin/pending-requests/', SuperAdminPendingRequestsView.as_view(), name='super-admin-pending-requests'),
    path('super-admin/approve-request/<int:admin_id>/', SuperAdminApproveRequestView.as_view(), name='super-admin-approve-request'),
    path('super-admin/reject-request/<int:admin_id>/', SuperAdminRejectRequestView.as_view(), name='super-admin-reject-request'),
    path('super-admin/manage-user/<int:user_id>/', SuperAdminManageUserView.as_view(), name='super-admin-manage-user'),
    path('super-admin/activity-logs/', SuperAdminActivityLogsView.as_view(), name='super-admin-activity-logs'),
    path('super-admin/system-analytics/', SuperAdminSystemAnalyticsView.as_view(), name='super-admin-system-analytics'),
    path('super-admin/assign-role/<int:admin_id>/', SuperAdminAssignRoleView.as_view(), name='super-admin-assign-role'),
]
