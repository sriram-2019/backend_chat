# INTELLIQ SHC Backend

Django REST Framework backend for INTELLIQ SHC Smart Student Assistant.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Authentication
- `POST /api/register/` - Register a new user
- `POST /api/login/` - Login user
- `POST /api/logout/` - Logout user

### User Profile
- `GET /api/profile/` - Get current user profile

### Chat
- `POST /api/chat/message/` - Send a message and get AI response
- `GET /api/chat/history/` - Get chat history
- `POST /api/chat/history/` - Create a chat message

### Feedback
- `POST /api/feedback/` - Submit feedback for a chat

### Saved Answers
- `GET /api/saved/` - Get all saved answers
- `POST /api/saved/` - Save an answer
- `DELETE /api/saved/` - Unsave an answer

