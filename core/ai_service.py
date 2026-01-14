import os
import json
import re
import requests
import google.generativeai as genai
from django.db.models import Q
from .models import ChatHistory, KnowledgeBase
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Load environment variables
# Check environment variables first (PythonAnywhere might have them set as system env vars)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

# If not in environment, try loading from .env file
# Try multiple paths for .env file (works for both local and PythonAnywhere)
if not GEMINI_API_KEY or not HUGGINGFACE_API_KEY:
    env_paths = [
        Path(__file__).resolve().parent.parent / ".env",  # backend/.env (PythonAnywhere: backend_chat/.env)
        Path(__file__).resolve().parent.parent.parent / ".env",  # project_root/.env (local structure)
        Path(__file__).resolve().parent / ".env",  # core/.env (fallback)
    ]

    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)  # Don't override existing env vars
            env_loaded = True
            print(f"✓ Loaded .env from: {env_path}")
            # Reload keys after loading .env
            if not GEMINI_API_KEY:
                GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            if not HUGGINGFACE_API_KEY:
                HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
            break

    if not env_loaded:
        # Try loading without explicit path (uses current directory)
        try:
            load_dotenv(override=False)
            if not GEMINI_API_KEY:
                GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            if not HUGGINGFACE_API_KEY:
                HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
        except Exception as e:
            print(f"⚠️ Could not load .env file: {e}")

# Print status (masked for security)
if GEMINI_API_KEY:
    key_preview = f"{GEMINI_API_KEY[:4]}...{GEMINI_API_KEY[-4:]}" if len(GEMINI_API_KEY) > 8 else "***"
    print(f"✓ GEMINI_API_KEY loaded ({key_preview})")
else:
    print("⚠️ WARNING: GEMINI_API_KEY not found in environment or .env file")

if HUGGINGFACE_API_KEY:
    print("✓ HUGGINGFACE_API_KEY loaded")
else:
    print("⚠️ HUGGINGFACE_API_KEY not found (optional)")

# Initialize clients
api_key = GEMINI_API_KEY  # Keep for backward compatibility
if api_key:
    try:
        genai.configure(api_key=api_key)
        client = genai  # Store genai module for compatibility checks
    except Exception as e:
        print(f"Error configuring Gemini API: {str(e)}")
        client = None
else:
    client = None
MODEL = "gemini-2.5-flash"  # Use stable model name

# Prefer Hugging Face if available (completely free, 1,000 requests/day)
USE_HUGGINGFACE = bool(HUGGINGFACE_API_KEY)

INTENT_CLASSIFICATION_PROMPT = """You are an intent classification engine inside a College AI Chatbot System.

Your only task is to decide whether a user's question is:

COLLEGE_SPECIFIC → requires college knowledge base

GENERAL → can be answered using general AI knowledge

You must not answer the question.

🔹 Classification Rules

COLLEGE_SPECIFIC

Classify as COLLEGE_SPECIFIC only if the question depends on institution-specific information, such as:

College rules, attendance, dress code

Syllabus, subjects, credits

Exams, internal marks, timetable

College departments, faculty, procedures

Uploaded college documents

Any data stored in the college knowledge base

GENERAL

Classify as GENERAL if the question:

Is general knowledge

Is about programming or technology

Is a greeting or casual message

Is entertainment, news, movies, or unrelated topics

🔹 Output Format (MANDATORY)

Return ONLY valid JSON.

No explanations, no markdown, no extra text.

{
  "intent_type": "COLLEGE_SPECIFIC | GENERAL",
  "confidence": "HIGH | MEDIUM | LOW"
}

🔹 Examples (Follow Exactly)

Input: What is Python?
{
  "intent_type": "GENERAL",
  "confidence": "HIGH"
}

Input: What is the attendance percentage required?
{
  "intent_type": "COLLEGE_SPECIFIC",
  "confidence": "HIGH"
}

Input: When will Jananayagan release?
{
  "intent_type": "GENERAL",
  "confidence": "HIGH"
}

Input: When is internal exam?
{
  "intent_type": "COLLEGE_SPECIFIC",
  "confidence": "MEDIUM"
}

Now classify this question:"""

# Track quota exhaustion to avoid repeated API calls
# Declared at module level for global access
_QUOTA_EXHAUSTED = False
_QUOTA_EXHAUSTED_UNTIL = None

def classify_intent(user_text):
    """
    Classify user question as COLLEGE_SPECIFIC or GENERAL using Gemini.
    Handles rate limits by defaulting to COLLEGE_SPECIFIC for safety.
    
    Args:
        user_text: The user's message
    
    Returns:
        dict: {"intent_type": "COLLEGE_SPECIFIC" | "GENERAL", "confidence": "HIGH" | "MEDIUM" | "LOW"}
    """
    global _QUOTA_EXHAUSTED, _QUOTA_EXHAUSTED_UNTIL
    
    if not client:
        # Default to GENERAL if Gemini is not configured
        return {"intent_type": "GENERAL", "confidence": "LOW"}
    
    # Check quota status
    if _QUOTA_EXHAUSTED and _QUOTA_EXHAUSTED_UNTIL:
        from django.utils import timezone
        if timezone.now() < _QUOTA_EXHAUSTED_UNTIL:
            # Quota exhausted, default to COLLEGE_SPECIFIC to allow KB matching
            # This is safer than assuming GENERAL and missing KB matches
            return {"intent_type": "COLLEGE_SPECIFIC", "confidence": "LOW"}
    
    try:
        # Create a model with system instruction for intent classification
        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=INTENT_CLASSIFICATION_PROMPT.strip()
        )
        
        # Send the classification request
        response = model.generate_content(user_text)
        response_text = response.text.strip()
        
        # Try to parse JSON from response
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        intent_data = json.loads(response_text)
        
        # Validate response
        if intent_data.get("intent_type") in ["COLLEGE_SPECIFIC", "GENERAL"]:
            return intent_data
        else:
            # Fallback to GENERAL if invalid response
            return {"intent_type": "GENERAL", "confidence": "LOW"}
            
    except json.JSONDecodeError as e:
        # If JSON parsing fails, try to extract intent from text
        try:
            response_lower = response_text.lower()
            if "college_specific" in response_lower:
                return {"intent_type": "COLLEGE_SPECIFIC", "confidence": "MEDIUM"}
            else:
                return {"intent_type": "GENERAL", "confidence": "MEDIUM"}
        except:
            # If response_text is not defined, default to GENERAL
            return {"intent_type": "GENERAL", "confidence": "LOW"}
    except Exception as e:
        error_str = str(e)
        
        # Handle quota/rate limit errors
        if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
            print("⚠️ Gemini API quota exhausted in classify_intent. Defaulting to COLLEGE_SPECIFIC.")
            
            # Extract retry delay if available
            import re
            from django.utils import timezone
            from datetime import timedelta
            
            retry_match = re.search(r'retry in (\d+)', error_str, re.IGNORECASE)
            if retry_match:
                retry_seconds = int(retry_match.group(1))
                _QUOTA_EXHAUSTED_UNTIL = timezone.now() + timedelta(seconds=retry_seconds + 10)
            else:
                _QUOTA_EXHAUSTED_UNTIL = timezone.now() + timedelta(hours=1)
            
            _QUOTA_EXHAUSTED = True
            
            # Default to COLLEGE_SPECIFIC to allow KB matching (safer)
            return {"intent_type": "COLLEGE_SPECIFIC", "confidence": "LOW"}
        
        print(f"Error in intent classification: {str(e)}")
        # Default to COLLEGE_SPECIFIC on error (safer - allows KB matching)
        return {"intent_type": "COLLEGE_SPECIFIC", "confidence": "LOW"}


def analyze_image_with_gemini(image_path: str, query_text: str = None) -> dict:
    """
    Analyze an image using Gemini Vision API.
    
    Args:
        image_path: Path to the image file
        query_text: Optional user query about the image
    
    Returns:
        dict: {"response": str, "confidence": float, "success": bool, "error": str}
    """
    if not client:
        return {
            "response": "Image analysis is not available. Please ensure Gemini API is configured.",
            "confidence": 0.0,
            "success": False,
            "error": "Gemini API not configured"
        }
    
    try:
        import PIL.Image
        
        # Load the image
        image = PIL.Image.open(image_path)
        
        # Use gemini-2.5-flash for vision (supports images)
        vision_model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Build the prompt - restrict to college-related content only
        if query_text and query_text.strip():
            prompt = f"""You are a College Study Assistant AI. You ONLY help with college and education-related content.

The user asks: {query_text}

RULES:
1. ONLY analyze images related to: syllabus, timetables, notes, textbooks, assignments, exam papers, academic documents, educational diagrams, college notices, or study materials.
2. If the image is NOT related to education/college (like selfies, memes, random photos, personal images), politely decline and say: "I can only help with college and education-related images. Please upload study materials, notes, or academic documents."
3. If it IS educational content, analyze it thoroughly and answer the user's question.

Examine the image and respond appropriately based on these rules."""
        else:
            prompt = """You are a College Study Assistant AI. You ONLY help with college and education-related content.

RULES:
1. ONLY analyze images related to: syllabus, timetables, notes, textbooks, assignments, exam papers, academic documents, educational diagrams, college notices, or study materials.
2. If the image is NOT related to education/college (like selfies, memes, random photos, personal images), politely decline and say: "I can only help with college and education-related images. Please upload study materials, notes, or academic documents."
3. If it IS educational content:
   - Describe the academic content
   - Summarize key points if it's notes or a document
   - Explain diagrams or charts if present
   - Provide helpful study insights

Examine the image and respond appropriately based on these rules."""
        
        # Generate response with image
        response = vision_model.generate_content([prompt, image])
        
        response_text = response.text.strip() if response.text else "I could not analyze this image. Please try again."
        
        return {
            "response": response_text,
            "confidence": 85.0,  # Vision model confidence
            "success": True,
            "error": None
        }
        
    except ImportError:
        return {
            "response": "Image processing library (PIL/Pillow) is not installed. Please install it: pip install Pillow",
            "confidence": 0.0,
            "success": False,
            "error": "PIL/Pillow not installed"
        }
    except Exception as e:
        error_str = str(e)
        print(f"Error analyzing image with Gemini: {error_str}")
        
        # Check for quota errors
        if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
            return {
                "response": "The AI service is temporarily busy. Please try again in a few moments.",
                "confidence": 0.0,
                "success": False,
                "error": "API quota exceeded"
            }
        
        return {
            "response": f"I couldn't analyze this image. Error: {error_str}",
            "confidence": 0.0,
            "success": False,
            "error": error_str
        }


# Synonym mappings for better regex matching
SYNONYM_MAP = {
    'hours': ['hour', 'hours', 'time', 'timing', 'schedule', 'when', 'timings'],
    'syllabus': ['syllabus', 'syllabi', 'subjects', 'topics', 'content', 'courses', 'curriculum'],
    'attendance': ['attendance', 'presence', 'present', 'absent', 'absence'],
    'dress': ['dress', 'clothing', 'uniform', 'attire', 'wear'],
    'code': ['code', 'rules', 'regulation', 'guidelines', 'policy', 'policies'],
    'exam': ['exam', 'examination', 'test', 'tests', 'assessment', 'evaluation'],
    'subject': ['subject', 'subjects', 'course', 'courses', 'paper', 'papers'],
    'office': ['office', 'administration', 'admin', 'department'],
    'working': ['working', 'operational', 'open', 'available'],
    'required': ['required', 'minimum', 'needed', 'mandatory', 'compulsory'],
    'programming': ['programming', 'program', 'coding', 'code', 'software'],
    'fundamentals': ['fundamentals', 'basics', 'basic', 'intro', 'introduction'],
}

def normalize_text(text):
    """Normalize text for better matching - remove punctuation, extra spaces"""
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    # Remove extra spaces
    text = ' '.join(text.split())
    return text

def expand_with_synonyms(word: str) -> List[str]:
    """Expand a word with its synonyms for regex matching"""
    word_lower = word.lower()
    synonyms = [word_lower]  # Include original word
    
    # Add synonyms from map
    for key, syn_list in SYNONYM_MAP.items():
        if word_lower in syn_list or key in word_lower:
            synonyms.extend(syn_list)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_syns = []
    for syn in synonyms:
        if syn not in seen:
            seen.add(syn)
            unique_syns.append(syn)
    
    return unique_syns if len(unique_syns) > 1 else [word_lower]

def generate_kb_regex_pattern(kb_entry) -> Optional[re.Pattern]:
    """
    Generate a robust regex pattern for a KB entry that matches variations.
    
    Args:
        kb_entry: KnowledgeBase model instance
    
    Returns:
        re.Pattern or None if pattern generation fails
    """
    try:
        question = kb_entry.question.lower().strip()
        category = kb_entry.type.lower()
        
        # Extract key terms (remove stop words)
        stop_words = {
            'what', 'is', 'are', 'the', 'a', 'an', 'for', 'of', 'in', 'on', 'at', 
            'to', 'and', 'or', 'but', 'with', 'by', 'from', 'as', 'about', 'into',
            'when', 'where', 'who', 'which', 'why', 'how', 'this', 'that', 'there'
        }
        
        words = re.findall(r'\b\w+\b', question)
        key_terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        if not key_terms:
            # Fallback: use all words except very common ones
            key_terms = [w for w in words if len(w) > 2]
        
        # Build regex pattern with synonyms
        pattern_parts = []
        
        for term in key_terms[:5]:  # Limit to top 5 terms to avoid over-complexity
            synonyms = expand_with_synonyms(term)
            # Create alternation pattern: (term|syn1|syn2)
            if len(synonyms) > 1:
                pattern_parts.append(f'(?:{"|".join(re.escape(s) for s in synonyms)})')
            else:
                pattern_parts.append(re.escape(term))
        
        if not pattern_parts:
            return None
        
        # Category-specific pattern adjustments
        if category == 'syllabus':
            # Syllabus questions: require syllabus-related terms
            syllabus_terms = '(?:syllabus|subjects|topics|content|courses|curriculum)'
            if not re.search(syllabus_terms, question):
                pattern_parts.insert(0, syllabus_terms)
        
        elif category == 'rule':
            # Rule questions: require rule-related terms
            rule_terms = '(?:rule|regulation|policy|code|guideline)'
            if not re.search(rule_terms, question):
                # Check if it's about attendance or dress code specifically
                if 'attendance' in question or 'present' in question:
                    pattern_parts.insert(0, '(?:attendance|minimum|required)')
                elif 'dress' in question:
                    pattern_parts.insert(0, '(?:dress|uniform|attire)')
                else:
                    pattern_parts.insert(0, rule_terms)
        
        elif category == 'exam':
            # Exam questions: require exam-related terms
            exam_terms = '(?:exam|examination|test|assessment)'
            if not re.search(exam_terms, question):
                pattern_parts.insert(0, exam_terms)
        
        elif category in ['faq', 'general']:
            # FAQ/General: more flexible, but still require key terms
            pass
        
        # Build final pattern: allow words in between but require all key terms
        # Using lookahead to ensure all important terms are present
        if len(pattern_parts) >= 3:
            # For 3+ terms: use lookahead to require at least 2 of them
            # This prevents over-matching while still being flexible
            pattern = r'\b(?=.*' + r')(?=.*'.join(pattern_parts[:3]) + r').+\b'
        elif len(pattern_parts) == 2:
            # For 2 terms: both should appear
            pattern = r'(?=.*\b' + pattern_parts[0] + r'\b)(?=.*\b' + pattern_parts[1] + r'\b).+'
        else:
            # For 1 term: just match that term with word boundaries
            pattern = r'\b' + pattern_parts[0] + r'\b'
        
        # Compile pattern with case-insensitive flag
        return re.compile(pattern, re.IGNORECASE)
        
    except Exception as e:
        print(f"Error generating regex for KB entry {kb_entry.id}: {str(e)}")
        return None

def build_kb_regex_cache() -> List[Dict]:
    """
    Build regex patterns for all approved KB entries.
    This should be called periodically or on-demand to refresh patterns.
    
    Returns:
        List of dicts with kb_id, category, and compiled pattern
    """
    kb_entries = KnowledgeBase.objects.filter(approved=True)
    regex_list = []
    
    for entry in kb_entries:
        pattern = generate_kb_regex_pattern(entry)
        if pattern:
            regex_list.append({
                'kb_id': entry.id,
                'kb_entry': entry,  # Store entry for quick access
                'category': entry.type,
                'pattern': pattern,
                'question': entry.question  # For debugging
            })
    
    return regex_list

# Cache for regex patterns (will be initialized on first use)
_KB_REGEX_CACHE = None
_CACHE_TIMESTAMP = None

def get_kb_regex_cache(force_refresh: bool = False) -> List[Dict]:
    """
    Get KB regex cache, building it if necessary.
    
    Args:
        force_refresh: Force rebuild of cache
    
    Returns:
        List of regex pattern dicts
    """
    global _KB_REGEX_CACHE, _CACHE_TIMESTAMP
    
    # Simple cache invalidation: rebuild if forced or cache doesn't exist
    if force_refresh or _KB_REGEX_CACHE is None:
        _KB_REGEX_CACHE = build_kb_regex_cache()
        from django.utils import timezone
        _CACHE_TIMESTAMP = timezone.now()
        print(f"KB Regex cache built: {len(_KB_REGEX_CACHE)} patterns")
    
    return _KB_REGEX_CACHE

def regex_kb_match(user_text: str) -> Optional[Tuple]:
    """
    Fast regex-based KB matching. Acts as a pre-filter before AI matching.
    
    Args:
        user_text: User's question
    
    Returns:
        Tuple of (kb_entry, confidence_string) or None if no match
    """
    user_text_normalized = normalize_text(user_text)
    
    if not user_text_normalized or len(user_text_normalized) < 3:
        return None
    
    # Get regex cache
    regex_patterns = get_kb_regex_cache()
    
    if not regex_patterns:
        return None
    
    # Try matching against all patterns
    # Stop at first strong match
    best_match = None
    best_score = 0
    
    for regex_data in regex_patterns:
        pattern = regex_data['pattern']
        kb_entry = regex_data['kb_entry']
        
        try:
            # Try to match pattern
            match = pattern.search(user_text_normalized)
            if match:
                # Calculate match score based on matched groups and length
                match_score = len(match.group()) / len(user_text_normalized)
                
                # Boost score if it's a longer match (more specific)
                if match_score > 0.5:  # At least 50% of text matched
                    match_score *= 1.5
                
                # Boost score if category matches user intent (basic check)
                category_boost = 1.0
                if 'syllabus' in user_text_normalized and regex_data['category'] == 'syllabus':
                    category_boost = 1.3
                elif 'exam' in user_text_normalized and regex_data['category'] == 'exam':
                    category_boost = 1.3
                elif ('rule' in user_text_normalized or 'attendance' in user_text_normalized) and regex_data['category'] == 'rule':
                    category_boost = 1.3
                elif ('hour' in user_text_normalized or 'time' in user_text_normalized) and regex_data['category'] in ['faq', 'general']:
                    category_boost = 1.3
                
                match_score *= category_boost
                
                if match_score > best_score:
                    best_score = match_score
                    best_match = (kb_entry, match_score)
        
        except Exception as e:
            # Skip patterns that cause errors (avoid catastrophic backtracking)
            print(f"Regex match error for KB {regex_data['kb_id']}: {str(e)}")
            continue
    
    # Return match only if score is above threshold (strong match)
    if best_match and best_score >= 0.3:  # 30% match threshold
        kb_entry, score = best_match
        confidence = "HIGH" if score >= 0.7 else "MEDIUM"
        print(f"Regex KB Match: KB_ID={kb_entry.id}, Score={score:.2f}, Confidence={confidence}, Question='{kb_entry.question[:50]}...'")
        return (kb_entry, confidence)
    
    return None

def extract_keywords(text):
    """Extract meaningful keywords from text"""
    # Extended stop words list
    stop_words = {
        'what', 'is', 'the', 'a', 'an', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
        'can', 'may', 'might', 'must', 'shall', 'to', 'of', 'in', 'on', 'at', 'for',
        'with', 'by', 'from', 'as', 'about', 'into', 'through', 'during', 'including',
        'when', 'where', 'who', 'whom', 'which', 'why', 'how', 'this', 'that', 'these',
        'those', 'they', 'them', 'their', 'there', 'then', 'than', 'if', 'else', 'and',
        'or', 'but', 'so', 'because', 'since', 'while', 'until', 'before', 'after',
        'i', 'you', 'he', 'she', 'it', 'we', 'our', 'your', 'my', 'me', 'him', 'her',
        'us', 'himself', 'herself', 'itself', 'themselves', 'myself', 'yourself', 'ourselves'
    }
    
    normalized = normalize_text(text)
    words = normalized.split()
    
    # Filter out stop words and short words
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    # If no keywords found, use all words longer than 2 chars (might be important terms)
    if not keywords:
        keywords = [word for word in words if len(word) > 2]
    
    return keywords

def calculate_relevance_score(user_text, user_keywords, kb_entry):
    """
    Calculate a comprehensive relevance score for a KB entry.
    Returns a score from 0 to 100.
    """
    user_text_lower = normalize_text(user_text)
    question_lower = normalize_text(kb_entry.question)
    answer_lower = normalize_text(kb_entry.answer)
    
    score = 0.0
    max_score = 100.0
    
    # 1. EXACT MATCHES (highest priority - 40 points max)
    if question_lower == user_text_lower:
        score += 40.0
        return min(score, max_score)
    
    if user_text_lower in question_lower or question_lower in user_text_lower:
        score += 35.0
    
    # 2. PHRASE MATCHES (30 points max)
    # Check if user text appears as phrase in question
    if user_text_lower in question_lower:
        # Bonus if phrase is at the beginning
        if question_lower.startswith(user_text_lower):
            score += 30.0
        else:
            score += 25.0
    
    # Check phrase in answer
    if user_text_lower in answer_lower:
        score += 15.0
    
    # 3. KEYWORD MATCHING (30 points max)
    if user_keywords:
        # Count matches in question (higher weight)
        question_matches = sum(1 for keyword in user_keywords if keyword in question_lower)
        answer_matches = sum(1 for keyword in user_keywords if keyword in answer_lower)
        
        total_keywords = len(user_keywords)
        if total_keywords > 0:
            # Coverage: percentage of keywords matched in question
            question_coverage = (question_matches / total_keywords) * 20.0
            answer_coverage = (answer_matches / total_keywords) * 10.0
            score += question_coverage + answer_coverage
    
    # 4. POSITION BONUS (10 points max)
    # If important keywords appear at the start of the question
    if user_keywords:
        question_words = question_lower.split()
        if question_words:
            # Check if first few words of question contain user keywords
            first_words = ' '.join(question_words[:min(5, len(question_words))])
            keyword_in_start = sum(1 for keyword in user_keywords if keyword in first_words)
            if keyword_in_start > 0:
                score += (keyword_in_start / len(user_keywords)) * 10.0
    
    # 5. LENGTH SIMILARITY ( penalty for very different lengths)
    user_len = len(user_text_lower)
    question_len = len(question_lower)
    if question_len > 0:
        length_ratio = min(user_len, question_len) / max(user_len, question_len)
        # Small bonus if lengths are similar (helps avoid partial matches)
        if length_ratio > 0.7:
            score += 5.0
    
    return min(score, max_score)

KB_MATCHING_PROMPT = """You are a Knowledge Base Matching Engine for a College AI Assistant.

Your ONLY job: Determine if a user question matches any Knowledge Base entry.

INPUTS YOU WILL RECEIVE:
- User Question (natural language)
- A list of approved Knowledge Base entries, where each entry has:
  * id
  * question
  * answer
  * category (rule, syllabus, exam, faq, general)

YOUR OBJECTIVE (STRICT):
1. Identify whether any KB entry sufficiently answers the user question
2. Choose ONLY ONE best entry
3. If no entry is clearly relevant, return NO_MATCH

MATCHING RULES (CRITICAL):
A. Semantic Meaning Comes First
   - Match by meaning, not exact words
   - Different phrasing may still be a valid match
   - Example: User: "What is office working time?" matches KB: "What are the college office working hours?"

B. Category Awareness
   - You must respect category relevance:
     * Office timings → general/faq
     * Attendance, dress code → rule
     * Subjects, units → syllabus
     * Exams, marks → exam
   - If a KB entry belongs to a wrong category, do NOT select it

C. Question Priority
   - Prefer matches where the KB question closely matches the user question
   - Use KB answers only as supporting context, not primary match drivers

D. High Precision Requirement
   - Do NOT select weak or partial matches
   - Do NOT guess
   - If confidence is low → return NO_MATCH (better than wrong answer)

OUTPUT FORMAT (MANDATORY):
Return ONLY valid JSON. No explanations. No markdown. No extra text.

If a match is found:
{
  "match_found": true,
  "kb_id": "<id>",
  "confidence": "HIGH | MEDIUM"
}

If no suitable match exists:
{
  "match_found": false
}

EXAMPLES:
Example 1:
User: "What are the office working hours?"
KB Entry: id="KB_012", question="What are the college office working hours?", category="general"
Output: {"match_found": true, "kb_id": "KB_012", "confidence": "HIGH"}

Example 2:
User: "What is the syllabus for programming?"
KB Entry: id="KB_012", question="What are the college office working hours?", category="general"
Output: {"match_found": false}

Example 3:
User: "When is internal exam?"
KB Entry: id="KB_045", question="When are internal examinations conducted?", category="exam"
Output: {"match_found": true, "kb_id": "KB_045", "confidence": "MEDIUM"}

CRITICAL: If multiple entries seem similar OR none clearly answer → Return {"match_found": false}

Now process this request:"""


def prefilter_kb_entries(user_text, kb_entries, max_entries=50):
    """
    Pre-filter KB entries to reduce the number sent to AI.
    Uses quick keyword matching to find potential candidates.
    
    Args:
        user_text: The user's question
        kb_entries: QuerySet of all KB entries
        max_entries: Maximum number of entries to return
    
    Returns:
        QuerySet: Filtered KB entries
    """
    if kb_entries.count() <= max_entries:
        return kb_entries
    
    # Extract keywords from user text
    user_keywords = extract_keywords(user_text)
    user_text_lower = normalize_text(user_text)
    
    if not user_keywords:
        # If no keywords, just return most recent entries
        return kb_entries.order_by('-created_at')[:max_entries]
    
    # Build Q filter for keyword matching
    keyword_filters = Q()
    for keyword in user_keywords[:5]:  # Limit to top 5 keywords
        keyword_filters |= Q(question__icontains=keyword) | Q(answer__icontains=keyword)
    
    # Try category-based filtering based on keywords
    category_keywords = {
        'rule': ['rule', 'rules', 'regulation', 'attendance', 'dress', 'code', 'discipline'],
        'syllabus': ['syllabus', 'subject', 'unit', 'credit', 'course', 'semester'],
        'exam': ['exam', 'examination', 'test', 'internal', 'marks', 'grade'],
        'faq': ['hour', 'time', 'working', 'office', 'contact', 'phone', 'email'],
    }
    
    # Find potential categories
    matched_categories = []
    for cat, keywords in category_keywords.items():
        if any(kw in user_text_lower for kw in keywords):
            matched_categories.append(cat)
    
    # Filter by category if matched
    if matched_categories:
        category_filter = Q(type__in=matched_categories)
        filtered = kb_entries.filter(category_filter & keyword_filters)
    else:
        filtered = kb_entries.filter(keyword_filters)
    
    # If we have results, sort by relevance and limit
    if filtered.exists():
        # Score and sort entries
        scored_entries = []
        for entry in filtered[:max_entries * 2]:  # Get more than needed for scoring
            score = calculate_relevance_score(user_text, user_keywords, entry)
            if score > 0:
                scored_entries.append((score, entry))
        
        if scored_entries:
            scored_entries.sort(key=lambda x: x[0], reverse=True)
            # Return top N entries
            entry_ids = [entry.id for _, entry in scored_entries[:max_entries]]
            return kb_entries.filter(id__in=entry_ids)
    
    # Fallback: return recent entries
    return kb_entries.order_by('-created_at')[:max_entries]


# Track quota exhaustion to avoid repeated API calls
_QUOTA_EXHAUSTED = False
_QUOTA_EXHAUSTED_UNTIL = None

def huggingface_semantic_kb_match(user_text: str, kb_entries, prefilter_func) -> Optional[Tuple]:
    """
    Use Hugging Face Inference API for semantic KB matching.
    FREE: 1,000 requests/day, completely free, no credit card required.
    
    Args:
        user_text: User's question
        kb_entries: QuerySet of KB entries
        prefilter_func: Function to pre-filter entries
    
    Returns:
        tuple: (kb_entry, confidence) or None
    """
    if not HUGGINGFACE_API_KEY or not kb_entries.exists():
        return None
    
    try:
        # Pre-filter entries to top 50 candidates
        filtered_entries = prefilter_func(user_text, kb_entries, max_entries=50)
        if not filtered_entries.exists():
            return None
        
        # Format KB entries for prompt
        kb_list_text = "Knowledge Base Entries:\n"
        kb_dict = {}
        
        for idx, entry in enumerate(filtered_entries, 1):
            kb_id = f"KB_{entry.id:03d}"
            kb_dict[kb_id] = entry
            answer_preview = entry.answer[:150] + "..." if len(entry.answer) > 150 else entry.answer
            kb_list_text += f'{idx}. id="{kb_id}", question="{entry.question}", answer="{answer_preview}", category="{entry.type}"\n'
        
        # Build prompt using KB_MATCHING_PROMPT
        prompt = f"""{KB_MATCHING_PROMPT}

User Question: "{user_text}"

{kb_list_text}

Return ONLY the JSON response:"""
        
        # Call Hugging Face API (using free Llama model)
        # Note: Using smaller model for faster inference
        model = "meta-llama/Meta-Llama-3-8B-Instruct"  # Smaller, faster model
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.1,
                    "return_full_text": False,
                    "do_sample": True,
                    "top_p": 0.9
                }
            },
            timeout=30  # HF can be slower, especially first call
        )
        
        if response.status_code != 200:
            error_msg = response.text[:200]
            print(f"Hugging Face API error: {response.status_code} - {error_msg}")
            # Handle loading state (503) - model might be loading
            if response.status_code == 503:
                print("Model is loading. First request may take longer. Please retry.")
            return None
        
        result = response.json()
        
        # Handle different response formats from HF
        response_text = ""
        if isinstance(result, list) and len(result) > 0:
            response_text = result[0].get("generated_text", "").strip()
        elif isinstance(result, dict):
            response_text = result.get("generated_text", "").strip()
            # Sometimes it's wrapped in a list within the dict
            if not response_text and "generated_text" not in result:
                if isinstance(result.get("data"), list) and len(result["data"]) > 0:
                    response_text = result["data"][0].get("generated_text", "").strip()
        else:
            response_text = str(result).strip()
        
        if not response_text:
            print("Hugging Face returned empty response")
            return None
        
        # Clean response (remove markdown if present)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Extract JSON from response
        try:
            match_result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON object from text
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
            if json_match:
                try:
                    match_result = json.loads(json_match.group())
                except:
                    print(f"Could not parse JSON from HF response: {response_text[:200]}")
                    return None
            else:
                print(f"No JSON found in HF response: {response_text[:200]}")
                return None
        
        if match_result.get("match_found") and match_result.get("kb_id"):
            kb_id_str = match_result["kb_id"]
            confidence = match_result.get("confidence", "MEDIUM")
            matched_entry = kb_dict.get(kb_id_str)
            
            if matched_entry:
                print(f"Hugging Face KB Match: {kb_id_str}, Confidence: {confidence}, Question: '{matched_entry.question[:50]}...' (Processed {filtered_entries.count()} of {kb_entries.count()} entries)")
                return matched_entry, confidence
        
        return None
        
    except requests.exceptions.Timeout:
        print("Hugging Face API timeout (model may be loading)")
        return None
    except Exception as e:
        print(f"Error in Hugging Face semantic match: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def semantic_kb_match(user_text, kb_entries):
    """
    Use Gemini AI to semantically match user question to knowledge base entries.
    FUTURE-PROOF: Pre-filters entries before sending to AI to handle large KBs.
    Handles rate limits and quota exhaustion gracefully.
    
    Args:
        user_text: The user's question
        kb_entries: QuerySet of KnowledgeBase entries
    
    Returns:
        tuple: (kb_entry or None, confidence or None)
    """
    global _QUOTA_EXHAUSTED, _QUOTA_EXHAUSTED_UNTIL
    
    # Check if quota is exhausted and we should skip AI calls
    if not client or not kb_entries.exists():
        return None, None
    
    # Check quota status
    if _QUOTA_EXHAUSTED and _QUOTA_EXHAUSTED_UNTIL:
        from django.utils import timezone
        if timezone.now() < _QUOTA_EXHAUSTED_UNTIL:
            # Quota still exhausted, skip AI call
            print("Skipping AI matching due to quota exhaustion. Using regex/fallback methods.")
            return None, None
        else:
            # Quota period expired, reset
            _QUOTA_EXHAUSTED = False
            _QUOTA_EXHAUSTED_UNTIL = None
    
    try:
        # FUTURE-PROOF: Pre-filter entries to avoid token limits and high costs
        # Limit to top 50 candidates (adjustable based on your needs)
        filtered_entries = prefilter_kb_entries(user_text, kb_entries, max_entries=50)
        
        if not filtered_entries.exists():
            return None, None
        
        # Format KB entries for prompt (only filtered ones)
        kb_list_text = "Knowledge Base Entries:\n"
        kb_dict = {}  # Map IDs to entries
        
        for idx, entry in enumerate(filtered_entries, 1):
            kb_id = f"KB_{entry.id:03d}"
            kb_dict[kb_id] = entry
            # Truncate long answers to save tokens
            answer_preview = entry.answer[:150] + "..." if len(entry.answer) > 150 else entry.answer
            kb_list_text += f"{idx}. id=\"{kb_id}\", question=\"{entry.question}\", answer=\"{answer_preview}\", category=\"{entry.type}\"\n"
        
        # Build complete prompt
        full_prompt = f"""User Question: "{user_text}"

{kb_list_text}

Return ONLY the JSON response:"""
        
        # Call Gemini with error handling for rate limits
        try:
            # Create model with system instruction for KB matching
            model = genai.GenerativeModel(
                model_name=MODEL,
                system_instruction=KB_MATCHING_PROMPT.strip(),
                generation_config={
                    "temperature": 0.1  # Low temperature for deterministic matching
                }
            )
            
            response = model.generate_content(full_prompt)
            response_text = response.text.strip()
            
            # Reset quota flag on successful call
            _QUOTA_EXHAUSTED = False
            _QUOTA_EXHAUSTED_UNTIL = None
            
        except Exception as api_error:
            error_str = str(api_error)
            
            # Check for quota/rate limit errors
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                print("⚠️ Gemini API quota exhausted. Falling back to regex/scoring methods.")
                
                # Extract retry delay if available
                import re
                retry_match = re.search(r'retry in (\d+)', error_str, re.IGNORECASE)
                if retry_match:
                    retry_seconds = int(retry_match.group(1))
                    from django.utils import timezone
                    from datetime import timedelta
                    _QUOTA_EXHAUSTED_UNTIL = timezone.now() + timedelta(seconds=retry_seconds + 10)  # Add buffer
                    print(f"Will retry AI matching after {retry_seconds + 10} seconds.")
                else:
                    # Default: wait 1 hour
                    from django.utils import timezone
                    from datetime import timedelta
                    _QUOTA_EXHAUSTED_UNTIL = timezone.now() + timedelta(hours=1)
                
                _QUOTA_EXHAUSTED = True
                return None, None
            else:
                # Other API errors, re-raise
                raise
        
        # Clean response (remove markdown if present)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        match_result = json.loads(response_text)
        
        if match_result.get("match_found") and match_result.get("kb_id"):
            kb_id_str = match_result["kb_id"]
            confidence = match_result.get("confidence", "MEDIUM")
            
            # Extract ID from KB_XXX format
            try:
                matched_entry = kb_dict.get(kb_id_str)
                
                if matched_entry:
                    print(f"Semantic KB Match: {kb_id_str}, Confidence: {confidence}, Question: '{matched_entry.question[:50]}...' (Processed {filtered_entries.count()} of {kb_entries.count()} entries)")
                    return matched_entry, confidence
            except (ValueError, IndexError) as e:
                print(f"Invalid KB ID format: {kb_id_str}, Error: {str(e)}")
        
        return None, None
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error in semantic KB match: {str(e)}")
        try:
            print(f"Response was: {response_text[:200]}")
        except:
            pass
        return None, None
    except Exception as e:
        # Check if it's a quota error
        error_str = str(e)
        if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
            # Already handled above, but catch here too
            return None, None
        
        print(f"Error in semantic KB match: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def query_knowledge_base(user_text):
    """
    Query the college knowledge base using a multi-tier matching system:
    1. FAST: Regex-based matching (pre-filter)
    2. AI: Semantic AI matching (high accuracy)
    3. FALLBACK: Scoring-based matching
    
    FUTURE-PROOF: Handles large KBs efficiently with pre-filtering and limits.
    
    Args:
        user_text: The user's message
    
    Returns:
        tuple: (answer_text or None, kb_entry or None)
    """
    try:
        user_text = user_text.strip()
        if not user_text:
            return None, None
        
        # Get all approved knowledge base entries
        all_kb = KnowledgeBase.objects.filter(approved=True)
        
        if not all_kb.exists():
            return None, None
        
        # TIER 1: FAST Regex-based matching (pre-filter)
        # This is extremely fast and acts as first-line defense
        regex_match = regex_kb_match(user_text)
        if regex_match:
            matched_entry, confidence = regex_match
            # Only accept HIGH or MEDIUM confidence from regex
            if confidence in ["HIGH", "MEDIUM"]:
                return matched_entry.answer, matched_entry
            # If LOW confidence, continue to next tier
        
        total_kb_count = all_kb.count()
        
        # TIER 2: Semantic AI matching (best for accuracy)
        # FUTURE-PROOF: Pre-filtering happens inside semantic_kb_match
        if client:
            matched_entry, confidence = semantic_kb_match(user_text, all_kb)
            if matched_entry and confidence:
                # Only accept HIGH or MEDIUM confidence from AI
                if confidence in ["HIGH", "MEDIUM"]:
                    return matched_entry.answer, matched_entry
                # If LOW confidence, fall through to scoring method
        
        # TIER 3: Scoring-based matching (fallback)
        # FUTURE-PROOF: Pre-filter before scoring for large KBs
        user_keywords = extract_keywords(user_text)
        
        # Pre-filter entries for faster processing
        if total_kb_count > 100:
            # For large KBs, pre-filter first
            filtered_kb = prefilter_kb_entries(user_text, all_kb, max_entries=100)
            entries_to_score = filtered_kb
            print(f"Large KB detected ({total_kb_count} entries). Pre-filtered to {filtered_kb.count()} candidates for scoring.")
        else:
            entries_to_score = all_kb
        
        scored_entries = []
        for kb_entry in entries_to_score:
            score = calculate_relevance_score(user_text, user_keywords, kb_entry)
            if score > 0:
                scored_entries.append((score, kb_entry))
        
        if not scored_entries:
            return None, None
        
        # Sort by score (highest first)
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        
        # Get the best match
        best_score, best_entry = scored_entries[0]
        
        # Minimum confidence threshold: at least 30% relevance
        min_threshold = 25.0 if best_score >= 30.0 else 30.0
        
        if best_score >= min_threshold:
            print(f"Scoring-based KB Match: Score={best_score:.2f}, Question='{best_entry.question[:50]}...'")
            return best_entry.answer, best_entry
        
        # No good match found
        return None, None
        
    except Exception as e:
        print(f"Error querying knowledge base: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def get_gemini_response(user_text, user=None, is_college_context=False):
    """
    Get response from Gemini AI.
    Handles rate limits and quota exhaustion gracefully.
    
    Args:
        user_text: The user's message
        user: The User object (optional)
        is_college_context: Whether this is a college-specific question that needs context
    
    Returns:
        str: Response text
    """
    global _QUOTA_EXHAUSTED, _QUOTA_EXHAUSTED_UNTIL
    
    if not client:
        return "AI service is not configured. Please set GEMINI_API_KEY in your .env file."
    
    # Check quota status
    if _QUOTA_EXHAUSTED and _QUOTA_EXHAUSTED_UNTIL:
        from django.utils import timezone
        if timezone.now() < _QUOTA_EXHAUSTED_UNTIL:
            # Quota exhausted, return helpful message
            from datetime import timedelta
            wait_time = _QUOTA_EXHAUSTED_UNTIL - timezone.now()
            minutes = int(wait_time.total_seconds() / 60)
            return f"I'm currently experiencing high demand. Please try again in {minutes} minute(s), or rephrase your question. For college-specific questions, try checking the knowledge base directly."
    
    try:
        # --- CONTEXT MANAGEMENT ---
        # Retrieve the last 10 messages for this user to provide memory
        history_context = []
        if user:
            recent_chats = ChatHistory.objects.filter(
                user=user,
                response__isnull=False
            ).exclude(response='').order_by('-timestamp')[:10]
            
            # Convert to Gemini history format (oldest first)
            for chat_item in reversed(recent_chats):
                if chat_item.message:
                    history_context.append({"role": "user", "parts": [{"text": chat_item.message}]})
                if chat_item.response:
                    history_context.append({"role": "model", "parts": [{"text": chat_item.response}]})

        if is_college_context:
            system_instruction = """
You are INTELLIQ, a College AI Assistant for students.

You help students with college-specific questions about:
- College rules, attendance, dress code
- Syllabus, subjects, credits
- Exams, internal marks, timetable
- College departments, faculty, procedures

If you don't have specific information, say "I don't have that specific information. Please contact the college office or check the official college website."

Be helpful, professional, and accurate.
"""
        else:
            system_instruction = """
You are INTELLIQ, a premium AI English Coach and Academic Assistant for college students.

Your goals are:

1. Help students improve their English grammar, vocabulary, and professional communication.

2. Answer questions about Engineering, Technology, Mathematics, and Science subjects.

3. Help with academic writing, reports, and presentation preparation.

You should:

- Maintain a professional yet encouraging tone.

- Provide clear, accurate explanations.

- If a question is entirely unrelated to academics or professional development, politely guide the student back to their studies.

Focus on being a helpful mentor for both subject matter and language proficiency.
"""

        # Create model with system instruction
        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=system_instruction.strip()
        )
        
        # Start chat session with retrieved history from Database
        if history_context:
            chat = model.start_chat(history=history_context)
            response = chat.send_message(user_text)
        else:
            # No history, just generate content
            response = model.generate_content(user_text)
        
        # Reset quota flag on successful call
        _QUOTA_EXHAUSTED = False
        _QUOTA_EXHAUSTED_UNTIL = None
        
        # Handle response - check if response has text attribute
        try:
            response_text = response.text
        except AttributeError:
            # Try alternative response structure
            if hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
            elif hasattr(response, 'parts') and response.parts:
                response_text = response.parts[0].text
            else:
                raise AttributeError("Response object does not have expected structure")
        
        return response_text
        
    except Exception as e:
        error_str = str(e)
        error_type = type(e).__name__
        
        # Print detailed error for debugging
        import traceback
        error_traceback = traceback.format_exc()
        print(f"AI Brain Error ({error_type}): {error_str}")
        print(f"Full traceback:\n{error_traceback}")
        
        # Handle quota/rate limit errors
        if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
            print("⚠️ Gemini API quota exhausted in get_gemini_response.")
            
            # Extract retry delay if available
            import re
            retry_match = re.search(r'retry in (\d+)', error_str, re.IGNORECASE)
            if retry_match:
                retry_seconds = int(retry_match.group(1))
                from django.utils import timezone
                from datetime import timedelta
                _QUOTA_EXHAUSTED_UNTIL = timezone.now() + timedelta(seconds=retry_seconds + 10)
            else:
                # Default: wait 1 hour
                from django.utils import timezone
                from datetime import timedelta
                _QUOTA_EXHAUSTED_UNTIL = timezone.now() + timedelta(hours=1)
            
            _QUOTA_EXHAUSTED = True
            
            # Return user-friendly message
            wait_time = _QUOTA_EXHAUSTED_UNTIL - timezone.now() if _QUOTA_EXHAUSTED_UNTIL else None
            if wait_time:
                minutes = max(1, int(wait_time.total_seconds() / 60))
                return f"I'm currently experiencing high demand. Please try again in approximately {minutes} minute(s). For college-specific questions, please check the knowledge base or contact the college office directly."
            else:
                return "I'm currently experiencing high demand. Please try again later, or check the knowledge base for college-specific information."
        
        # Handle API key/auth errors
        if 'API key' in error_str or 'authentication' in error_str.lower() or '401' in error_str or '403' in error_str:
            print("⚠️ Gemini API authentication error. Check GEMINI_API_KEY.")
            return "AI service authentication error. Please contact the administrator."
        
        # Handle model errors
        if 'model' in error_str.lower() or 'MODEL' in error_str:
            print(f"⚠️ Gemini model error: {error_str}")
            return "AI model error. Please try again or contact the administrator."
        
        # Other errors - log but return generic message
        print(f"AI Brain Error: {error_str}")
        return f"I encountered an error processing your request. Please try rephrasing your question or try again later."


def get_hybrid_response(user_text, user=None):
    """
    Legacy wrapper - redirects to new KB-first chat router.
    This maintains backward compatibility while using the new system.
    
    Args:
        user_text: The user's message
        user: The User object (optional)
    
    Returns:
        tuple: (response_text, intent)
    """
    # Use new KB-first chat router
    from .chat_router import chat_reply
    return chat_reply(user_text, user)

