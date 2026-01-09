"""
Knowledge Base Matcher
Fast keyword-based matching without AI.
"""
from typing import Optional, Tuple, List, Dict
from .kb_cache import get_kb_cache, normalize_text, extract_keywords, expand_keywords


def calculate_match_score(user_text: str, kb_entry: Dict) -> float:
    """
    Calculate match score between user text and KB entry.
    Returns score from 0.0 to 1.0
    """
    user_normalized = normalize_text(user_text)
    user_keywords = extract_keywords(user_text)
    user_keywords_expanded = expand_keywords(user_keywords)
    
    if not user_keywords:
        return 0.0
    
    question_norm = kb_entry.get('question_normalized', '')
    answer_norm = kb_entry.get('answer_normalized', '')
    kb_keywords = set(kb_entry.get('keywords', []))
    kb_keywords_expanded = set(kb_entry.get('keywords_expanded', []))
    kb_tags = set(kb_entry.get('tags', []))
    
    score = 0.0
    
    # 1. EXACT PHRASE MATCH (highest weight: 0.4)
    if user_normalized in question_norm or question_norm in user_normalized:
        if question_norm.startswith(user_normalized) or user_normalized.startswith(question_norm):
            score += 0.4
        else:
            score += 0.3
    
    # 2. KEYWORD OVERLAP IN QUESTION (weight: 0.3)
    question_matches = len(user_keywords & kb_keywords)
    question_expanded_matches = len(user_keywords_expanded & kb_keywords_expanded)
    
    if len(user_keywords) > 0:
        question_coverage = (question_matches + question_expanded_matches * 0.5) / len(user_keywords)
        score += min(question_coverage * 0.3, 0.3)
    
    # 3. KEYWORD OVERLAP IN ANSWER (weight: 0.2)
    answer_matches = len(user_keywords & kb_keywords)
    if len(user_keywords) > 0:
        answer_coverage = answer_matches / len(user_keywords)
        score += min(answer_coverage * 0.2, 0.2)
    
    # 4. TAG MATCHING (weight: 0.1)
    user_tags = set()
    for keyword in user_keywords:
        for tag_key, tag_synonyms in [
            ('faq', ['hour', 'time', 'working', 'office']),
            ('rule', ['attendance', 'dress', 'code', 'required']),
            ('syllabus', ['syllabus', 'subject', 'course', 'semester']),
            ('exam', ['exam', 'test', 'marks'])
        ]:
            if keyword in tag_synonyms or any(tag in keyword for tag in tag_synonyms):
                user_tags.add(tag_key)
    
    if user_tags and kb_tags:
        tag_overlap = len(user_tags & kb_tags)
        if tag_overlap > 0:
            score += min(tag_overlap * 0.1, 0.1)
    
    # 5. CATEGORY AWARENESS BONUS
    category = kb_entry.get('category', '').lower()
    user_text_lower = user_normalized
    
    if category == 'faq' and any(word in user_text_lower for word in ['hour', 'time', 'timing', 'working', 'office']):
        score += 0.05
    elif category == 'rule' and any(word in user_text_lower for word in ['attendance', 'dress', 'code', 'required']):
        score += 0.05
    elif category == 'syllabus' and any(word in user_text_lower for word in ['syllabus', 'subject', 'course', 'semester']):
        score += 0.05
    elif category == 'exam' and any(word in user_text_lower for word in ['exam', 'test', 'marks']):
        score += 0.05
    
    return min(score, 1.0)


def match_kb_entry(user_text: str, min_confidence: float = 0.4) -> Optional[Tuple[Dict, float]]:
    """
    Match user text against cached KB entries.
    
    Args:
        user_text: User's question
        min_confidence: Minimum score threshold (0.0 to 1.0)
    
    Returns:
        Tuple of (kb_entry_dict, score) or None if no match
    """
    if not user_text or len(user_text.strip()) < 3:
        return None
    
    cache_data = get_kb_cache()
    
    if not cache_data:
        return None
    
    best_match = None
    best_score = 0.0
    
    for entry in cache_data:
        score = calculate_match_score(user_text, entry)
        
        if score > best_score:
            best_score = score
            best_match = entry
    
    if best_match and best_score >= min_confidence:
        return (best_match, best_score)
    
    return None


def match_kb_entry_with_details(user_text: str, min_confidence: float = 0.4) -> Optional[Dict]:
    """
    Match with detailed information for debugging.
    
    Returns:
        Dict with match details or None
    """
    result = match_kb_entry(user_text, min_confidence)
    
    if result:
        entry, score = result
        return {
            'match_found': True,
            'kb_entry': entry,
            'score': score,
            'confidence': 'HIGH' if score >= 0.7 else 'MEDIUM' if score >= 0.5 else 'LOW',
            'answer': entry.get('answer'),
            'question': entry.get('question'),
            'category': entry.get('category')
        }
    
    return {
        'match_found': False,
        'score': 0.0,
        'confidence': 'NONE'
    }

