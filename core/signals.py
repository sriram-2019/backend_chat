"""
Django signals for auto-rebuilding KB cache when entries change.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import KnowledgeBase
from .kb_cache import rebuild_kb_cache


@receiver(post_save, sender=KnowledgeBase)
def kb_entry_saved(sender, instance, created, **kwargs):
    """Rebuild cache when KB entry is saved"""
    # Only rebuild if entry is approved (or was just approved)
    if instance.approved:
        print(f"KB entry {instance.id} saved/updated. Rebuilding cache...")
        try:
            rebuild_kb_cache()
            print("KB cache rebuilt successfully")
        except Exception as e:
            print(f"Error rebuilding KB cache: {str(e)}")


@receiver(post_delete, sender=KnowledgeBase)
def kb_entry_deleted(sender, instance, **kwargs):
    """Rebuild cache when KB entry is deleted"""
    print(f"KB entry {instance.id} deleted. Rebuilding cache...")
    try:
        rebuild_kb_cache()
        print("KB cache rebuilt successfully")
    except Exception as e:
        print(f"Error rebuilding KB cache: {str(e)}")

