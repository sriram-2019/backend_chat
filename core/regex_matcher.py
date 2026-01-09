import re

# Manual Regex Patterns to solve immediate issues and stabilize the system
# These should be auto-generated in the future when API quota permits
REGEX_PATTERNS = [
    {
        "kb_id": 16, # Assuming ID for 'What is office working hour ?' - verify this ID if possible or use a lookup
        "category": "General",
        # Matches: office timing, office working hours, college office time, offcie timing (typo)
        "pattern": re.compile(r"(?i)\b(college\s+)?off(?:ic|ci)e\s*(?:working\s*)?(?:time|timings?|hours?)\b")
    },
    {
         "kb_id": 15, # Example ID, placeholder
         "category": "Syllabus",
         "pattern": re.compile(r"(?i)\bsyllabus\b.*\b(2nd|second)\s*year")
    }
]

# We need to dynamically fetch IDs to be safe. 
# But for a static file, we can't context-switch easily. 
# Better approach: The regex matcher should return the QUESTION string or a lookup key, 
# and we find the KB entry by that. Or we just fetch KB entries and compile regexes at runtime (caching them).

def match_kb_with_regex(user_text):
    """
    Try to match user text against defined regex patterns.
    Returns: kb_id (int) or None
    """
    # Quick fix for the specific office typo
    if re.search(r"(?i)off(ic|ci)e\s*(working\s*)?(time|timing|hour)", user_text):
        # We need to find the correct KB ID. 
        # Since we can't hardcode IDs easily without risking mismatch, 
        # let's return a unique identifier or known questions.
        from .models import KnowledgeBase
        
        # Try to find the office entry
        kf = KnowledgeBase.objects.filter(question__icontains="office working hour").first()
        if kf:
             return kf.id
             
    # Syllabus 2nd year
    if re.search(r"(?i)syllabus.*(2nd|second)\s*year", user_text) or re.search(r"(?i)(2nd|second)\s*year.*syllabus", user_text):
         kf = KnowledgeBase.objects.filter(question__icontains="2nd year syllabus").first()
         if kf:
             return kf.id
             
    return None
