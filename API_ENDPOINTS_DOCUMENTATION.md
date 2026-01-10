# INTELLIQ SHC API Endpoints Documentation

**Base URL:** `https://chatbackend1.pythonanywhere.com`  
**API Base:** `https://chatbackend1.pythonanywhere.com/api`

## API Status

✅ **API is running and accessible**

Root endpoint returns:
```json
{
  "message": "INTELLIQ SHC API is running",
  "status": "ok",
  "version": "1.0",
  "endpoints": {
    "api": "/api/",
    "admin": "/admin/",
    "login": "/api/login/",
    "register": "/api/register/"
  }
}
```

---

## Authentication Endpoints

### 1. Student Registration
**POST** `/api/register/`

**Request Body:**
```json
{
  "username": "string (optional, defaults to email prefix)",
  "email": "string (required)",
  "password": "string (required, min 8 chars)",
  "password_confirm": "string (required, must match password)",
  "full_name": "string (required)",
  "roll_no": "string (required, unique)",
  "phone": "string (required, max 15 chars)",
  "course": "string (required)",
  "year": "string (required)"
}
```

**Response (201 Created):**
```json
{
  "message": "Account created successfully",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User"
  },
  "profile": {
    "id": 1,
    "full_name": "Test User",
    "roll_no": "TEST001",
    "email": "test@example.com",
    "phone": "1234567890",
    "course": "Computer Science",
    "year": "1st Year"
  }
}
```

---

### 2. Student Login
**POST** `/api/login/`

**Request Body:**
```json
{
  "email": "string (required)",
  "password": "string (required)",
  "roll_no": "string (optional)"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "token": "jwt_token_here",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User"
  },
  "profile": {
    "id": 1,
    "roll_no": "TEST001",
    "course": "Computer Science",
    "year": "1st Year"
  }
}
```

**Note:** Token should be included in subsequent requests as:
```
Authorization: Bearer <token>
```

---

### 3. Student Logout
**POST** `/api/logout/`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

---

## User Profile Endpoints

### 4. Get User Profile
**GET** `/api/profile/`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "",
    "last_name": ""
  },
  "full_name": "Test User",
  "roll_no": "TEST001",
  "email": "test@example.com",
  "phone": "1234567890",
  "course": "Computer Science",
  "year": "1st Year",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

## Chat Endpoints

### 5. Send Chat Message
**POST** `/api/chat/message/`

**Request Body:**
```json
{
  "message": "string (required)",
  "session_id": "string (optional)",
  "user_id": "integer (optional)",
  "email": "string (optional)"
}
```

**Response (200 OK):**
```json
{
  "message": "User message",
  "response": "AI response",
  "chat_id": 1,
  "session_id": "session_123",
  "intent": "question"
}
```

**Note:** Currently returns 500 error due to Google AI import issue on server.

---

### 6. Get Chat History
**GET** `/api/chat/history/`

**Query Parameters (optional):**
- `user_id`: integer
- `email`: string

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "username": "testuser",
    "message": "Hello",
    "response": "Hi there!",
    "sender": "user",
    "intent": "greeting",
    "timestamp": "2024-01-01T00:00:00Z",
    "session_id": "session_123",
    "is_saved": false
  }
]
```

---

## Feedback Endpoints

### 7. Submit Feedback
**POST** `/api/feedback/`

**Request Body:**
```json
{
  "chat_id": "integer (required)",
  "rating": "string (required, 'helpful' or 'not_helpful')",
  "comment": "string (optional)"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "chat_history": 1,
  "rating": "helpful",
  "comment": "Great response!",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Saved Answers Endpoints

### 8. Get Saved Answers
**GET** `/api/saved/`

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "username": "testuser",
    "message": "Question",
    "response": "Answer",
    "sender": "user",
    "intent": "question",
    "timestamp": "2024-01-01T00:00:00Z",
    "session_id": "session_123",
    "is_saved": true
  }
]
```

### 9. Save Answer
**POST** `/api/saved/`

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "chat_id": "integer (required)"
}
```

**Response (200 OK):**
```json
{
  "message": "Answer saved successfully"
}
```

### 10. Unsave Answer
**DELETE** `/api/saved/`

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "chat_id": "integer (required)"
}
```

**Response (200 OK):**
```json
{
  "message": "Answer unsaved successfully"
}
```

---

## Public Knowledge Base Endpoints

### 11. Get Public Knowledge Base
**GET** `/api/knowledge-base/`

**Query Parameters (optional):**
- `approved`: boolean (default: true)
- `type`: string

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "question": "What is the exam schedule?",
    "answer": "Exams are scheduled for...",
    "type": "exam",
    "approved": true,
    "approved_at": "2024-01-01T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## Admin Endpoints

### 12. Admin Registration
**POST** `/api/admin/register/`

**Request Body:**
```json
{
  "username": "string (optional)",
  "email": "string (required)",
  "password": "string (required)",
  "full_name": "string (required)",
  "prof_id": "string (optional)",
  "phone": "string (optional)",
  "department": "string (optional)"
}
```

---

### 13. Admin Login
**POST** `/api/admin/login/`

**Request Body:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response (200 OK):**
```json
{
  "message": "Admin login successful",
  "token": "admin_jwt_token_here",
  "admin": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User"
  }
}
```

---

### 14. Admin Dashboard
**GET** `/api/admin/dashboard/`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters (optional):**
- `user_id`: integer

---

### 15. Admin Analytics
**GET** `/api/admin/analytics/`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters (optional):**
- `days`: integer (default: 30)

---

### 16. Admin Unsolved Questions
**GET** `/api/admin/unsolved/`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters (optional):**
- `status`: string (default: 'pending')

**POST** `/api/admin/unsolved/` - Resolve Question

**Request Body:**
```json
{
  "question_id": "integer (required)",
  "resolved_answer": "string (required)",
  "add_to_kb": "boolean (optional, default: false)"
}
```

---

### 17. Admin Documents
**GET** `/api/admin/documents/`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters (optional):**
- `type`: string

**POST** `/api/admin/documents/` - Upload Document

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data
```

**Request Body (FormData):**
- `file`: File (required)
- `title`: string (required)
- `document_type`: string (required)
- `description`: string (optional)

---

### 18. Admin List
**GET** `/api/admin/list/`

**Headers:**
```
Authorization: Bearer <admin_token>
```

---

### 19. Admin Rules Management
**GET** `/api/admin/rules/` - Get all rules

**POST** `/api/admin/rules/` - Create rule

**Request Body:**
```json
{
  "title": "string (required)",
  "rule_text": "string (required)",
  "applicability": "string (required)",
  "status": "string (optional)",
  "category": "string (optional)"
}
```

**PUT** `/api/admin/rules/<rule_id>/` - Update rule

**DELETE** `/api/admin/rules/<rule_id>/` - Delete rule

**Headers for all:**
```
Authorization: Bearer <admin_token>
```

---

### 20. Admin Syllabus Management
**GET** `/api/admin/syllabus/` - Get all syllabus

**Query Parameters (optional):**
- `course`: string
- `semester`: string

**POST** `/api/admin/syllabus/` - Create syllabus

**Request Body:**
```json
{
  "department": "string (required)",
  "course": "string (required)",
  "semester": "string (required)",
  "subject_code": "string (required)",
  "subject_name": "string (required)",
  "units": "string (required)",
  "credits": "integer (required)"
}
```

**PUT** `/api/admin/syllabus/<syllabus_id>/` - Update syllabus

**DELETE** `/api/admin/syllabus/<syllabus_id>/` - Delete syllabus

**Headers for all:**
```
Authorization: Bearer <admin_token>
```

---

### 21. Admin Exam Information Management
**GET** `/api/admin/exams/` - Get all exams

**Query Parameters (optional):**
- `course`: string
- `semester`: string

**POST** `/api/admin/exams/` - Create exam

**Request Body:**
```json
{
  "exam_name": "string (required)",
  "course": "string (required)",
  "semester": "string (required)",
  "exam_date": "string (required, ISO format)",
  "duration": "string (required)",
  "instructions": "string (required)",
  "venue": "string (optional)"
}
```

**PUT** `/api/admin/exams/<exam_id>/` - Update exam

**DELETE** `/api/admin/exams/<exam_id>/` - Delete exam

**Headers for all:**
```
Authorization: Bearer <admin_token>
```

---

### 22. Admin Knowledge Base Management
**GET** `/api/admin/knowledge-base/` - Get all KB entries

**Query Parameters (optional):**
- `approved`: boolean
- `type`: string

**POST** `/api/admin/knowledge-base/` - Create KB entry

**Request Body:**
```json
{
  "question": "string (required)",
  "answer": "string (required)",
  "type": "string (optional)"
}
```

**PUT** `/api/admin/knowledge-base/<kb_id>/` - Update KB entry

**DELETE** `/api/admin/knowledge-base/<kb_id>/` - Delete KB entry

**POST** `/api/admin/knowledge-base/<kb_id>/approve/` - Approve KB entry

**Headers for all:**
```
Authorization: Bearer <admin_token>
```

---

### 23. Admin Student Detail
**GET** `/api/admin/student/<username>/`

**Headers:**
```
Authorization: Bearer <admin_token>
```

---

### 24. Admin College Data
**GET** `/api/admin/college-data/`

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `type`: string (required)

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Error message",
  "errors": {
    "field_name": ["Error details"]
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid email or password"
}
```

### 403 Forbidden
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Error details"
}
```

---

## Testing Status

Based on automated testing:

✅ **Working Endpoints:**
- Root endpoint (`/`)
- Chat history (`/api/chat/history/`)
- Public knowledge base (`/api/knowledge-base/`)

⚠️ **Endpoints Requiring Authentication:**
- Profile (`/api/profile/`)
- Logout (`/api/logout/`)
- Saved answers (`/api/saved/`)
- All admin endpoints

❌ **Issues Found:**
- Register endpoint requires all fields (password_confirm, full_name, roll_no, phone, course, year)
- Login endpoint requires `email` (not `username`)
- Chat message endpoint has Google AI import error (500)
- Admin login requires `email` (not `username`)

---

## Integration Notes

1. **Base URL:** Use `https://chatbackend1.pythonanywhere.com/api` for all API calls
2. **Authentication:** Use Bearer token authentication for protected endpoints
3. **Login Format:** Use `email` and `password` (not `username`)
4. **Register Format:** Include all required fields including `password_confirm`
5. **CORS:** Backend should be configured to allow requests from your frontend domain

---

## Quick Reference

| Endpoint | Method | Auth Required | Status |
|----------|--------|----------------|--------|
| `/api/register/` | POST | No | ✅ |
| `/api/login/` | POST | No | ✅ |
| `/api/logout/` | POST | Yes | ⚠️ |
| `/api/profile/` | GET | Yes | ⚠️ |
| `/api/chat/message/` | POST | No | ❌ (500 error) |
| `/api/chat/history/` | GET | No | ✅ |
| `/api/feedback/` | POST | No | ⚠️ |
| `/api/saved/` | GET/POST/DELETE | Yes | ⚠️ |
| `/api/knowledge-base/` | GET | No | ✅ |
| `/api/admin/*` | Various | Yes | ⚠️ |

