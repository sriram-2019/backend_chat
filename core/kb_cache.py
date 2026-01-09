"""
Knowledge Base Cache Manager
Preprocesses and caches all approved KB entries for fast local matching.
"""
import json
import re
from typing import List, Dict, Set
from pathlib import Path
from django.core.cache import cache
from .models import KnowledgeBase

# Synonym mappings for keyword expansion
SYNONYM_MAP = {
    'hour': ['hour', 'hours', 'time', 'timing', 'schedule', 'when', 'timings', 'working time'],
    'working': ['working', 'operational', 'open', 'available', 'office'],
    'office': ['office', 'administration', 'admin', 'department', 'college office'],
    'attendance': ['attendance', 'presence', 'present', 'absent', 'absence', 'minimum attendance'],
    'dress': ['dress', 'clothing', 'uniform', 'attire', 'wear', 'dress code'],
    'code': ['code', 'rules', 'regulation', 'guidelines', 'policy', 'policies'],
    'syllabus': ['syllabus', 'syllabi', 'subjects', 'topics', 'content', 'courses', 'curriculum'],
    'subject': ['subject', 'subjects', 'course', 'courses', 'paper', 'papers'],
    'exam': ['exam', 'examination', 'test', 'tests', 'assessment', 'evaluation'],
    'required': ['required', 'minimum', 'needed', 'mandatory', 'compulsory'],
    'programming': ['programming', 'program', 'coding', 'code', 'software'],
    'fundamentals': ['fundamentals', 'basics', 'basic', 'intro', 'introduction'],
}

# Category tags for auto-tagging
CATEGORY_TAGS = {
    'faq': ['hour', 'time', 'working', 'office', 'contact', 'phone', 'email', 'when', 'timing'],
    'rule': ['attendance', 'dress', 'code', 'regulation', 'policy', 'required', 'minimum', 'must'],
    'syllabus': ['syllabus', 'subject', 'course', 'semester', 'unit', 'credit', 'topics'],
    'exam': ['exam', 'examination', 'test', 'internal', 'marks', 'grade', 'assessment'],
    'general': []
}

# Stop words to filter out
STOP_WORDS = {
    'what', 'is', 'are', 'the', 'a', 'an', 'for', 'of', 'in', 'on', 'at', 'to', 'and', 'or', 'but',
    'with', 'by', 'from', 'as', 'about', 'into', 'when', 'where', 'who', 'which', 'why', 'how',
    'this', 'that', 'there', 'can', 'could', 'should', 'would', 'may', 'might', 'must', 'will'
}


def normalize_text(text: str) -> str:
    """Normalize text: lowercase, remove punctuation, extra spaces"""
    if not text:
        return ""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    text = ' '.join(text.split())
    return text


def extract_keywords(text: str) -> Set[str]:
    """Extract meaningful keywords from text"""
    normalized = normalize_text(text)
    words = normalized.split()
    
    keywords = {w for w in words if len(w) > 2 and w not in STOP_WORDS}
    
    if not keywords:
        keywords = {w for w in words if len(w) > 2}
    
    return keywords


def expand_keywords(keywords: Set[str]) -> Set[str]:
    """Expand keywords with synonyms"""
    expanded = set(keywords)
    
    for keyword in keywords:
        for key, synonyms in SYNONYM_MAP.items():
            if keyword in synonyms or key in keyword:
                expanded.update(synonyms)
    
    return expanded


def auto_tag_entry(entry: Dict) -> Set[str]:
    """Auto-tag KB entry based on content and category"""
    tags = set()
    category = entry.get('category', '').lower()
    
    # Add category-specific tags
    if category in CATEGORY_TAGS:
        tags.update(CATEGORY_TAGS[category])
    
    # Extract keywords from question and answer
    question_keywords = extract_keywords(entry.get('question', ''))
    answer_keywords = extract_keywords(entry.get('answer', ''))
    all_keywords = question_keywords | answer_keywords
    
    # Match keywords to tags
    for keyword in all_keywords:
        for tag_key, tag_synonyms in CATEGORY_TAGS.items():
            if keyword in tag_synonyms or any(tag in keyword for tag in tag_synonyms):
                tags.add(tag_key)
    
    return tags


def preprocess_kb_entry(entry: KnowledgeBase) -> Dict:
    """Preprocess a single KB entry for caching"""
    question_norm = normalize_text(entry.question)
    answer_norm = normalize_text(entry.answer)
    
    question_keywords = extract_keywords(entry.question)
    answer_keywords = extract_keywords(entry.answer)
    all_keywords = question_keywords | answer_keywords
    
    expanded_keywords = expand_keywords(all_keywords)
    
    processed = {
        'id': entry.id,
        'kb_id': f"KB_{entry.id:03d}",
        'question': entry.question,
        'question_normalized': question_norm,
        'answer': entry.answer,
        'answer_normalized': answer_norm,
        'category': entry.type.lower(),
        'keywords': list(all_keywords),
        'keywords_expanded': list(expanded_keywords),
        'tags': list(auto_tag_entry({
            'question': entry.question,
            'answer': entry.answer,
            'category': entry.type
        })),
        'created_at': entry.created_at.isoformat() if entry.created_at else None,
    }
    
    return processed


def build_kb_cache() -> List[Dict]:
    """Build cache of all approved KB entries"""
    kb_entries = KnowledgeBase.objects.filter(approved=True)
    
    cache_data = []
    for entry in kb_entries:
        try:
            processed = preprocess_kb_entry(entry)
            cache_data.append(processed)
        except Exception as e:
            print(f"Error processing KB entry {entry.id}: {str(e)}")
            continue
    
    return cache_data


def get_kb_cache(force_rebuild: bool = False) -> List[Dict]:
    """
    Get KB cache, building if necessary.
    Uses Django cache for in-memory storage.
    """
    cache_key = 'kb_cache_all_entries'
    
    if force_rebuild:
        cache_data = build_kb_cache()
        cache.set(cache_key, cache_data, timeout=None)  # No expiration
        print(f"KB Cache rebuilt: {len(cache_data)} entries")
        return cache_data
    
    cache_data = cache.get(cache_key)
    
    if cache_data is None:
        cache_data = build_kb_cache()
        cache.set(cache_key, cache_data, timeout=None)
        print(f"KB Cache built: {len(cache_data)} entries")
    
    return cache_data


def rebuild_kb_cache():
    """Force rebuild of KB cache"""
    return get_kb_cache(force_rebuild=True)


def get_cache_stats() -> Dict:
    """Get statistics about cached KB entries"""
    cache_data = get_kb_cache()
    
    stats = {
        'total_entries': len(cache_data),
        'by_category': {},
        'total_keywords': 0,
        'avg_keywords_per_entry': 0
    }
    
    total_keywords = 0
    for entry in cache_data:
        category = entry.get('category', 'unknown')
        stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        total_keywords += len(entry.get('keywords', []))
    
    stats['total_keywords'] = total_keywords
    if len(cache_data) > 0:
        stats['avg_keywords_per_entry'] = total_keywords / len(cache_data)
    
    return stats

