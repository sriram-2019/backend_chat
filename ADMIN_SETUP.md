# Admin Panel Setup Guide

## Overview

A complete admin panel has been created with separate pages for managing the INTELLIQ SHC system. The admin panel uses the same backend but has its own authentication and interface.

## Admin Features

### 1. **Admin Authentication**
- Separate login page at `/admin/login`
- Admin registration endpoint
- Role-based access control

### 2. **Admin Dashboard** (`/admin/dashboard`)
- Overview statistics:
  - Total Students
  - Total Questions
  - Unsolved Questions
  - Documents Count
  - Knowledge Base Entries
- Recent questions display
- Recent unsolved questions

### 3. **Analytics Page** (`/admin/analytics`)
- System performance metrics
- Daily statistics breakdown
- Questions, KB matches, AI fallbacks
- Feedback statistics
- Customizable date range (7, 30, 90 days)

### 4. **Unsolved Questions** (`/admin/unsolved`)
- View pending/resolved/archived questions
- Resolve questions with answers
- Option to add resolved answers to Knowledge Base
- Filter by status

### 5. **Documents Management** (`/admin/documents`)
- Upload college documents (Syllabus, Exam Info, Rules)
- View all uploaded documents
- Document metadata management
- File upload support

## Database Models Added

1. **AdminProfile** - Admin user profiles
2. **UnsolvedQuestion** - Track unanswered questions
3. **Document** - Store uploaded documents
4. **Analytics** - System analytics data

## API Endpoints

### Admin Authentication
- `POST /api/admin/register/` - Register new admin
- `POST /api/admin/login/` - Admin login

### Admin Dashboard
- `GET /api/admin/dashboard/` - Get dashboard stats

### Analytics
- `GET /api/admin/analytics/?days=30` - Get analytics data

### Unsolved Questions
- `GET /api/admin/unsolved/?status=pending` - Get unsolved questions
- `POST /api/admin/unsolved/` - Resolve a question

### Documents
- `GET /api/admin/documents/` - Get all documents
- `POST /api/admin/documents/` - Upload document

## Setup Steps

### 1. Run Migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 2. Create First Admin Account

You can create an admin account through:
- Django admin panel (`/admin/`)
- Admin registration API endpoint
- Or manually create via Django shell:

```python
from django.contrib.auth.models import User
from core.models import AdminProfile

user = User.objects.create_user(
    username='admin',
    email='admin@college.edu',
    password='admin123',
    is_staff=True
)

AdminProfile.objects.create(
    user=user,
    full_name='Admin User',
    email='admin@college.edu',
    department='IT'
)
```

### 3. Access Admin Panel

1. Go to `http://localhost:3000/admin/login`
2. Login with admin credentials
3. Access dashboard and other admin features

## Features Matching Flowchart

✅ **Admin Dashboard** - Central hub for admin operations
✅ **View Analytics** - System performance metrics
✅ **Manage College Data** - Through Knowledge Base and Documents
✅ **Upload Documents** - Document management system
✅ **View Unsolved Questions** - Track and resolve unanswered questions
✅ **Resolve Questions** - Answer questions and add to KB
✅ **Store in Knowledge Base** - Automatic KB updates

## Notes

- Admin users are separate from student users
- Admin authentication uses the same session system
- All admin endpoints check for admin role
- Unsolved questions are automatically created when feedback is "not_helpful"
- Documents can be uploaded (file storage needs to be configured for production)

## Next Steps (Optional)

1. **File Storage**: Configure proper file storage (AWS S3, local storage, etc.)
2. **Document Processing**: Add text extraction from PDFs for Knowledge Base
3. **Advanced Analytics**: Add charts and graphs
4. **Bulk Operations**: Add bulk question resolution
5. **Email Notifications**: Notify admins of new unsolved questions

