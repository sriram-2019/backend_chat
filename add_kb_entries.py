"""
Script to add Knowledge Base entries to the database.
Run this from the backend directory: python add_kb_entries.py
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from core.models import KnowledgeBase

# Knowledge Base entries to add
kb_entries = [
    {
        "question": "What is the minimum attendance required?",
        "answer": "Students must maintain a minimum of 75% attendance in each subject to be eligible for semester examinations.",
        "category": "Rules",
        "department": None,
        "course": None,
        "is_active": True
    },
    {
        "question": "Is there a dress code for students?",
        "answer": "Yes. Students are required to follow the college dress code during all working days. Casual or inappropriate attire is not permitted.",
        "category": "Rules",
        "department": None,
        "course": None,
        "is_active": True
    },
    {
        "question": "What subjects are included in BSc Computer Science semester 1?",
        "answer": "Semester 1 includes Programming Fundamentals, Mathematics, Digital Electronics, and Environmental Studies.",
        "category": "Syllabus",
        "department": "Computer Science",
        "course": "BSc",
        "is_active": True
    },
    {
        "question": "What is the syllabus for Programming Fundamentals?",
        "answer": "The syllabus includes introduction to programming, data types, control structures, functions, and basic problem-solving techniques.",
        "category": "Syllabus",
        "department": "Computer Science",
        "course": "BSc",
        "is_active": True
    }
]

def add_kb_entries():
    """Add Knowledge Base entries to the database"""
    
    # Map category to type
    category_to_type = {
        "Rules": "rule",
        "Syllabus": "syllabus",
        "Exam": "exam",
        "FAQ": "faq",
        "General": "general"
    }
    
    # Get or create a default admin user for created_by and approved_by
    admin_user = None
    try:
        # Try to get first admin user
        from core.models import AdminProfile
        admin_profile = AdminProfile.objects.first()
        if admin_profile:
            admin_user = admin_profile.user
    except:
        pass
    
    # If no admin, try to get first superuser
    if not admin_user:
        admin_user = User.objects.filter(is_superuser=True).first()
    
    # If still no admin, create a system user (or use first user)
    if not admin_user:
        admin_user = User.objects.first()
    
    added_count = 0
    skipped_count = 0
    
    print("Adding Knowledge Base entries...")
    print("-" * 60)
    
    for entry_data in kb_entries:
        question = entry_data["question"]
        answer = entry_data["answer"]
        category = entry_data["category"]
        is_active = entry_data.get("is_active", True)
        
        # Map category to type
        kb_type = category_to_type.get(category, "general")
        
        # Check if entry already exists
        existing = KnowledgeBase.objects.filter(question=question).first()
        if existing:
            print(f"[SKIP] Already exists: {question[:50]}...")
            skipped_count += 1
            continue
        
        # Create KB entry
        kb_entry = KnowledgeBase.objects.create(
            question=question,
            answer=answer,
            type=kb_type,
            approved=is_active,  # is_active maps to approved
            created_by=admin_user,
            approved_by=admin_user if is_active else None,
            approved_at=timezone.now() if is_active else None
        )
        
        print(f"[OK] Added: {question[:50]}...")
        print(f"     Type: {kb_type}, Approved: {is_active}")
        added_count += 1
    
    print("-" * 60)
    print(f"\n[SUCCESS] Added {added_count} entries")
    if skipped_count > 0:
        print(f"[INFO] Skipped {skipped_count} entries (already exist)")
    print(f"\nTotal Knowledge Base entries: {KnowledgeBase.objects.count()}")
    print(f"Approved entries: {KnowledgeBase.objects.filter(approved=True).count()}")

if __name__ == "__main__":
    add_kb_entries()

