"""
Chat Router - Main entry point for chat responses
Minimizes Gemini usage by prioritizing KB matching.
"""
from typing import Optional, Tuple, Union
from .kb_matcher import match_kb_entry
from .kb_cache import get_kb_cache, rebuild_kb_cache


def chat_reply(user_text: str, user=None, return_details: bool = False) -> Union[Tuple[str, str], Tuple[str, str, float, dict]]:
    """
    Main entry point for chat responses.
    
    Args:
        user_text: The user's message
        user: The user object (optional)
        return_details: If True, returns (response_text, intent_source, confidence_score, source_details)
                       If False, returns (response_text, intent_source) for backward compatibility
    
    Returns: 
        If return_details=False: (response_text, intent_source)
        If return_details=True: (response_text, intent_source, confidence_score, source_details)
    
    Intent sources:
    - 'kb_match': Found in Knowledge Base
    - 'ai_fallback': Used Gemini (general question or no KB match)
    - 'error': Error occurred
    """
    if not user_text or not user_text.strip():
        if return_details:
            return "Please provide a question.", "error", 0.0, {}
        return "Please provide a question.", "error"
    
    user_text = user_text.strip()
    
    # STEP 1: Try KB matching first (NO AI CALL)
    kb_match = match_kb_entry(user_text, min_confidence=0.4)
    
    if kb_match:
        entry, score = kb_match
        confidence_label = 'HIGH' if score >= 0.7 else 'MEDIUM'
        
        # Convert score to percentage (0-100)
        confidence_score = min(score * 100, 100.0)
        
        source_details = {
            "kb_id": entry['id'],
            "matched_question": entry['question'][:100] + "..." if len(entry['question']) > 100 else entry['question'],
            "match_score": score,
            "confidence_label": confidence_label,
            "source_type": "knowledge_base"
        }
        
        print(f"[API] Using KB Database (NO API call) - KB_ID={entry['id']}, Score={score:.2f}, Confidence={confidence_label}")
        print(f"KB Match: KB_ID={entry['id']}, Score={score:.2f}, Confidence={confidence_label}, Question='{entry['question'][:50]}...'")
        
        if return_details:
            return entry['answer'], 'kb_match', confidence_score, source_details
        return entry['answer'], 'kb_match'
    
    # STEP 2: No KB match found - use Gemini as fallback
    # Only for general questions, explanations, or when KB doesn't have answer
    try:
        from .ai_service import get_gemini_response, classify_intent
        
        # Classify intent to determine if it's college-specific or general
        intent_result = classify_intent(user_text)
        intent_type = intent_result.get("intent_type", "GENERAL")
        confidence = intent_result.get("confidence", "MEDIUM")
        
        # Set is_college_context based on intent classification
        is_college_context = (intent_type == "COLLEGE_SPECIFIC")
        
        print(f"[API] Using Gemini API (fallback - no KB match found)")
        print(f"[INTENT] Classified as: {intent_type} (confidence: {confidence})")
        
        # Use Gemini with appropriate context based on intent
        response_text = get_gemini_response(
            user_text=user_text,
            user=user,
            is_college_context=is_college_context
        )
        
        # AI responses get lower confidence since they're not from verified KB
        confidence_score = 60.0 if confidence == "HIGH" else 50.0 if confidence == "MEDIUM" else 40.0
        
        source_details = {
            "intent_type": intent_type,
            "intent_confidence": confidence,
            "source_type": "ai_generated",
            "is_college_context": is_college_context
        }
        
        if return_details:
            return response_text, 'ai_fallback', confidence_score, source_details
        return response_text, 'ai_fallback'
        
    except Exception as e:
        import traceback
        error_str = str(e)
        error_traceback = traceback.format_exc()
        print(f"Error in Gemini fallback: {error_str}")
        print(error_traceback)
        # Raise the exception with full details so it can be caught by the view
        raise Exception(f"Gemini API Error: {error_str}\n\nTraceback:\n{error_traceback}") from e


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

