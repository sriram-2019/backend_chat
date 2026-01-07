from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from .models import StudentProfile, ChatHistory, Feedback, UnsolvedQuestion
from .serializers import (
    UserSerializer,
    StudentProfileSerializer,
    UserRegisterSerializer,
    ChatHistorySerializer,
    ChatHistoryCreateSerializer,
    FeedbackSerializer
)

class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Log received data for debugging
        print(f"Received registration data: {request.data}")
        
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                # Get profile
                try:
                    profile = StudentProfile.objects.get(user=user)
                    profile_data = StudentProfileSerializer(profile).data
                except StudentProfile.DoesNotExist:
                    profile_data = None
                
                return Response({
                    "message": "Account created successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.get_full_name() or user.username
                    },
                    "profile": profile_data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                import traceback
                print(f"Error in registration: {str(e)}")
                print(traceback.format_exc())
                return Response({
                    "error": str(e),
                    "details": "An error occurred while creating the account. Please check all fields are filled correctly."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                import traceback
                print(f"Error creating user: {str(e)}")
                print(traceback.format_exc())
                return Response({
                    "error": str(e),
                    "details": "An error occurred while creating the account"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log validation errors
        print(f"Validation errors: {serializer.errors}")
        return Response({
            "error": "Validation failed",
            "errors": serializer.errors,
            "received_data": request.data
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        roll_no = request.data.get('roll_no', '')
        
        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Authenticate user
        user = authenticate(username=user.username, password=password)
        if not user:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Optional: Verify roll number if provided
        if roll_no:
            try:
                profile = StudentProfile.objects.get(user=user, roll_no=roll_no)
            except StudentProfile.DoesNotExist:
                return Response(
                    {"error": "Roll number does not match this account"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Login user
        login(request, user)
        
        # Get student profile
        try:
            profile = StudentProfile.objects.get(user=user)
            profile_data = StudentProfileSerializer(profile).data
            # Ensure profile data is saved to localStorage
        except StudentProfile.DoesNotExist:
            profile_data = None
        
        return Response({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.get_full_name() or user.username
            },
            "profile": profile_data
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = StudentProfile.objects.get(user=request.user)
            serializer = StudentProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StudentProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class ChatHistoryView(APIView):
    permission_classes = [AllowAny]  # Changed to AllowAny for now
    
    def get(self, request):
        """Get chat history for the authenticated user"""
        # Get user from session if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # If not authenticated, try to get user from query params or request data
        if not user:
            user_id = request.query_params.get('user_id') or request.data.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass
        
        # If still no user, try to get from email/username in localStorage
        if not user:
            email = request.query_params.get('email')
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    pass
        
        if user:
            # Filter chat history for this specific user only
            chats = ChatHistory.objects.filter(user=user).order_by('timestamp')  # Oldest first
            serializer = ChatHistorySerializer(chats, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Return empty if no user found
            return Response([], status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create a new chat message"""
        serializer = ChatHistoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            chat = serializer.save(user=request.user)
            response_serializer = ChatHistorySerializer(chat)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatMessageView(APIView):
    permission_classes = [AllowAny]  # Changed to AllowAny for now, can be changed back to IsAuthenticated
    
    def post(self, request):
        """Send a message and get AI response"""
        message = request.data.get('message')
        session_id = request.data.get('session_id', '')
        
        if not message:
            return Response(
                {"error": "Message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user from session if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # If not authenticated, try to get user from request data
        if not user:
            user_id = request.data.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass
            
            # Try email if user_id not found
            if not user:
                email = request.data.get('email')
                if email:
                    try:
                        user = User.objects.get(email=email)
                    except User.DoesNotExist:
                        pass
        
        try:
            # Import AI service
            from .ai_service import get_hybrid_response
            
            # Save user message first
            user_message = ChatHistory.objects.create(
                user=user,
                message=message,
                sender='user',
                session_id=session_id
            )
            
            # Get AI response using hybrid approach (KB + Gemini)
            response_text, intent = get_hybrid_response(
                user_text=message,
                user=user
            )
            
            # Save AI response
            assistant_entry = ChatHistory.objects.create(
                user=user,
                message=message,
                response=response_text,
                sender='assistant',
                intent=intent,
                session_id=session_id
            )
            
            return Response({
                "message": response_text,
                "response": response_text,  # For compatibility
                "chat_id": assistant_entry.id,
                "session_id": session_id,
                "intent": intent
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            print(f"Error in ChatMessageView: {str(e)}")
            print(traceback.format_exc())
            
            # Save error message
            error_response = f"Sorry, I encountered an error processing your message. Please try again."
            error_entry = ChatHistory.objects.create(
                user=user,
                message=message,
                response=error_response,
                sender='assistant',
                intent='error',
                session_id=session_id
            )
            
            return Response({
                "message": error_response,
                "response": error_response,
                "chat_id": error_entry.id,
                "session_id": session_id,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FeedbackView(APIView):
    permission_classes = [AllowAny]  # Changed to AllowAny to match chat endpoint
    
    def post(self, request):
        chat_id = request.data.get('chat_id')
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')
        
        if not chat_id or not rating:
            return Response(
                {"error": "chat_id and rating are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user from session if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # Get chat entry
        try:
            chat = ChatHistory.objects.get(id=chat_id)
        except ChatHistory.DoesNotExist:
            return Response(
                {"error": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # If user is authenticated, verify chat belongs to them
        # If not authenticated, use the chat's user (for compatibility)
        if user:
            if chat.user != user:
                return Response(
                    {"error": "You can only provide feedback on your own chats"},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Use chat's user if not authenticated
            user = chat.user
            if not user:
                return Response(
                    {"error": "User authentication required"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        feedback = Feedback.objects.create(
            chat_history=chat,
            user=user,
            rating=rating,
            comment=comment
        )
        
        # If feedback is "not_helpful", create unsolved question
        if rating == 'not_helpful':
            UnsolvedQuestion.objects.get_or_create(
                chat_history=chat,
                defaults={
                    'user': user,
                    'question': chat.message,
                    'status': 'pending'
                }
            )
        
        serializer = FeedbackSerializer(feedback)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SavedAnswersView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all saved answers for the user"""
        saved_chats = ChatHistory.objects.filter(
            user=request.user,
            is_saved=True
        ).order_by('-timestamp')
        
        serializer = ChatHistorySerializer(saved_chats, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Save a chat answer"""
        chat_id = request.data.get('chat_id')
        
        if not chat_id:
            return Response(
                {"error": "chat_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            chat = ChatHistory.objects.get(id=chat_id, user=request.user)
            chat.is_saved = True
            chat.save()
            return Response({"message": "Answer saved successfully"}, status=status.HTTP_200_OK)
        except ChatHistory.DoesNotExist:
            return Response(
                {"error": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request):
        """Unsave a chat answer"""
        chat_id = request.data.get('chat_id')
        
        if not chat_id:
            return Response(
                {"error": "chat_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            chat = ChatHistory.objects.get(id=chat_id, user=request.user)
            chat.is_saved = False
            chat.save()
            return Response({"message": "Answer unsaved successfully"}, status=status.HTTP_200_OK)
        except ChatHistory.DoesNotExist:
            return Response(
                {"error": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND
            )

