import os
import json
import re
import requests
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from google import genai
from django.db.models import Q
from django.utils import timezone
from dotenv import load_dotenv
from pathlib import Path

from .models import ChatHistory, KnowledgeBase

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
MODEL = "gemini-2.0-flash-exp"  # Using stable flash model

# Global State for Quota Handling
_QUOTA_EXHAUSTED = False
_QUOTA_EXHAUSTED_UNTIL = None

# Global Cache for Regex Patterns
_KB_REGEX_CACHE = None
_CACHE_TIMESTAMP = None

# --- PROMPTS ---

INTENT_CLASSIFICATION_PROMPT = """You are an intent classification engine inside a College AI Chatbot System.

Your only task is to decide whether a user's question is:
COLLEGE_SPECIFIC → requires college knowledge base
GENERAL → can be answered using general AI knowledge

You must not answer the question.

🔹 Classification Rules
COLLEGE_SPECIFIC: Classify as COLLEGE_SPECIFIC if the question is about college rules, attendance, syllabus, exams, faculty, departments, or procedures.
GENERAL: Classify as GENERAL if the question is a greeting, general knowledge, programming, or unrelated topics.

🔹 Output Format (MANDATORY)
Return ONLY valid JSON.
{
  "intent_type": "COLLEGE_SPECIFIC | GENERAL",
  "confidence": "HIGH | MEDIUM | LOW"
}"""

KB_MATCHING_PROMPT = """You are a Knowledge Base Matching Engine for a College AI Assistant.
Your ONLY job: Determine if a user question matches any Knowledge Base entry.

MATCHING RULES:
1. Semantic Meaning: Match by meaning, not just exact words.
2. Category Awareness: Respect category relevance (rules, syllabus, exams, etc.).
3. High Precision: Do NOT select weak matches. If unsure, return no_match.

OUTPUT FORMAT (MANDATORY):
Return ONLY valid JSON.
If match: {"match_found": true, "kb_id": "<id>", "confidence": "HIGH | MEDIUM"}
If no match: {"match_found": false}"""

# --- UTILITY FUNCTIONS ---

def normalize_text(text: str) -> str:
    """Normalize text for better matching."""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return ' '.join(text.split())

def extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text."""
    stop_words = {'what', 'is', 'the', 'a', 'an', 'are', 'for', 'of', 'in', 'on', 'at', 'to', 'and', 'or', 'with', 'by', 'from', 'when', 'where', 'who', 'which', 'why', 'how', 'how', 'this', 'that'}
    words = normalize_text(text).split()
    return [w for w in words if len(w) > 2 and w not in stop_words]

def get_quota_status() -> bool:
    """Check if the API quota is currently exhausted."""
    global _QUOTA_EXHAUSTED, _QUOTA_EXHAUSTED_UNTIL
    if _QUOTA_EXHAUSTED and _QUOTA_EXHAUSTED_UNTIL:
        if timezone.now() < _QUOTA_EXHAUSTED_UNTIL:
            return True
        else:
            _QUOTA_EXHAUSTED = False
            _QUOTA_EXHAUSTED_UNTIL = None
    return False

def set_quota_exhausted(retry_seconds: int = 3600):
    """Set the quota exhausted flag with a cooldown period."""
    global _QUOTA_EXHAUSTED, _QUOTA_EXHAUSTED_UNTIL
    _QUOTA_EXHAUSTED = True
    _QUOTA_EXHAUSTED_UNTIL = timezone.now() + timedelta(seconds=retry_seconds)
    print(f"⚠️ API Quota exhausted. cooldown until: {_QUOTA_EXHAUSTED_UNTIL}")

def handle_api_error(e: Exception) -> str:
    """Handle Gemini API errors and manage quota state."""
    error_str = str(e)
    if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
        retry_match = re.search(r'retry in (\d+)', error_str, re.IGNORECASE)
        delay = int(retry_match.group(1)) + 10 if retry_match else 3600
        set_quota_exhausted(delay)
        return "QUOTA_EXHAUSTED"
    return error_str

# --- REGEX MATCHING ENGINE ---

SYNONYM_MAP = {
    'timing': ['hours', 'time', 'schedule', 'open', 'close', 'when', 'timings', 'working'],
    'hours': ['timing', 'time', 'schedule', 'open', 'close', 'when', 'timings', 'working'],
    'syllabus': ['subjects', 'topics', 'content', 'courses', 'curriculum', 'portion', 'unit', 'units'],
    'attendance': ['presence', 'present', 'absent', 'minimum', 'percentage', 'required'],
    'dress': ['uniform', 'attire', 'clothing', 'wear', 'code'],
    'code': ['dress', 'uniform', 'regulation', 'rule', 'rules'],
    'exam': ['test', 'examination', 'marks', 'assessment', 'internal', 'semester', 'external'],
    'office': ['administration', 'admin', 'desk', 'reception'],
}

def expand_keywords(keywords: List[str]) -> List[str]:
    """Expand keywords with their synonyms."""
    expanded = set(keywords)
    for kw in keywords:
        if kw in SYNONYM_MAP:
            expanded.update(SYNONYM_MAP[kw])
    return list(expanded)

def generate_kb_regex_pattern(kb_entry) -> Optional[re.Pattern]:
    """Generate a robust regex pattern for a KB entry."""
    keywords = extract_keywords(kb_entry.question)
    if not keywords: return None
    
    parts = []
    # Pick the most important keywords (usually nouns/verbs)
    for kw in keywords[:4]:
        synonyms = [kw]
        if kw in SYNONYM_MAP: synonyms.extend(SYNONYM_MAP[kw])
        parts.append(f'(?:{"|".join(re.escape(s) for s in synonyms)})')
    
    # Create a flexible pattern that requires at least 2 of the top keywords if many exist
    if len(parts) >= 2:
        pattern = r'.*'.join(parts[:2]) # Must have first two key concepts
    else:
        pattern = parts[0]
        
    return re.compile(pattern, re.IGNORECASE)

def get_kb_regex_cache() -> List[Dict]:
    """Get or build the KB regex cache."""
    global _KB_REGEX_CACHE
    if _KB_REGEX_CACHE is None:
        _KB_REGEX_CACHE = []
        for entry in KnowledgeBase.objects.filter(approved=True):
            p = generate_kb_regex_pattern(entry)
            if p: _KB_REGEX_CACHE.append({'entry': entry, 'pattern': p})
    return _KB_REGEX_CACHE

def regex_kb_match(user_text: str) -> Optional[Tuple]:
    """Attempt fast regex matching against KB."""
    normalized = normalize_text(user_text)
    for item in get_kb_regex_cache():
        if item['pattern'].search(normalized):
            return item['entry'], "HIGH"
    return None

# --- CORE AI LOGIC ---

def classify_intent(user_text: str) -> Dict:
    """Classify user intent."""
    if not client or get_quota_status():
        return {"intent_type": "COLLEGE_SPECIFIC", "confidence": "LOW"}
    
    try:
        chat = client.chats.create(model=MODEL, config={"system_instruction": INTENT_CLASSIFICATION_PROMPT})
        response = chat.send_message(user_text)
        text = response.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        handle_api_error(e)
        return {"intent_type": "COLLEGE_SPECIFIC", "confidence": "LOW"}

def calculate_relevance_score(user_text: str, keywords: List[str], entry) -> float:
    """Calculate advanced relevance score (0-100)."""
    q_norm = normalize_text(entry.question)
    u_norm = normalize_text(user_text)
    
    # Exact phrase bonus
    if u_norm in q_norm or q_norm in u_norm:
        return 95.0
    
    score = 0
    u_keywords = set(keywords)
    u_expanded = set(expand_keywords(keywords))
    q_keywords = set(extract_keywords(entry.question))
    
    # Direct keyword matches (using fuzzy substring checks)
    direct_matches = 0
    for uk in u_keywords:
        if any(uk in qk or qk in uk for qk in q_keywords):
            direct_matches += 1
            
    if u_keywords:
        score += (direct_matches / len(u_keywords)) * 60
    
    # Expanded (synonym) matches (using fuzzy substring checks)
    expanded_matches = 0
    for uk in u_expanded:
        if any(uk in qk or qk in uk for qk in q_keywords):
            expanded_matches += 1
            
    if u_keywords:
        score += (min(expanded_matches, len(u_keywords)) / len(u_keywords)) * 20
        
    # Result set matching (if keywords are few, require more precision)
    if len(u_keywords) == 1 and score < 50:
        score = 0 # Prevent single-word weak matches
        
    return min(score, 100.0)

def semantic_kb_match(user_text: str, kb_entries) -> Optional[Tuple]:
    """AI-powered semantic KB match."""
    if not client or get_quota_status(): return None
    
    # Pre-filter to 20 best candidates to save tokens
    keywords = extract_keywords(user_text)
    candidates = []
    for entry in kb_entries[:100]:
        candidates.append((calculate_relevance_score(user_text, keywords, entry), entry))
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_candidates = [c[1] for c in candidates[:20] if c[0] > 0]
    
    if not best_candidates: return None
    
    kb_text = "\n".join([f'id="{e.id}", q="{e.question}"' for e in best_candidates])
    prompt = f'User Question: "{user_text}"\n\nKB Entries:\n{kb_text}\n\nReturn JSON:'
    
    try:
        chat = client.chats.create(model=MODEL, config={"system_instruction": KB_MATCHING_PROMPT})
        response = chat.send_message(prompt)
        text = response.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        result = json.loads(text)
        if result.get("match_found"):
            kb_id = str(result["kb_id"])
            for e in best_candidates:
                if str(e.id) == kb_id:
                    return e, result.get("confidence", "MEDIUM")
    except Exception as e:
        handle_api_error(e)
    return None

def query_knowledge_base(user_text: str) -> Tuple[Optional[str], Optional[KnowledgeBase]]:
    """Multi-tier KB query."""
    try:
        # Tier 1: Regex
        match = regex_kb_match(user_text)
        if match: return match[0].answer, match[0]
        
        # Tier 2: AI Semantic
        all_kb = KnowledgeBase.objects.filter(approved=True)
        match = semantic_kb_match(user_text, all_kb)
        if match: return match[0].answer, match[0]
        
        # Tier 3: Scoring Fallback
        keywords = extract_keywords(user_text)
        best_entry = None
        best_score = 0
        for entry in all_kb:
            score = calculate_relevance_score(user_text, keywords, entry)
            if score > best_score:
                best_score = score
                best_entry = entry
        
        if best_entry and best_score >= 40:
            return best_entry.answer, best_entry
            
        return None, None
    except Exception:
        traceback.print_exc()
        return None, None

def get_gemini_response(user_text: str, user=None, is_college_context=False) -> str:
    """Get general or college-context AI response."""
    if get_quota_status():
        wait_time = _QUOTA_EXHAUSTED_UNTIL - timezone.now()
        mins = max(1, int(wait_time.total_seconds() / 60))
        return f"I'm experiencing high demand. Please try again in ~{mins} minutes or check the Knowledge Base."
    
    if not client: return "AI service unconfigured."
    
    history = []
    if user:
        past = ChatHistory.objects.filter(user=user).order_by('-timestamp')[:5]
        for c in reversed(past):
            if c.message: history.append({"role": "user", "parts": [{"text": c.message}]})
            if c.response: history.append({"role": "model", "parts": [{"text": c.response}]})

    sys_inst = "You are INTELLIQ, a helpful College Assistant."
    if is_college_context:
        sys_inst += " Focus on college rules and procedures. If unknown, refer to office."
    else:
        sys_inst += " Focus on academics, English coaching, and technology."

    try:
        chat = client.chats.create(model=MODEL, history=history, config={"system_instruction": sys_inst})
        return chat.send_message(user_text).text
    except Exception as e:
        err = handle_api_error(e)
        if err == "QUOTA_EXHAUSTED":
            return "I'm experiencing high demand. Please try again later."
        return f"Error: {err}"

def get_hybrid_response(user_text: str, user=None) -> Tuple[str, str]:
    """Main entry point for AI responses."""
    intent_data = classify_intent(user_text)
    intent = intent_data.get("intent_type", "GENERAL")
    
    if intent == "COLLEGE_SPECIFIC":
        answer, entry = query_knowledge_base(user_text)
        if answer: return answer, "kb_match"
        return get_gemini_response(user_text, user, True), "ai_fallback"
    
    return get_gemini_response(user_text, user, False), "ai_fallback"
