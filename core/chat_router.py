"""
Chat Router - Main entry point for chat responses
Minimizes Gemini usage by prioritizing KB matching.
"""
from typing import Optional, Tuple
from .kb_matcher import match_kb_entry
from .kb_cache import get_kb_cache, rebuild_kb_cache


def chat_reply(user_text: str, user=None) -> Tuple[str, str]:
    """
    Main entry point for chat responses.
    Returns: (response_text, intent_source)
    
    Intent sources:
    - 'kb_match': Found in Knowledge Base
    - 'ai_fallback': Used Gemini (general question or no KB match)
    - 'error': Error occurred
    """
    if not user_text or not user_text.strip():
        return "Please provide a question.", "error"
    
    user_text = user_text.strip()
    
    # STEP 1: Try KB matching first (NO AI CALL)
    kb_match = match_kb_entry(user_text, min_confidence=0.4)
    
    if kb_match:
        entry, score = kb_match
        confidence = 'HIGH' if score >= 0.7 else 'MEDIUM'
        
        print(f"KB Match: KB_ID={entry['id']}, Score={score:.2f}, Confidence={confidence}, Question='{entry['question'][:50]}...'")
        
        return entry['answer'], 'kb_match'
    
    # STEP 2: No KB match found - use Gemini as fallback
    # Only for general questions, explanations, or when KB doesn't have answer
    try:
        from .ai_service import get_gemini_response
        
        # Use Gemini with college context
        response_text = get_gemini_response(
            user_text=user_text,
            user=user,
            is_college_context=True
        )
        
        return response_text, 'ai_fallback'
        
    except Exception as e:
        print(f"Error in Gemini fallback: {str(e)}")
        return "I couldn't find that information in the knowledge base. Please contact the college office for assistance.", "error"


def get_hybrid_response(user_text: str, user=None) -> Tuple[str, str]:
    """
    Legacy compatibility wrapper for existing code.
    Uses KB-first approach with Gemini fallback.
    """
    return chat_reply(user_text, user)


# Initialize cache on module import (lazy loading)
def initialize_cache():
    """Initialize KB cache on startup"""
    try:
        cache_data = get_kb_cache()
        print(f"KB Cache initialized: {len(cache_data)} entries ready")
    except Exception as e:
        print(f"Warning: Could not initialize KB cache: {str(e)}")


# Auto-initialize on import
try:
    initialize_cache()
except:
    pass  # Will initialize on first use

