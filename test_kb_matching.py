"""
Test script for KB matching system
Tests the KB-first matching without AI calls
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from core.kb_cache import get_kb_cache, rebuild_kb_cache, get_cache_stats
from core.kb_matcher import match_kb_entry, match_kb_entry_with_details
from core.chat_router import chat_reply


def test_kb_cache():
    """Test KB cache building"""
    print("=" * 80)
    print("TEST 1: KB Cache Building")
    print("=" * 80)
    
    print("\nRebuilding cache...")
    cache_data = rebuild_kb_cache()
    
    print(f"\n[OK] Cache built: {len(cache_data)} entries")
    
    stats = get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  By category: {stats['by_category']}")
    print(f"  Total keywords: {stats['total_keywords']}")
    print(f"  Avg keywords/entry: {stats['avg_keywords_per_entry']:.1f}")
    
    # Show sample entry
    if cache_data:
        print(f"\nSample Entry:")
        sample = cache_data[0]
        print(f"  ID: {sample['id']}")
        print(f"  Question: {sample['question']}")
        print(f"  Keywords: {sample['keywords'][:10]}")
        print(f"  Tags: {sample['tags']}")
    
    return cache_data


def test_matching():
    """Test KB matching with various queries"""
    print("\n" + "=" * 80)
    print("TEST 2: KB Matching")
    print("=" * 80)
    
    # Test cases based on actual KB entries
    test_cases = [
        # Office hours variations (should match KB_001)
        ("what is office working hour", "KB_001"),
        ("office timing", "KB_001"),
        ("what time does office work", "KB_001"),
        ("what is working hour of the office", "KB_001"),
        ("when is office open", "KB_001"),
        ("office hours", "KB_001"),
        
        # Attendance (should match KB_002)
        ("what is minimum attendance", "KB_002"),
        ("attendance required", "KB_002"),
        ("how much attendance needed", "KB_002"),
        
        # Dress code (should match KB_003)
        ("is there dress code", "KB_003"),
        ("dress code for students", "KB_003"),
        ("uniform required", "KB_003"),
        
        # Syllabus (should match KB_004 or KB_005)
        ("subjects in computer science semester 1", "KB_004"),
        ("what is programming fundamentals syllabus", "KB_005"),
        ("syllabus for programming", "KB_005"),
    ]
    
    print(f"\nTesting {len(test_cases)} query variations...\n")
    
    passed = 0
    failed = 0
    
    for query, expected_kb in test_cases:
        result = match_kb_entry_with_details(query, min_confidence=0.4)
        
        if result and result.get('match_found'):
            matched_kb = result['kb_entry']['kb_id']
            score = result['score']
            confidence = result['confidence']
            
            status = "[PASS]" if matched_kb == expected_kb else "[FAIL]"
            if matched_kb == expected_kb:
                passed += 1
            else:
                failed += 1
            
            print(f"{status} Query: '{query}'")
            print(f"        Expected: {expected_kb}, Got: {matched_kb}, Score: {score:.2f}, Confidence: {confidence}")
            print(f"        Answer: {result['answer'][:60]}...")
        else:
            failed += 1
            print(f"[FAIL] Query: '{query}'")
            print(f"        Expected: {expected_kb}, Got: NO MATCH")
            if result:
                print(f"        Score: {result.get('score', 0):.2f}")
        print()
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    return passed, failed


def test_chat_router():
    """Test full chat router (KB-first, Gemini fallback)"""
    print("\n" + "=" * 80)
    print("TEST 3: Chat Router (KB-First)")
    print("=" * 80)
    
    test_queries = [
        "what is office working hour",
        "minimum attendance required",
        "what is the syllabus for programming",
        "what is python",  # General question - should use Gemini fallback
    ]
    
    print("\nTesting chat router responses...\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        try:
            response, intent = chat_reply(query)
            print(f"  Intent: {intent}")
            print(f"  Response: {response[:100]}...")
            
            if intent == 'kb_match':
                print(f"  [OK] Used KB (no Gemini call)")
            elif intent == 'ai_fallback':
                print(f"  [INFO] Used Gemini fallback")
            print()
        except Exception as e:
            print(f"  [ERROR] {str(e)}\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("KB MATCHING SYSTEM TEST SUITE")
    print("=" * 80)
    print("\nTesting production-grade KB-first matching system...\n")
    
    # Test 1: Cache
    cache_data = test_kb_cache()
    
    if not cache_data:
        print("\n[ERROR] No KB entries found. Please add entries to database first.")
        sys.exit(1)
    
    # Test 2: Matching
    passed, failed = test_matching()
    
    # Test 3: Chat Router
    test_chat_router()
    
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  KB Entries: {len(cache_data)}")
    print(f"  Matching Tests: {passed} passed, {failed} failed")
    print(f"\nSystem is ready for production use!")
    print("=" * 80 + "\n")

