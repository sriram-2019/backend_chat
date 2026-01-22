"""
Chat Router - Main entry point for chat responses
Minimizes Gemini usage by prioritizing KB matching.
"""
from typing import Optional, Tuple, Union
from .kb_matcher import match_kb_entry
from .kb_cache import get_kb_cache, rebuild_kb_cache
from .models import Document, StudentProfile
from django.db.models import Q


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
    
    # STEP 0: Check for download/document related intent
    download_keywords = [
        'download', 'get files', 'need files', 'syllabus', 'documents', 'document',
        'get document', 'shall i download', 'list all uploaded documents',
        'document download', 'download document', 'exam schedule', 
        'exam info', 'exam information', 'timetable', 'rules', 'regulations',
        'file', 'doc', 'material', 'notes', 'pdf', 'ppt'
    ]
    user_query_lower = user_text.lower()
    is_download_query = any(keyword in user_query_lower for keyword in download_keywords)
    
    if is_download_query:
        print(f"[API] Download intent detected for query: '{user_text}'")
        docs = []
        dept_name = None
        
        # Determine if there's a specific category filter
        category_filter = None
        if any(k in user_query_lower for k in ['exam', 'schedule', 'timetable']):
            category_filter = 'exam_info'
        elif 'syllabus' in user_query_lower:
            category_filter = 'syllabus'
        elif any(k in user_query_lower for k in ['rule', 'regulation']):
            category_filter = 'rules'
            
        if user:
            try:
                profile = StudentProfile.objects.get(user=user)
                dept_name = profile.course
                user_year = profile.year
                print(f"[API] Searching docs for User: {user.username}, Dept: '{dept_name}', Year: '{user_year}', Category: '{category_filter}'")
                
                # We fetch all candidates and filter in Python because SQLite JSON lookups are unreliable
                # 1. Fetch all documents that ARE public OR have VISIBILITY='department'
                candidates = Document.objects.filter(
                    Q(visibility='public') | Q(visibility='department')
                ).order_by('-created_at')
                
                if category_filter:
                    candidates = candidates.filter(document_type=category_filter)
                
                matched_docs = []
                # DEBUG: Trace first doc and student data
                # first_doc = candidates.first()
                # if first_doc:
                #    target_depts = first_doc.target_departments or []
                #    match_result = dept_name in target_depts if dept_name else "NoDept"
                #    # raise Exception(f"DEBUG: Student=['{dept_name}', '{user_year}'], DocTargetDepts={repr(target_depts)}, Match={match_result}")
                
                for doc in candidates:
                    if doc.visibility == 'public':
                        matched_docs.append(doc)
                    elif doc.visibility == 'department':
                        target_depts = doc.target_departments or []
                        target_years = doc.target_years or []
                        dept_match = dept_name in target_depts if dept_name else False
                        year_match = not target_years or (user_year in target_years if user_year else False)
                        if dept_match and year_match:
                            matched_docs.append(doc)
                    if len(matched_docs) >= 10:
                        break
                docs = matched_docs
                
                # If no specific matches found, try fallback to just public docs
                if not docs and (dept_name or user_year):
                    print(f"[API] No specific matches, falling back to all public docs")
                    fallback = Document.objects.filter(visibility='public').order_by('-created_at')
                    if category_filter:
                        fallback = fallback.filter(document_type=category_filter)
                    docs = list(fallback[:5])
                    
            except StudentProfile.DoesNotExist:
                print(f"[API] StudentProfile not found, showing public docs only")
                docs = Document.objects.filter(visibility='public').order_by('-created_at')[:10]
        else:
            print(f"[API] No user, showing public docs only")
            docs = Document.objects.filter(visibility='public').order_by('-created_at')[:10]
            
        if docs:
            print(f"[API] Found {len(docs)} documents for download suggestion")
            doc_list = []
            for d in docs:
                doc_list.append({
                    'id': d.id,
                    'title': d.title,
                    'file_name': d.file_name,
                    'file_size': d.file_size,
                    'type': d.document_type
                })
            
            # Compose helpful response text
            if category_filter:
                cat_name = category_filter.replace('_', ' ')
                response_text = f"I found some {cat_name} documents"
            else:
                response_text = f"I found some documents related to your request"
                
            # Check if any dept-specific docs are in the list
            if any(getattr(d, 'visibility', 'public') == 'department' for d in docs) and dept_name:
                response_text += f" for the {dept_name} department"
                
            response_text += ":"
            
            source_details = {
                "source_type": "document_list",
                "documents": doc_list,
                "department": dept_name,
                "year": user_year if 'user_year' in locals() else None
            }
            
            if return_details:
                return response_text, 'document_suggestion', 100.0, source_details
            return response_text, 'document_suggestion'
        else:
            print(f"[API] No documents found at all for intent: {user_text}")
    
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

