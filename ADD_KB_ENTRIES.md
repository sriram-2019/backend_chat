# How to Add Knowledge Base Entries

## Quick Method: Using the Script

1. **Edit the script:**
   - Open `backend/add_kb_entries.py`
   - Add your entries to the `kb_entries` list

2. **Run the script:**
   ```bash
   cd backend
   python add_kb_entries.py
   ```

## Entry Format

```python
{
    "question": "Your question here?",
    "answer": "Your answer here.",
    "category": "Rules" | "Syllabus" | "Exam" | "FAQ" | "General",
    "department": "Computer Science" | None,  # Optional
    "course": "BSc" | None,  # Optional
    "is_active": True  # True = approved, False = pending
}
```

## Category Mapping

- `"Rules"` → `type: "rule"`
- `"Syllabus"` → `type: "syllabus"`
- `"Exam"` → `type: "exam"`
- `"FAQ"` → `type: "faq"`
- `"General"` → `type: "general"`

## Alternative: Using Admin Interface

1. Login as admin: `http://localhost:3000/admin/login`
2. Go to Knowledge Base: `http://localhost:3000/admin/knowledge-base`
3. Click "Add FAQ"
4. Fill in the form and click "Create Entry"
5. **Important:** Click the Approve button (✅) to activate it

## Alternative: Using Django Shell

```python
python manage.py shell
```

```python
from core.models import KnowledgeBase
from django.contrib.auth.models import User
from django.utils import timezone

# Get admin user
admin = User.objects.filter(is_superuser=True).first()

# Create entry
kb = KnowledgeBase.objects.create(
    question="What is the minimum attendance required?",
    answer="Students must maintain a minimum of 75% attendance.",
    type="rule",
    approved=True,
    created_by=admin,
    approved_by=admin,
    approved_at=timezone.now()
)
```

