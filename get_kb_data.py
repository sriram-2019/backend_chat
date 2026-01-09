"""
Script to retrieve and display all Knowledge Base entries from database
Run: python manage.py shell < get_kb_data.py
Or: python get_kb_data.py (if Django is set up)
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from core.models import KnowledgeBase

def display_all_kb():
    """Display all Knowledge Base entries"""
    print("=" * 80)
    print("KNOWLEDGE BASE ENTRIES")
    print("=" * 80)
    
    all_kb = KnowledgeBase.objects.all().order_by('id')
    total = all_kb.count()
    approved = KnowledgeBase.objects.filter(approved=True).count()
    
    print(f"\nTotal KB Entries: {total}")
    print(f"Approved Entries: {approved}")
    print(f"Pending Entries: {total - approved}")
    print("\n" + "=" * 80)
    
    if total == 0:
        print("No Knowledge Base entries found in database.")
        return
    
    for idx, entry in enumerate(all_kb, 1):
        print(f"\n[{idx}] Entry ID: {entry.id}")
        print(f"    Question: {entry.question}")
        print(f"    Answer: {entry.answer[:100]}{'...' if len(entry.answer) > 100 else ''}")
        print(f"    Category: {entry.type}")
        print(f"    Approved: {'YES' if entry.approved else 'NO'}")
        if entry.approved_by:
            print(f"    Approved By: {entry.approved_by.username}")
        if entry.created_by:
            print(f"    Created By: {entry.created_by.username}")
        print(f"    Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Updated: {entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
    
    print("\n" + "=" * 80)
    print("SUMMARY BY CATEGORY")
    print("=" * 80)
    
    from django.db.models import Count
    category_counts = KnowledgeBase.objects.values('type').annotate(count=Count('id')).order_by('-count')
    
    for cat in category_counts:
        approved_in_cat = KnowledgeBase.objects.filter(type=cat['type'], approved=True).count()
        print(f"{cat['type'].upper():15} : Total={cat['count']:3} | Approved={approved_in_cat:3}")
    
    print("\n" + "=" * 80)
    print("APPROVED ENTRIES ONLY (for matching)")
    print("=" * 80)
    
    approved_kb = KnowledgeBase.objects.filter(approved=True).order_by('id')
    print(f"\nTotal Approved: {approved_kb.count()}\n")
    
    for idx, entry in enumerate(approved_kb, 1):
        print(f"[{idx}] KB_{entry.id:03d} | {entry.type:10} | {entry.question[:60]}...")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        display_all_kb()
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

