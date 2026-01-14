from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from .models import (
    StudentProfile, ChatHistory, Feedback,
    KnowledgeBase, UserSettings, ImageQuery, Notification
)
from .serializers import (
    StudentProfileSerializer, ChatHistorySerializer, FeedbackSerializer,
    KnowledgeBaseSerializer, UserSettingsSerializer,
    ImageQuerySerializer, NotificationSerializer, UserRegisterSerializer
)
import json
import base64
import os
import tempfile


# Helper function to get user from request
def get_user_from_request(request):
    """Get user from session or user_id parameter"""
    user = None
    
    # Try session first
    if request.user.is_authenticated:
        user = request.user
    else:
        # Try user_id from query params or body
        user_id = request.query_params.get('user_id') or request.data.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass
    
    return user


class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Register a new user"""
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Get the student profile
            try:
                profile = user.student_profile
                return Response({
                    'message': 'Registration successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': profile.full_name,
                        'roll_no': profile.roll_no,
                        'phone': profile.phone,
                        'course': profile.course,
                        'year': profile.year
                    }
                }, status=status.HTTP_201_CREATED)
            except StudentProfile.DoesNotExist:
                return Response({
                    'message': 'Registration successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Authenticate user with roll_no and password"""
        roll_no = request.data.get('roll_no')
        password = request.data.get('password')
        
        if not roll_no or not password:
            return Response(
                {'error': 'Roll number and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find user by roll_no
        try:
            profile = StudentProfile.objects.get(roll_no=roll_no)
            user = profile.user
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'Invalid roll number or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Authenticate
        authenticated_user = authenticate(username=user.username, password=password)
        if authenticated_user:
            login(request, authenticated_user)
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': profile.full_name,
                    'roll_no': profile.roll_no,
                    'phone': profile.phone,
                    'course': profile.course,
                    'year': profile.year
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid roll number or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Logout the current user"""
        logout(request)
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """User profile management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get current user profile"""
        user = get_user_from_request(request)
        if not user:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            profile = user.student_profile
            serializer = StudentProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request):
        """Update user profile"""
        user = get_user_from_request(request)
        if not user:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            profile = user.student_profile
            
            # Update allowed fields
            if 'full_name' in request.data:
                profile.full_name = request.data['full_name']
            if 'phone' in request.data:
                profile.phone = request.data['phone']
            if 'email' in request.data:
                profile.email = request.data['email']
                user.email = request.data['email']
                user.save()
            
            profile.save()
            serializer = StudentProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ChatHistoryView(APIView):
    """Chat history management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get chat history for a user"""
        user = get_user_from_request(request)
        email = request.query_params.get('email')
        
        if user:
            # Get history by user
            history = ChatHistory.objects.filter(user=user).order_by('timestamp')
        elif email:
            # Fallback: get by email
            try:
                user = User.objects.get(email=email)
                history = ChatHistory.objects.filter(user=user).order_by('timestamp')
            except User.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
        else:
            return Response([], status=status.HTTP_200_OK)
        
        serializer = ChatHistorySerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatMessageView(APIView):
    """Send chat messages and get AI responses"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Process a chat message and return AI response"""
        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id', '')
        
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = get_user_from_request(request)
        
        try:
            # Import the chat router
            from .chat_router import chat_reply
            
            # Get AI response with details
            response_text, intent, confidence_score, source_details = chat_reply(
                message, user, return_details=True
            )
            
            # Save chat history
            chat = ChatHistory.objects.create(
                user=user,
                message=message,
                response=response_text,
                sender='assistant',
                intent=intent,
                confidence_score=confidence_score,
                source_details=source_details,
                session_id=session_id
            )
            
            return Response({
                'message': response_text,
                'response': response_text,
                'chat_id': chat.id,
                'intent': intent,
                'confidence_score': confidence_score,
                'source': intent,
                'source_details': source_details
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error processing chat message: {str(e)}")
            return Response(
                {'error': f'Failed to process message: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeedbackView(APIView):
    """Feedback management for chat responses"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Submit feedback for a chat response"""
        chat_id = request.data.get('chat_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not chat_id or not rating:
            return Response(
                {'error': 'chat_id and rating are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if rating not in ['helpful', 'not_helpful']:
            return Response(
                {'error': "Rating must be 'helpful' or 'not_helpful'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            chat = ChatHistory.objects.get(id=chat_id)
        except ChatHistory.DoesNotExist:
            return Response(
                {'error': 'Chat not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = get_user_from_request(request)
        
        # Create or update feedback
        feedback, created = Feedback.objects.update_or_create(
            chat_history=chat,
            user=user,
            defaults={'rating': rating, 'comment': comment}
        )
        
        return Response({
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback.id
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class SavedAnswersView(APIView):
    """Saved answers management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get all saved answers for a user"""
        user = get_user_from_request(request)
        if not user:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get saved chats
        saved_chats = ChatHistory.objects.filter(user=user, is_saved=True).order_by('-timestamp')
        serializer = ChatHistorySerializer(saved_chats, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Save a chat answer"""
        chat_id = request.data.get('chat_id')
        if not chat_id:
            return Response(
                {'error': 'chat_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            chat = ChatHistory.objects.get(id=chat_id)
            chat.is_saved = True
            chat.save()
            return Response({
                'message': 'Answer saved successfully'
            }, status=status.HTTP_200_OK)
        except ChatHistory.DoesNotExist:
            return Response(
                {'error': 'Chat not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request):
        """Remove a saved answer"""
        chat_id = request.data.get('chat_id')
        if not chat_id:
            return Response(
                {'error': 'chat_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            chat = ChatHistory.objects.get(id=chat_id)
            chat.is_saved = False
            chat.save()
            return Response({
                'message': 'Answer unsaved successfully'
            }, status=status.HTTP_200_OK)
        except ChatHistory.DoesNotExist:
            return Response(
                {'error': 'Chat not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserSettingsView(APIView):
    """User settings (dark mode, notifications, etc.)"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get user settings"""
        user = get_user_from_request(request)
        if not user:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or create settings
        settings, created = UserSettings.objects.get_or_create(user=user)
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Update user settings"""
        user = get_user_from_request(request)
        if not user:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        settings, created = UserSettings.objects.get_or_create(user=user)
        
        # Update settings
        if 'dark_mode' in request.data:
            settings.dark_mode = request.data['dark_mode']
        if 'push_notifications_enabled' in request.data:
            settings.push_notifications_enabled = request.data['push_notifications_enabled']
        if 'voice_enabled' in request.data:
            settings.voice_enabled = request.data['voice_enabled']
        
        settings.save()
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SearchView(APIView):
    """Search across chat history, documents, and knowledge base"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Search for content"""
        keyword = request.query_params.get('keyword', '').strip()
        search_type = request.query_params.get('type', 'all')
        
        if not keyword:
            return Response(
                {'error': 'Search keyword is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = get_user_from_request(request)
        results = {
            'chat_results': [],
            'kb_results': [],
        }
        
        # Search chat history
        if search_type in ['all', 'chat']:
            chat_query = ChatHistory.objects.filter(
                Q(message__icontains=keyword) | Q(response__icontains=keyword)
            )
            if user:
                chat_query = chat_query.filter(user=user)
            chat_query = chat_query[:20]
            results['chat_results'] = ChatHistorySerializer(chat_query, many=True).data
        
        # Search knowledge base
        if search_type in ['all', 'kb']:
            kb_query = KnowledgeBase.objects.filter(
                Q(question__icontains=keyword) | Q(answer__icontains=keyword),
                approved=True
            )[:20]
            results['kb_results'] = KnowledgeBaseSerializer(kb_query, many=True).data
        
        return Response(results, status=status.HTTP_200_OK)


class ImageQueryView(APIView):
    """Process image queries with AI"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Process an uploaded image with optional text query
        
        Accepts either:
        1. FormData with 'image' file field (traditional upload)
        2. JSON with 'image_base64' field (base64 encoded image for mobile compatibility)
        """
        query_text = request.data.get('query_text', '')
        user = get_user_from_request(request)
        
        # Check for base64 image first (mobile compatibility)
        image_base64 = request.data.get('image_base64')
        mime_type = request.data.get('mime_type', 'image/jpeg')
        
        # Also check for FormData file upload
        image_file = request.FILES.get('image')
        
        if not image_base64 and not image_file:
            return Response(
                {'error': 'No image provided. Send either image_base64 or image file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            import tempfile
            import os as temp_os
            
            temp_path = None
            
            if image_base64:
                # Handle base64 image from mobile
                try:
                    # Decode base64
                    import base64 as b64
                    image_data = b64.b64decode(image_base64)
                    
                    # Determine file extension from mime type
                    ext_map = {
                        'image/jpeg': '.jpg',
                        'image/jpg': '.jpg',
                        'image/png': '.png',
                        'image/gif': '.gif',
                        'image/webp': '.webp',
                    }
                    ext = ext_map.get(mime_type.lower(), '.jpg')
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                        tmp_file.write(image_data)
                        temp_path = tmp_file.name
                    
                    print(f"Saved base64 image to: {temp_path} (size: {len(image_data)} bytes)")
                    
                    # Create ImageQuery record (without file, just track the query)
                    image_query = ImageQuery.objects.create(
                        user=user,
                        query_text=query_text
                    )
                    
                    # Use the temp file path for analysis
                    image_path = temp_path
                    
                except Exception as decode_error:
                    print(f"Error decoding base64 image: {decode_error}")
                    return Response(
                        {'error': f'Failed to decode base64 image: {str(decode_error)}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Handle traditional file upload
                image_query = ImageQuery.objects.create(
                    user=user,
                    image=image_file,
                    query_text=query_text
                )
                image_path = image_query.image.path
            
            # Analyze image with Gemini Vision
            try:
                from .ai_service import analyze_image_with_gemini
                
                result = analyze_image_with_gemini(image_path, query_text)
                
                # Check if Gemini returned a skip response (image not related to system prompt)
                if result.get('skip', False):
                    # Image is not related to college/education content - skip it
                    image_query.ai_response = "Image not related to college/education content"
                    image_query.confidence_score = 0.0
                    image_query.save()
                    
                    # Clean up temp file if used
                    if temp_path and temp_os.path.exists(temp_path):
                        temp_os.unlink(temp_path)
                    
                    return Response({
                        'message': 'Image not related to college/education content',
                        'skipped': True,
                        'ai_response': None,
                        'confidence_score': 0.0,
                        'image_query_id': image_query.id,
                    }, status=status.HTTP_200_OK)
                
                ai_response = result.get('response', 'I received your image.')
                confidence_score = result.get('confidence', 50.0)
                success = result.get('success', False)
                
                if not success:
                    print(f"Image analysis error: {result.get('error')}")
                
            except Exception as e:
                print(f"Error importing/calling image analysis: {str(e)}")
                ai_response = "I received your image but couldn't analyze it. Please describe what you need help with."
                confidence_score = 30.0
            
            # Update the image query with AI response
            image_query.ai_response = ai_response
            image_query.confidence_score = confidence_score
            image_query.save()
            
            # Clean up temp file if used
            if temp_path and temp_os.path.exists(temp_path):
                temp_os.unlink(temp_path)
            
            return Response({
                'message': 'Image processed successfully',
                'ai_response': ai_response,
                'confidence_score': confidence_score,
                'image_query_id': image_query.id,
                'source': 'ai',
                'skipped': False
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            # Clean up temp file if error
            if 'temp_path' in locals() and temp_path and temp_os.path.exists(temp_path):
                temp_os.unlink(temp_path)
            return Response(
                {'error': f'Failed to process image: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationView(APIView):
    """User notifications management"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get notifications for a user"""
        user = get_user_from_request(request)
        if not user:
            return Response([], status=status.HTTP_200_OK)
        
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        
        notifications = Notification.objects.filter(user=user)
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        notifications = notifications.order_by('-created_at')[:50]
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Mark notifications as read"""
        user = get_user_from_request(request)
        if not user:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        notification_id = request.data.get('notification_id')
        mark_all = request.data.get('mark_all', False)
        
        if mark_all:
            Notification.objects.filter(user=user, is_read=False).update(is_read=True)
            return Response({'message': 'All notifications marked as read'}, status=status.HTTP_200_OK)
        elif notification_id:
            try:
                notification = Notification.objects.get(id=notification_id, user=user)
                notification.is_read = True
                notification.save()
                return Response({'message': 'Notification marked as read'}, status=status.HTTP_200_OK)
            except Notification.DoesNotExist:
                return Response(
                    {'error': 'Notification not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {'error': 'notification_id or mark_all is required'},
                status=status.HTTP_400_BAD_REQUEST
            )


class VoiceToTextView(APIView):
    """Convert voice/audio to text using speech recognition"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Convert audio file to text"""
        try:
            audio_file = request.FILES.get('audio')
            if not audio_file:
                return Response(
                    {"error": "No audio file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save audio file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as tmp_file:
                for chunk in audio_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            try:
                # Try using speech_recognition library
                import speech_recognition as sr
                
                r = sr.Recognizer()
                
                # Convert audio format if needed
                audio_format = audio_file.name.split('.')[-1].lower()
                
                # Use speech_recognition to transcribe
                with sr.AudioFile(tmp_path) as source:
                    audio_data = r.record(source)
                
                # Try Google Speech Recognition (free, no API key needed for limited use)
                try:
                    text = r.recognize_google(audio_data, language='en-US')
                except sr.UnknownValueError:
                    return Response(
                        {"error": "Could not understand audio. Please speak clearly."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                except sr.RequestError as e:
                    # Fallback: return a placeholder message
                    return Response(
                        {"error": "Speech recognition service unavailable. Please type your message."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )
                
                return Response({
                    "text": text,
                    "message": "Audio transcribed successfully"
                }, status=status.HTTP_200_OK)
                
            except ImportError:
                # If speech_recognition is not installed, provide helpful error
                return Response(
                    {"error": "Speech recognition library not installed. Please install: pip install SpeechRecognition pydub"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            except Exception as e:
                return Response(
                    {"error": f"Error processing audio: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            return Response(
                {"error": f"Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
