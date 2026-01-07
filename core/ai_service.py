import os
import json
from google import genai
from django.db.models import Q
from .models import ChatHistory, KnowledgeBase
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

MODEL = "gemini-2.5-flash"

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

def classify_intent(user_text):
    """
    Classify user question as COLLEGE_SPECIFIC or GENERAL using Gemini.
    
    Args:
        user_text: The user's message
    
    Returns:
        dict: {"intent_type": "COLLEGE_SPECIFIC" | "GENERAL", "confidence": "HIGH" | "MEDIUM" | "LOW"}
    """
    if not client:
        # Default to GENERAL if Gemini is not configured
        return {"intent_type": "GENERAL", "confidence": "LOW"}
    
    try:
        # Create a simple chat for intent classification
        chat = client.chats.create(
            model=MODEL,
            config={
                "system_instruction": INTENT_CLASSIFICATION_PROMPT.strip()
            }
        )
        
        # Send the classification request
        response = chat.send_message(user_text)
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
        print(f"Error in intent classification: {str(e)}")
        # Default to GENERAL on error
        return {"intent_type": "GENERAL", "confidence": "LOW"}


def query_knowledge_base(user_text):
    """
    Query the college knowledge base for relevant answers.
    
    Args:
        user_text: The user's message
    
    Returns:
        tuple: (answer_text or None, kb_entry or None)
    """
    try:
        # Search in approved knowledge base entries
        # Try exact match first
        kb_match = KnowledgeBase.objects.filter(
            approved=True,
            question__icontains=user_text
        ).first()
        
        if kb_match:
            return kb_match.answer, kb_match
        
        # Try searching in answer field as well
        kb_match = KnowledgeBase.objects.filter(
            approved=True,
            answer__icontains=user_text
        ).first()
        
        if kb_match:
            return kb_match.answer, kb_match
        
        # Try keyword matching (split user text into keywords)
        keywords = user_text.lower().split()
        for keyword in keywords:
            if len(keyword) > 3:  # Only search for words longer than 3 chars
                kb_match = KnowledgeBase.objects.filter(
                    approved=True
                ).filter(
                    Q(question__icontains=keyword) | Q(answer__icontains=keyword)
                ).first()
                
                if kb_match:
                    return kb_match.answer, kb_match
        
        return None, None
        
    except Exception as e:
        print(f"Error querying knowledge base: {str(e)}")
        return None, None


def get_gemini_response(user_text, user=None, is_college_context=False):
    """
    Get response from Gemini AI.
    
    Args:
        user_text: The user's message
        user: The User object (optional)
        is_college_context: Whether this is a college-specific question that needs context
    
    Returns:
        str: Response text
    """
    if not client:
        return "AI service is not configured. Please set GEMINI_API_KEY in your .env file."
    
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
            for chat in reversed(recent_chats):
                if chat.message:
                    history_context.append({"role": "user", "parts": [{"text": chat.message}]})
                if chat.response:
                    history_context.append({"role": "model", "parts": [{"text": chat.response}]})

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

        # Start chat session with retrieved history from Database
        chat = client.chats.create(
            model=MODEL,
            history=history_context,
            config={
                "system_instruction": system_instruction.strip()
            }
        )
        
        response = chat.send_message(user_text)
        return response.text
        
    except Exception as e:
        return f"AI Brain Error: {str(e)}"


def get_hybrid_response(user_text, user=None):
    """
    Get AI response using intent classification, then route to Knowledge Base or Gemini.
    
    Flow:
    1. Classify intent (COLLEGE_SPECIFIC or GENERAL)
    2. If COLLEGE_SPECIFIC:
       - Query Knowledge Base
       - If found, return KB answer
       - If not found, use Gemini with college context
    3. If GENERAL:
       - Use Gemini directly
    
    Args:
        user_text: The user's message
        user: The User object (optional)
    
    Returns:
        tuple: (response_text, intent)
    """
    # Step 1: Classify intent
    intent_classification = classify_intent(user_text)
    intent_type = intent_classification.get("intent_type", "GENERAL")
    
    # Step 2: Route based on intent
    if intent_type == "COLLEGE_SPECIFIC":
        # Query Knowledge Base first
        kb_answer, kb_entry = query_knowledge_base(user_text)
        
        if kb_answer:
            # Found in Knowledge Base
            return kb_answer, "kb_match"
        else:
            # Not found in KB, use Gemini with college context
            response_text = get_gemini_response(user_text, user, is_college_context=True)
            return response_text, "ai_fallback"
    else:
        # GENERAL intent - use Gemini directly
        response_text = get_gemini_response(user_text, user, is_college_context=False)
        return response_text, "ai_fallback"

