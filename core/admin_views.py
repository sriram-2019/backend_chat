from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    AdminProfile, UnsolvedQuestion, Document, Analytics,
    ChatHistory, Feedback, KnowledgeBase, StudentProfile,
    Rule, Syllabus, ExamInformation, AdminActivityLog,
    Notification, SystemReport, User
)
from .serializers import (
    AdminProfileSerializer, UnsolvedQuestionSerializer,
    DocumentSerializer, AnalyticsSerializer,
    RuleSerializer, SyllabusSerializer, ExamInformationSerializer,
    KnowledgeBaseSerializer, AdminActivityLogSerializer,
    NotificationSerializer, SystemReportSerializer
)

def is_admin(user, check_authenticated=False):
    """Check if user is an admin (has AdminProfile OR is staff)"""
    if not user:
        return False
    if check_authenticated and not user.is_authenticated:
        return False
    try:
        # Allow users with AdminProfile OR staff users (teachers/admins)
        return AdminProfile.objects.filter(user=user).exists() or user.is_staff
    except:
        return False

def is_super_admin(user):
    """Check if user is a super admin (has AdminProfile with role='super_admin' OR is_superuser)"""
    if not user:
        return False
    try:
        # Check if user is Django superuser
        if user.is_superuser:
            return True
        # Check if user has AdminProfile with super_admin role
        admin_profile = AdminProfile.objects.filter(user=user).first()
        if admin_profile and admin_profile.role == 'super_admin':
            return True
        return False
    except:
        return False

def log_admin_activity(admin, action, target_type, target_id=None, target_title=None, details=None, ip_address=None):
    """Helper function to log admin activities"""
    try:
        AdminActivityLog.objects.create(
            admin=admin,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_title=target_title,
            details=details or {},
            ip_address=ip_address
        )
    except Exception as e:
        print(f"Error logging admin activity: {str(e)}")

def get_admin_user(request):
    """Get admin user from request (session) or from user_id parameter"""
    user = request.user if request.user.is_authenticated else None
    if not user:
        # Check both data and query_params for user_id
        user_id = request.data.get('user_id') if isinstance(request.data, dict) else None
        user_id = user_id or request.query_params.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except (User.DoesNotExist, ValueError, TypeError):
                pass
    
    if user and is_admin(user):
        return user
    return None

class AdminRegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        full_name = request.data.get('full_name')
        prof_id = request.data.get('prof_id', '')
        phone = request.data.get('phone', '')
        department = request.data.get('department', '')
        username = request.data.get('username', '')
        
        if not email or not password or not full_name:
            return Response(
                {"error": "Email, password, and full name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if username is provided and not already taken
        if username:
            if User.objects.filter(username=username).exists():
                return Response(
                    {"error": "Username already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            username = email.split('@')[0]
            # Ensure username is unique
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
        
        # Check if prof_id is provided and unique
        if prof_id:
            if AdminProfile.objects.filter(prof_id=prof_id).exists():
                return Response(
                    {"error": "Professor ID already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True  # Admin users are staff
            )
            
            AdminProfile.objects.create(
                user=user,
                full_name=full_name,
                email=email,
                prof_id=prof_id if prof_id else None,
                phone=phone if phone else None,
                department=department if department else None
            )
            
            return Response({
                "message": "Admin account created successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": full_name
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            logger.warning(f"Admin login attempt with missing credentials")
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Admin login attempt for email: {email}")
        
        try:
            user = User.objects.get(email=email)
            logger.info(f"User found: {user.username} (ID: {user.id})")
        except User.DoesNotExist:
            logger.warning(f"Admin login failed: User with email {email} does not exist")
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Error looking up user: {str(e)}")
            return Response(
                {"error": "An error occurred during login"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check if user is admin - don't check session yet as we're logging in
        is_admin_user = is_admin(user, check_authenticated=False)
        logger.info(f"User {user.username} is_admin check: {is_admin_user}")
        
        if not is_admin_user:
            logger.warning(f"Admin login denied: User {user.username} is not an admin")
            return Response(
                {"error": "Access denied. Admin account required."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Authenticate password
        authenticated_user = authenticate(username=user.username, password=password)
        if not authenticated_user:
            logger.warning(f"Admin login failed: Invalid password for user {user.username}")
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Login the user (creates session)
        try:
            login(request, authenticated_user)
            logger.info(f"Admin login successful: {authenticated_user.username} (ID: {authenticated_user.id})")
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return Response(
                {"error": "An error occurred during login"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            profile = AdminProfile.objects.get(user=authenticated_user)
            profile_data = AdminProfileSerializer(profile).data
        except AdminProfile.DoesNotExist:
            profile_data = None
            logger.info(f"No AdminProfile found for user {authenticated_user.username}, but user is staff")
        
        return Response({
            "message": "Login successful",
            "user": {
                "id": authenticated_user.id,
                "username": authenticated_user.username,
                "email": authenticated_user.email,
                "is_admin": True
            },
            "profile": profile_data
        }, status=status.HTTP_200_OK)

class AdminDashboardView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get statistics
        total_students = StudentProfile.objects.count()
        total_questions = ChatHistory.objects.filter(sender='user').count()
        total_unsolved = UnsolvedQuestion.objects.filter(status='pending').count()
        total_documents = Document.objects.count()
        total_kb_entries = KnowledgeBase.objects.count()
        
        # Get students who have used the chat (have chat history)
        students_with_chats = User.objects.filter(
            chat_history__isnull=False
        ).distinct().select_related('student_profile')
        
        # Get student data with profile info
        students_list = []
        for student_user in students_with_chats:
            try:
                profile = StudentProfile.objects.get(user=student_user)
                students_list.append({
                    "id": student_user.id,
                    "username": student_user.username,
                    "email": student_user.email,
                    "full_name": profile.full_name,
                    "roll_no": profile.roll_no,
                    "course": profile.course,
                    "year": profile.year,
                    "total_messages": ChatHistory.objects.filter(user=student_user, sender='user').count(),
                    "last_activity": ChatHistory.objects.filter(user=student_user).order_by('-timestamp').first().timestamp if ChatHistory.objects.filter(user=student_user).exists() else None
                })
            except StudentProfile.DoesNotExist:
                # If no profile, still include with basic info
                students_list.append({
                    "id": student_user.id,
                    "username": student_user.username,
                    "email": student_user.email,
                    "full_name": student_user.get_full_name() or student_user.username,
                    "roll_no": "N/A",
                    "course": "N/A",
                    "year": "N/A",
                    "total_messages": ChatHistory.objects.filter(user=student_user, sender='user').count(),
                    "last_activity": ChatHistory.objects.filter(user=student_user).order_by('-timestamp').first().timestamp if ChatHistory.objects.filter(user=student_user).exists() else None
                })
        
        # Sort by last activity (most recent first)
        students_list.sort(key=lambda x: x['last_activity'] if x['last_activity'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        
        # Recent activity
        recent_questions = ChatHistory.objects.filter(sender='user').order_by('-timestamp')[:10]
        recent_unsolved = UnsolvedQuestion.objects.filter(status='pending').order_by('-created_at')[:5]
        
        return Response({
            "stats": {
                "total_students": total_students,
                "total_questions": total_questions,
                "total_unsolved": total_unsolved,
                "total_documents": total_documents,
                "total_kb_entries": total_kb_entries
            },
            "students_with_chats": students_list,
            "recent_questions": [
                {
                    "id": q.id,
                    "message": q.message,
                    "user": q.user.username if q.user else "Anonymous",
                    "timestamp": q.timestamp
                } for q in recent_questions
            ],
            "recent_unsolved": UnsolvedQuestionSerializer(recent_unsolved, many=True).data
        }, status=status.HTTP_200_OK)

class AnalyticsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get date range (default: last 30 days)
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Calculate analytics
        chats = ChatHistory.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
        feedbacks = Feedback.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
        
        analytics_data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "total_questions": chats.filter(sender='user').count(),
            "total_responses": chats.filter(sender='assistant').count(),
            "kb_matches": chats.filter(intent='kb_match').count(),
            "ai_fallbacks": chats.filter(intent='ai_fallback').count(),
            "helpful_feedback": feedbacks.filter(rating='helpful').count(),
            "not_helpful_feedback": feedbacks.filter(rating='not_helpful').count(),
            "total_users": StudentProfile.objects.filter(created_at__date__lte=end_date).count(),
            "unsolved_questions": UnsolvedQuestion.objects.filter(status='pending').count(),
            "daily_stats": []
        }
        
        # Daily breakdown
        current_date = start_date
        while current_date <= end_date:
            day_chats = chats.filter(timestamp__date=current_date)
            day_feedbacks = feedbacks.filter(timestamp__date=current_date)
            
            analytics_data["daily_stats"].append({
                "date": current_date.isoformat(),
                "questions": day_chats.filter(sender='user').count(),
                "kb_matches": day_chats.filter(intent='kb_match').count(),
                "ai_fallbacks": day_chats.filter(intent='ai_fallback').count(),
                "helpful": day_feedbacks.filter(rating='helpful').count(),
                "not_helpful": day_feedbacks.filter(rating='not_helpful').count()
            })
            current_date += timedelta(days=1)
        
        return Response(analytics_data, status=status.HTTP_200_OK)

class UnsolvedQuestionsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        status_filter = request.query_params.get('status', 'pending')
        questions = UnsolvedQuestion.objects.filter(status=status_filter).order_by('-created_at')
        serializer = UnsolvedQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Resolve an unsolved question"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        question_id = request.data.get('question_id')
        resolved_answer = request.data.get('resolved_answer')
        
        if not question_id or not resolved_answer:
            return Response(
                {"error": "question_id and resolved_answer are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            question = UnsolvedQuestion.objects.get(id=question_id)
            question.status = 'resolved'
            question.resolved_by = user
            question.resolved_answer = resolved_answer
            question.resolved_at = timezone.now()
            question.save()
            
            # Optionally add to Knowledge Base
            if request.data.get('add_to_kb', False):
                KnowledgeBase.objects.create(
                    question=question.question,
                    answer=resolved_answer
                )
            
            serializer = UnsolvedQuestionSerializer(question)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UnsolvedQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class DocumentsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        doc_type = request.query_params.get('type')
        documents = Document.objects.all()
        if doc_type:
            documents = documents.filter(document_type=doc_type)
        
        documents = documents.order_by('-created_at')
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Upload a document, extract text, and add to knowledge base"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle file upload
        file = request.FILES.get('file')
        if not file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract text from document
        extracted_text = self._extract_text_from_file(file)
        
        if not extracted_text or extracted_text.startswith("Error") or extracted_text.startswith("PDF extraction") or extracted_text.startswith("python-docx"):
            return Response(
                {"error": extracted_text or "Could not extract text from document"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save file to media directory
        import os
        from django.conf import settings
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'documents')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        # Save document metadata
        document = Document.objects.create(
            title=request.data.get('title', file.name),
            document_type=request.data.get('document_type', 'other'),
            description=request.data.get('description', ''),
            file_path=file_path,
            file_name=file.name,
            file_size=file.size,
            extracted_text=extracted_text[:10000],  # Store first 10000 chars
            uploaded_by=user
        )
        
        # Map document_type to KB type
        doc_type = request.data.get('document_type', 'other')
        kb_type_map = {
            'rules': 'rule',
            'syllabus': 'syllabus',
            'exam_info': 'exam',
            'other': 'general'
        }
        kb_type = kb_type_map.get(doc_type, 'general')
        
        # Set visibility and target departments
        visibility = request.data.get('visibility', 'public')
        target_departments = request.data.get('target_departments', [])
        target_user_groups = request.data.get('target_user_groups', [])
        
        if isinstance(target_departments, str):
            import json
            try:
                target_departments = json.loads(target_departments)
            except:
                target_departments = [target_departments] if target_departments else []
        
        if isinstance(target_user_groups, str):
            import json
            try:
                target_user_groups = json.loads(target_user_groups)
            except:
                target_user_groups = [target_user_groups] if target_user_groups else []
        
        document.visibility = visibility
        document.target_departments = target_departments
        document.target_user_groups = target_user_groups
        document.save()
        
        # Add extracted text to Knowledge Base
        kb_entry = KnowledgeBase.objects.create(
            question=f"Document: {document.title}",
            answer=extracted_text[:5000],  # Limit to 5000 chars for KB
            type=kb_type,
            created_by=user,
            approved=True,  # Auto-approve admin-uploaded documents
            approved_by=user,
            approved_at=timezone.now()
        )
        
        # Log admin activity
        log_admin_activity(
            admin=user,
            action='upload',
            target_type='document',
            target_id=document.id,
            target_title=document.title,
            details={
                'document_type': document.document_type,
                'file_name': document.file_name,
                'visibility': visibility,
                'target_departments': target_departments
            },
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Send push notifications to relevant department users
        try:
            # Get users from target departments
            target_users = []
            if visibility == 'department' and target_departments:
                # Get students from target departments
                students = StudentProfile.objects.filter(course__in=target_departments)
                target_users = [student.user for student in students]
            elif visibility == 'public':
                # Notify all active users
                target_users = list(User.objects.filter(is_active=True))
            
            # Create notifications for target users
            notification_title = f"New Document: {document.title}"
            notification_message = f"A new {document.document_type} document has been uploaded."
            
            for target_user in target_users:
                # Check if user has push notifications enabled (from UserSettings)
                try:
                    from .models import UserSettings
                    settings = UserSettings.objects.get(user=target_user)
                    if not settings.push_notifications_enabled:
                        continue
                except:
                    pass  # Default to sending if no settings found
                
                Notification.objects.create(
                    user=target_user,
                    title=notification_title,
                    message=notification_message,
                    notification_type='document',
                    metadata={'document_id': document.id, 'document_type': document.document_type},
                    sent_by=user
                )
        except Exception as e:
            print(f"Error sending notifications: {str(e)}")
            # Don't fail the upload if notifications fail
        
        return Response({
            'document': DocumentSerializer(document).data,
            'kb_entry_id': kb_entry.id,
            'extracted_text_length': len(extracted_text),
            'message': 'Document uploaded and added to knowledge base'
        }, status=status.HTTP_201_CREATED)
    
    def _extract_text_from_file(self, file):
        """Extract text from uploaded file (PDF, DOCX, TXT)"""
        import os
        from django.conf import settings
        
        try:
            file_extension = os.path.splitext(file.name)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_text_from_pdf(file)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_text_from_docx(file)
            elif file_extension == '.txt':
                return self._extract_text_from_txt(file)
            else:
                return None
        except Exception as e:
            print(f"Error extracting text: {str(e)}")
            return None
    
    def _extract_text_from_pdf(self, file):
        """Extract text from PDF file"""
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except ImportError:
            # Fallback: try pdfplumber
            try:
                import pdfplumber
                text = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                return text.strip()
            except ImportError:
                return "PDF extraction library not installed. Please install PyPDF2 or pdfplumber."
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
    
    def _extract_text_from_docx(self, file):
        """Extract text from DOCX file"""
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except ImportError:
            return "python-docx library not installed. Please install it to extract text from Word documents."
        except Exception as e:
            return f"Error extracting DOCX: {str(e)}"
    
    def _extract_text_from_txt(self, file):
        """Extract text from TXT file"""
        try:
            file.seek(0)  # Reset file pointer
            text = file.read().decode('utf-8')
            return text.strip()
        except Exception as e:
            return f"Error extracting TXT: {str(e)}"

class AdminListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all admin users - accessible for authenticated admins"""
        user = get_admin_user(request)
        
        # If no user from get_admin_user, check if user_id was provided
        if not user:
            user_id = request.query_params.get('user_id')
            if user_id:
                try:
                    user_obj = User.objects.get(id=user_id)
                    # Check if this user is an admin
                    if is_admin(user_obj):
                        user = user_obj
                    else:
                        return Response(
                            {"error": "Admin access required"},
                            status=status.HTTP_403_FORBIDDEN
                        )
                except (User.DoesNotExist, ValueError, TypeError):
                    pass
        
        # Final check - user must be admin
        if not user or not is_admin(user):
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        admins = AdminProfile.objects.all().order_by('-created_at')
        serializer = AdminProfileSerializer(admins, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StudentDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, username):
        """Get student details and chat history by username"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            student_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Student not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get student profile
        try:
            profile = StudentProfile.objects.get(user=student_user)
            profile_data = {
                'id': profile.id,
                'full_name': profile.full_name,
                'roll_no': profile.roll_no,
                'email': profile.email,
                'phone': profile.phone,
                'course': profile.course,
                'year': profile.year,
                'created_at': profile.created_at,
            }
        except StudentProfile.DoesNotExist:
            profile_data = {
                'full_name': student_user.get_full_name() or student_user.username,
                'roll_no': 'N/A',
                'email': student_user.email,
            }
        
        # Get all chat history for this student
        from .serializers import ChatHistorySerializer
        chats = ChatHistory.objects.filter(user=student_user).order_by('-timestamp')
        chat_data = ChatHistorySerializer(chats, many=True).data
        
        return Response({
            'user': {
                'id': student_user.id,
                'username': student_user.username,
                'email': student_user.email,
            },
            'profile': profile_data,
            'chat_history': chat_data,
            'total_messages': chats.count(),
        }, status=status.HTTP_200_OK)

# Rules Management API
class RulesView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all rules"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        status_filter = request.query_params.get('status', None)
        applicability = request.query_params.get('applicability', None)
        
        rules = Rule.objects.all()
        if status_filter:
            rules = rules.filter(status=status_filter)
        if applicability:
            rules = rules.filter(applicability=applicability)
        
        rules = rules.order_by('-created_at')
        serializer = RuleSerializer(rules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new rule"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = RuleSerializer(data=request.data)
        if serializer.is_valid():
            rule = serializer.save(created_by=user, updated_by=user)
            return Response(RuleSerializer(rule).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RuleDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, rule_id):
        """Get a specific rule"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            rule = Rule.objects.get(id=rule_id)
            serializer = RuleSerializer(rule)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Rule.DoesNotExist:
            return Response(
                {"error": "Rule not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, rule_id):
        """Update a rule"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            rule = Rule.objects.get(id=rule_id)
            serializer = RuleSerializer(rule, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(updated_by=user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Rule.DoesNotExist:
            return Response(
                {"error": "Rule not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, rule_id):
        """Delete a rule"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            rule = Rule.objects.get(id=rule_id)
            rule.delete()
            return Response({"message": "Rule deleted successfully"}, status=status.HTTP_200_OK)
        except Rule.DoesNotExist:
            return Response(
                {"error": "Rule not found"},
                status=status.HTTP_404_NOT_FOUND
            )

# Syllabus Management API
class SyllabusView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all syllabus entries"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        course = request.query_params.get('course', None)
        semester = request.query_params.get('semester', None)
        
        syllabi = Syllabus.objects.all()
        if course:
            syllabi = syllabi.filter(course=course)
        if semester:
            syllabi = syllabi.filter(semester=semester)
        
        syllabi = syllabi.order_by('course', 'semester', 'subject_code')
        serializer = SyllabusSerializer(syllabi, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new syllabus entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SyllabusSerializer(data=request.data)
        if serializer.is_valid():
            syllabus = serializer.save(created_by=user, updated_by=user)
            return Response(SyllabusSerializer(syllabus).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SyllabusDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, syllabus_id):
        """Get a specific syllabus entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            syllabus = Syllabus.objects.get(id=syllabus_id)
            serializer = SyllabusSerializer(syllabus)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Syllabus.DoesNotExist:
            return Response(
                {"error": "Syllabus not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, syllabus_id):
        """Update a syllabus entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            syllabus = Syllabus.objects.get(id=syllabus_id)
            serializer = SyllabusSerializer(syllabus, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(updated_by=user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Syllabus.DoesNotExist:
            return Response(
                {"error": "Syllabus not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, syllabus_id):
        """Delete a syllabus entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            syllabus = Syllabus.objects.get(id=syllabus_id)
            syllabus.delete()
            return Response({"message": "Syllabus deleted successfully"}, status=status.HTTP_200_OK)
        except Syllabus.DoesNotExist:
            return Response(
                {"error": "Syllabus not found"},
                status=status.HTTP_404_NOT_FOUND
            )

# Exam Information Management API
class ExamInformationView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all exam information"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        course = request.query_params.get('course', None)
        semester = request.query_params.get('semester', None)
        
        exams = ExamInformation.objects.all()
        if course:
            exams = exams.filter(course=course)
        if semester:
            exams = exams.filter(semester=semester)
        
        exams = exams.order_by('-exam_date', 'course', 'semester')
        serializer = ExamInformationSerializer(exams, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new exam information entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ExamInformationSerializer(data=request.data)
        if serializer.is_valid():
            exam = serializer.save(created_by=user, updated_by=user)
            return Response(ExamInformationSerializer(exam).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ExamInformationDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, exam_id):
        """Get a specific exam information"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            exam = ExamInformation.objects.get(id=exam_id)
            serializer = ExamInformationSerializer(exam)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ExamInformation.DoesNotExist:
            return Response(
                {"error": "Exam information not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, exam_id):
        """Update exam information"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            exam = ExamInformation.objects.get(id=exam_id)
            serializer = ExamInformationSerializer(exam, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(updated_by=user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ExamInformation.DoesNotExist:
            return Response(
                {"error": "Exam information not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, exam_id):
        """Delete exam information"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            exam = ExamInformation.objects.get(id=exam_id)
            exam.delete()
            return Response({"message": "Exam information deleted successfully"}, status=status.HTTP_200_OK)
        except ExamInformation.DoesNotExist:
            return Response(
                {"error": "Exam information not found"},
                status=status.HTTP_404_NOT_FOUND
            )

# Knowledge Base Management API
class KnowledgeBaseView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get knowledge base entries - public for approved entries, admin for all"""
        user = get_admin_user(request)
        is_admin_user = user is not None
        
        approved = request.query_params.get('approved', None)
        entry_type = request.query_params.get('type', None)
        
        # If not admin, only show approved entries
        if not is_admin_user:
            kb_entries = KnowledgeBase.objects.filter(approved=True)
        else:
            # Admin can see all entries
            kb_entries = KnowledgeBase.objects.all()
            if approved is not None:
                kb_entries = kb_entries.filter(approved=approved.lower() == 'true')
        
        if entry_type:
            kb_entries = kb_entries.filter(type=entry_type)
        
        kb_entries = kb_entries.order_by('-created_at')
        serializer = KnowledgeBaseSerializer(kb_entries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new knowledge base entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Remove user_id from data before passing to serializer (it's not a model field)
        kb_data = {k: v for k, v in request.data.items() if k != 'user_id'}
        
        serializer = KnowledgeBaseSerializer(data=kb_data)
        if serializer.is_valid():
            # Automatically approve admin-created entries
            kb_entry = serializer.save(
                created_by=user,
                approved=True,
                approved_by=user,
                approved_at=timezone.now()
            )
            return Response(KnowledgeBaseSerializer(kb_entry).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KnowledgeBaseDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, kb_id):
        """Get a specific knowledge base entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            kb_entry = KnowledgeBase.objects.get(id=kb_id)
            serializer = KnowledgeBaseSerializer(kb_entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KnowledgeBase.DoesNotExist:
            return Response(
                {"error": "Knowledge base entry not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, kb_id):
        """Update a knowledge base entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            kb_entry = KnowledgeBase.objects.get(id=kb_id)
            # Remove user_id from data before passing to serializer
            kb_data = {k: v for k, v in request.data.items() if k != 'user_id'}
            serializer = KnowledgeBaseSerializer(kb_entry, data=kb_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except KnowledgeBase.DoesNotExist:
            return Response(
                {"error": "Knowledge base entry not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, kb_id):
        """Delete a knowledge base entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            kb_entry = KnowledgeBase.objects.get(id=kb_id)
            kb_entry.delete()
            return Response({"message": "Knowledge base entry deleted successfully"}, status=status.HTTP_200_OK)
        except KnowledgeBase.DoesNotExist:
            return Response(
                {"error": "Knowledge base entry not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class KnowledgeBaseApproveView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, kb_id):
        """Approve a knowledge base entry"""
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            kb_entry = KnowledgeBase.objects.get(id=kb_id)
            kb_entry.approved = True
            kb_entry.approved_by = user
            kb_entry.approved_at = timezone.now()
            kb_entry.save()
            serializer = KnowledgeBaseSerializer(kb_entry)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except KnowledgeBase.DoesNotExist:
            return Response(
                {"error": "Knowledge base entry not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminCollegeDataView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_admin_user(request)
        if not user:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data_type = request.query_params.get('type', 'rules')
        
        if data_type == 'rules':
            data = Rule.objects.all().order_by('-created_at')
            serializer = RuleSerializer(data, many=True)
        elif data_type == 'syllabus':
            data = Syllabus.objects.all().order_by('course', 'semester', 'subject_code')
            serializer = SyllabusSerializer(data, many=True)
        elif data_type == 'exams':
            data = ExamInformation.objects.all().order_by('-exam_date')
            serializer = ExamInformationSerializer(data, many=True)
        else:
            return Response(
                {"error": f"Invalid type: {data_type}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==================== SUPER ADMIN ENDPOINTS ====================

def get_super_admin_user(request):
    """Get super admin user from request"""
    user = get_admin_user(request)
    if user and is_super_admin(user):
        return user
    return None

class SuperAdminDashboardView(APIView):
    """Super Admin Dashboard with system-wide analytics"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_super_admin_user(request)
        if not user:
            return Response(
                {"error": "Super Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # System-wide statistics
        total_users = User.objects.count()
        total_students = StudentProfile.objects.count()
        total_admins = AdminProfile.objects.count()
        pending_admin_requests = AdminProfile.objects.filter(approval_status='pending').count()
        active_admins = AdminProfile.objects.filter(is_active=True, approval_status='approved').count()
        total_questions = ChatHistory.objects.filter(sender='user').count()
        total_unsolved = UnsolvedQuestion.objects.filter(status='pending').count()
        total_documents = Document.objects.count()
        total_kb_entries = KnowledgeBase.objects.count()
        kb_matches = ChatHistory.objects.filter(intent='kb_match').count()
        ai_fallbacks = ChatHistory.objects.filter(intent='ai_fallback').count()
        
        # Recent admin activities
        recent_activities = AdminActivityLog.objects.all().order_by('-timestamp')[:10]
        
        # Department-wise statistics
        departments = {}
        for admin in AdminProfile.objects.filter(approval_status='approved', is_active=True):
            dept = admin.department or 'Unassigned'
            if dept not in departments:
                departments[dept] = {'admins': 0, 'documents': 0}
            departments[dept]['admins'] += 1
        
        for doc in Document.objects.all():
            dept = doc.uploaded_by.admin_profile.department if hasattr(doc.uploaded_by, 'admin_profile') and doc.uploaded_by.admin_profile else 'Unassigned'
            if dept not in departments:
                departments[dept] = {'admins': 0, 'documents': 0}
            departments[dept]['documents'] += 1
        
        return Response({
            "stats": {
                "total_users": total_users,
                "total_students": total_students,
                "total_admins": total_admins,
                "pending_admin_requests": pending_admin_requests,
                "active_admins": active_admins,
                "total_questions": total_questions,
                "total_unsolved": total_unsolved,
                "total_documents": total_documents,
                "total_kb_entries": total_kb_entries,
                "kb_matches": kb_matches,
                "ai_fallbacks": ai_fallbacks,
                "kb_match_rate": round((kb_matches / total_questions * 100) if total_questions > 0 else 0, 2)
            },
            "departments": departments,
            "recent_activities": AdminActivityLogSerializer(recent_activities, many=True).data
        }, status=status.HTTP_200_OK)

class SuperAdminPendingRequestsView(APIView):
    """Get pending admin registration requests"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_super_admin_user(request)
        if not user:
            return Response(
                {"error": "Super Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        pending_requests = AdminProfile.objects.filter(approval_status='pending').order_by('-created_at')
        serializer = AdminProfileSerializer(pending_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SuperAdminApproveRequestView(APIView):
    """Approve admin registration request"""
    permission_classes = [AllowAny]
    
    def post(self, request, admin_id):
        user = get_super_admin_user(request)
        if not user:
            return Response(
                {"error": "Super Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            admin_profile = AdminProfile.objects.get(id=admin_id)
            admin_profile.approval_status = 'approved'
            admin_profile.approved_by = user
            admin_profile.approved_at = timezone.now()
            admin_profile.is_active = True
            admin_profile.save()
            
            # Log activity
            log_admin_activity(
                admin=user,
                action='approve',
                target_type='admin',
                target_id=admin_profile.id,
                target_title=f"{admin_profile.full_name} ({admin_profile.email})",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            serializer = AdminProfileSerializer(admin_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AdminProfile.DoesNotExist:
            return Response(
                {"error": "Admin profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class SuperAdminRejectRequestView(APIView):
    """Reject admin registration request"""
    permission_classes = [AllowAny]
    
    def post(self, request, admin_id):
        user = get_super_admin_user(request)
        if not user:
            return Response(
                {"error": "Super Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            admin_profile = AdminProfile.objects.get(id=admin_id)
            admin_profile.approval_status = 'rejected'
            admin_profile.approved_by = user
            admin_profile.rejection_reason = request.data.get('rejection_reason', 'Request rejected by Super Admin')
            admin_profile.is_active = False
            admin_profile.save()
            
            # Log activity
            log_admin_activity(
                admin=user,
                action='reject',
                target_type='admin',
                target_id=admin_profile.id,
                target_title=f"{admin_profile.full_name} ({admin_profile.email})",
                details={'rejection_reason': admin_profile.rejection_reason},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            serializer = AdminProfileSerializer(admin_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AdminProfile.DoesNotExist:
            return Response(
                {"error": "Admin profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class SuperAdminManageUserView(APIView):
    """Activate/Deactivate users and admins"""
    permission_classes = [AllowAny]
    
    def post(self, request, user_id):
        user = get_super_admin_user(request)
        if not user:
            return Response(
                {"error": "Super Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            target_user = User.objects.get(id=user_id)
            action = request.data.get('action', 'activate')  # 'activate' or 'deactivate'
            
            if action == 'activate':
                target_user.is_active = True
                # If user has admin profile, activate it too
                try:
                    admin_profile = AdminProfile.objects.get(user=target_user)
                    admin_profile.is_active = True
                    admin_profile.save()
                except AdminProfile.DoesNotExist:
                    pass
            elif action == 'deactivate':
                target_user.is_active = False
                # If user has admin profile, deactivate it too
                try:
                    admin_profile = AdminProfile.objects.get(user=target_user)
                    admin_profile.is_active = False
                    admin_profile.save()
                except AdminProfile.DoesNotExist:
                    pass
            else:
                return Response(
                    {"error": "Invalid action. Use 'activate' or 'deactivate'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            target_user.save()
            
            # Log activity
            log_admin_activity(
                admin=user,
                action=action,
                target_type='user',
                target_id=target_user.id,
                target_title=f"{target_user.username} ({target_user.email})",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                "message": f"User {action}d successfully",
                "user": {
                    "id": target_user.id,
                    "username": target_user.username,
                    "email": target_user.email,
                    "is_active": target_user.is_active
                }
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class SuperAdminActivityLogsView(APIView):
    """View admin activity logs"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_super_admin_user(request)
        if not user:
            return Response(
                {"error": "Super Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filter options
        admin_id = request.query_params.get('admin_id')
        action = request.query_params.get('action')
        target_type = request.query_params.get('target_type')
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now() - timedelta(days=days)
        logs = AdminActivityLog.objects.filter(timestamp__gte=start_date)
        
        if admin_id:
            logs = logs.filter(admin_id=admin_id)
        if action:
            logs = logs.filter(action=action)
        if target_type:
            logs = logs.filter(target_type=target_type)
        
        logs = logs.order_by('-timestamp')[:100]  # Limit to 100 most recent
        serializer = AdminActivityLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SuperAdminSystemAnalyticsView(APIView):
    """System-wide analytics for Super Admin"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        user = get_super_admin_user(request)
        if not user:
            return Response(
                {"error": "Super Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # AI usage statistics
        chats = ChatHistory.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
        total_ai_queries = chats.filter(intent='ai_fallback').count()
        total_kb_queries = chats.filter(intent='kb_match').count()
        
        # Admin activity statistics
        activities = AdminActivityLog.objects.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
        uploads_count = activities.filter(action='upload').count()
        updates_count = activities.filter(action='update').count()
        
        # System performance metrics
        total_users_active = User.objects.filter(is_active=True).count()
        total_admins_active = AdminProfile.objects.filter(is_active=True, approval_status='approved').count()
        
        return Response({
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "ai_usage": {
                "total_ai_queries": total_ai_queries,
                "total_kb_queries": total_kb_queries,
                "total_queries": chats.count(),
                "kb_match_rate": round((total_kb_queries / chats.count() * 100) if chats.count() > 0 else 0, 2),
                "ai_fallback_rate": round((total_ai_queries / chats.count() * 100) if chats.count() > 0 else 0, 2)
            },
            "admin_activity": {
                "uploads": uploads_count,
                "updates": updates_count,
                "total_activities": activities.count()
            },
            "system_performance": {
                "active_users": total_users_active,
                "active_admins": total_admins_active,
                "total_documents": Document.objects.count(),
                "total_kb_entries": KnowledgeBase.objects.count()
            }
        }, status=status.HTTP_200_OK)

class SuperAdminAssignRoleView(APIView):
    """Assign role-based access control for admins"""
    permission_classes = [AllowAny]
    
    def post(self, request, admin_id):
        user = get_super_admin_user(request)
        if not user:
            return Response(
                {"error": "Super Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            admin_profile = AdminProfile.objects.get(id=admin_id)
            new_role = request.data.get('role')
            permissions = request.data.get('permissions', {})
            
            if new_role not in ['department_admin', 'super_admin']:
                return Response(
                    {"error": "Invalid role. Must be 'department_admin' or 'super_admin'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            admin_profile.role = new_role
            admin_profile.permissions = permissions
            admin_profile.save()
            
            # Log activity
            log_admin_activity(
                admin=user,
                action='update',
                target_type='admin',
                target_id=admin_profile.id,
                target_title=f"{admin_profile.full_name} - Role changed to {new_role}",
                details={'role': new_role, 'permissions': permissions},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            serializer = AdminProfileSerializer(admin_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AdminProfile.DoesNotExist:
            return Response(
                {"error": "Admin profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
