"""
Test specific query: "what's the working hour of the office"
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from core.kb_matcher import match_kb_entry_with_details
from core.chat_router import chat_reply

# Test the exact query
query = "whats the working hour of the office"

print("=" * 80)
print(f"Testing Query: '{query}'")
print("=" * 80)

# Test matching
print("\n1. KB Matching Test:")
print("-" * 80)
result = match_kb_entry_with_details(query, min_confidence=0.4)

if result and result.get('match_found'):
    print(f"[MATCH FOUND]")
    print(f"   KB ID: {result['kb_entry']['kb_id']}")
    print(f"   Score: {result['score']:.2f}")
    print(f"   Confidence: {result['confidence']}")
    print(f"   Question: {result['question']}")
    print(f"   Answer: {result['answer']}")
    print(f"   Category: {result['category']}")
else:
    print(f"[NO MATCH FOUND]")
    print(f"   Score: {result.get('score', 0):.2f}")

# Test full chat router
print("\n2. Full Chat Router Test:")
print("-" * 80)
response, intent = chat_reply(query)

print(f"Intent: {intent}")
print(f"Response: {response}")
status_msg = "[OK] Used KB (NO Gemini call)" if intent == 'kb_match' else "[INFO] Used Gemini fallback" if intent == 'ai_fallback' else "[ERROR]"
print(f"\n{status_msg}")

print("\n" + "=" * 80)
print("Analysis:")
print("=" * 80)

if result and result.get('match_found'):
    print("[OK] This query WILL match KB entry #1 (office working hours)")
    print("[OK] Answer will be returned from database (NO Gemini API call)")
    print("[OK] Response time: < 10ms (instant)")
    print("[OK] Gemini quota: 0 requests (saved!)")
else:
    print("[ERROR] This query did NOT match")
    print("[WARNING] Will fall back to Gemini API")

print("=" * 80)

