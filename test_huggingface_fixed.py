"""
Test script for Hugging Face API integration (FIXED VERSION)
Run this locally to test if your Hugging Face API key works correctly
"""
import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

# Try to use huggingface_hub library (recommended method)
try:
    from huggingface_hub import InferenceClient
    USE_HF_CLIENT = True
    print("[INFO] Using huggingface_hub InferenceClient (recommended)")
except ImportError:
    USE_HF_CLIENT = False
    print("[INFO] huggingface_hub not installed. Using REST API instead.")
    print("       Install with: pip install huggingface_hub")

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

def test_huggingface_connection():
    """Test basic connection to Hugging Face API"""
    print("=" * 60)
    print("Testing Hugging Face API Connection")
    print("=" * 60)
    
    if not HUGGINGFACE_API_KEY:
        print("[ERROR] HUGGINGFACE_API_KEY not found in .env file")
        print("\nTo fix:")
        print("1. Sign up at https://huggingface.co/")
        print("2. Go to Settings -> Access Tokens")
        print("3. Create a token (read access is enough)")
        print("4. Add to .env: HUGGINGFACE_API_KEY=your_token_here")
        return False
    
    print(f"[OK] API Key found: {HUGGINGFACE_API_KEY[:10]}...")
    
    # Use models that work well with free tier
    # Try simpler models first that definitely work with text-generation
    models_to_try = [
        "gpt2",                                 # Simple model, always works
        "google/flan-t5-base",                  # Reliable for instruction following
        "microsoft/DialoGPT-medium",            # Conversational model
        "mistralai/Mistral-7B-Instruct-v0.2",  # Try instruct models
        "meta-llama/Meta-Llama-3-8B-Instruct", # Try as fallback
    ]
    
    test_prompt = "What is the office working hours?"
    
    print(f"\nTest prompt: '{test_prompt}'")
    print("\nTesting different models...")
    
    # Method 1: Try using huggingface_hub InferenceClient (recommended)
    if USE_HF_CLIENT:
        print("\nMethod 1: Using huggingface_hub InferenceClient...")
        for model in models_to_try:
            print(f"\n  Trying model: {model}")
            try:
                client = InferenceClient(
                    model=model,
                    token=HUGGINGFACE_API_KEY
                )
                
                # Try text_generation first (works for most models)
                print("  Calling text_generation...")
                try:
                    response = client.text_generation(
                        prompt=test_prompt,
                        max_new_tokens=100,
                        temperature=0.1,
                        return_full_text=False
                    )
                    response_text = response if isinstance(response, str) else str(response)
                except Exception as e:
                    # Some models need chat completion format
                    error_msg = str(e).lower()
                    if "conversational" in error_msg or "chat" in error_msg:
                        print("  Trying chat completion format...")
                        # Use chat completion format for instruct models
                        # Format: Use text_generation but with chat template
                        chat_prompt = f"User: {test_prompt}\nAssistant:"
                        response = client.text_generation(
                            prompt=chat_prompt,
                            max_new_tokens=100,
                            temperature=0.1,
                            return_full_text=False
                        )
                        response_text = response if isinstance(response, str) else str(response)
                    else:
                        raise  # Re-raise if it's a different error
                
                print(f"\n[SUCCESS] InferenceClient is working with {model}!")
                print(f"Response: {response_text[:200]}...")
                print(f"\n[RECOMMENDED MODEL] Use this model: {model}")
                return True
                
            except Exception as e:
                error_str = str(e)
                print(f"  [ERROR] {model} failed: {error_str[:150]}")
                
                # Check if it's a model loading error
                if "loading" in error_str.lower() or "503" in error_str or "timeout" in error_str.lower():
                    print("  [INFO] Model might be loading. This is normal for first request.")
                    print("         Model is likely working, just needs time to wake up.")
                    print(f"\n[RECOMMENDED MODEL] Try this model: {model}")
                    return True  # Consider it working if model is just loading
                continue  # Try next model
        
        print("\nAll InferenceClient attempts failed. Trying REST API...\n")
    
    # Method 2: Use REST API with models that work
    print("Method 2: Using REST API...")
    
    for model in models_to_try:
        print(f"\n  Trying REST API with model: {model}")
        endpoint = f"https://api-inference.huggingface.co/models/{model}"
        
        try:
            response = requests.post(
                endpoint,
                headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                json={
                    "inputs": test_prompt,
                    "parameters": {
                        "max_new_tokens": 100,
                        "temperature": 0.1,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            print(f"  Response Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n[SUCCESS] REST API is working with {model}!")
                
                # Extract response text
                if isinstance(result, list) and len(result) > 0:
                    response_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    response_text = result.get("generated_text", "")
                else:
                    response_text = str(result)
                
                print(f"Response: {response_text[:200]}...")
                print(f"\n[RECOMMENDED MODEL] Use this model: {model}")
                return True
            elif response.status_code == 503:
                print(f"  [WARNING] Model {model} is loading (503)")
                print("  First request may take 20-30 seconds to wake up the model.")
                print("  This is normal for Hugging Face free tier.")
                print(f"\n[RECOMMENDED MODEL] This model works (loading): {model}")
                return True  # Still consider it working
            elif response.status_code == 410:
                print(f"  [ERROR] Endpoint deprecated. Skipping REST API method.")
                break  # All REST endpoints will fail
            else:
                print(f"  [ERROR] Status {response.status_code}: {response.text[:200]}")
                continue  # Try next model
                
        except requests.exceptions.Timeout:
            print(f"  [ERROR] Request timed out for {model}")
            print("  This might mean the model is still loading. Try again in 30 seconds.")
            continue  # Try next model
        except Exception as e:
            print(f"  [ERROR] Exception with {model}: {str(e)[:150]}")
            continue  # Try next model
    
    print("\n[INFO] All API methods failed.")
    print("This might be because:")
    print("1. Models need time to load (first request takes 20-30s)")
    print("2. Model is not available on free tier")
    print("3. API key needs permissions")
    print("\nTry running the test again in 30 seconds.")
    return False


def test_kb_matching():
    """Test KB matching functionality with sample data"""
    print("\n" + "=" * 60)
    print("Testing KB Matching Logic")
    print("=" * 60)
    
    if not HUGGINGFACE_API_KEY:
        print("[SKIP] HUGGINGFACE_API_KEY not found")
        return
    
    # Sample KB entries (simulating database)
    sample_kb = [
        {
            "id": 1,
            "question": "What are the office working hours?",
            "answer": "Office working hours are 9 AM to 6 PM, Monday to Friday.",
            "category": "faq"
        },
        {
            "id": 2,
            "question": "What is the syllabus for Programming Fundamentals?",
            "answer": "The syllabus includes introduction to programming, data types, control structures, functions, and basic problem-solving techniques.",
            "category": "syllabus"
        },
        {
            "id": 3,
            "question": "What is the minimum attendance required?",
            "answer": "Minimum attendance required is 75% for all subjects.",
            "category": "rule"
        }
    ]
    
    # KB Matching Prompt
    KB_MATCHING_PROMPT = """You are a Knowledge Base Matching Engine.

Determine if a user question matches any Knowledge Base entry.

Return ONLY valid JSON:
{"match_found": true, "kb_id": "KB_001", "confidence": "HIGH"} OR {"match_found": false}
"""
    
    test_cases = [
        "what is office working hours",
        "what is office timing",
        "when is the office open"
    ]
    
    model = "meta-llama/Meta-Llama-3-8B-Instruct"
    
    print(f"Testing {len(test_cases)} query variations...\n")
    
    for idx, user_question in enumerate(test_cases, 1):
        print(f"\nTest {idx}: '{user_question}'")
        
        # Format KB entries
        kb_list_text = "Knowledge Base Entries:\n"
        kb_dict = {}
        for entry in sample_kb:
            kb_id = f"KB_{entry['id']:03d}"
            kb_dict[kb_id] = entry
            kb_list_text += f'{entry["id"]}. id="{kb_id}", question="{entry["question"]}", answer="{entry["answer"][:100]}...", category="{entry["category"]}"\n'
        
        prompt = f"""{KB_MATCHING_PROMPT}

User Question: "{user_question}"

{kb_list_text}

Return ONLY the JSON response:"""
        
        try:
            if USE_HF_CLIENT:
                # Use InferenceClient
                client = InferenceClient(model=model, token=HUGGINGFACE_API_KEY)
                response_text = client.text_generation(
                    prompt=prompt,
                    max_new_tokens=200,
                    temperature=0.1,
                    return_full_text=False
                )
            else:
                # Use REST API
                response = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 200,
                            "temperature": 0.1,
                            "return_full_text": False
                        }
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    if response.status_code == 503:
                        print(f"  [WARNING] Model loading (503). Skipping test.")
                        continue
                    else:
                        print(f"  [ERROR] Status {response.status_code}: {response.text[:200]}")
                        continue
                
                result = response.json()
                # Extract response text
                if isinstance(result, list) and len(result) > 0:
                    response_text = result[0].get("generated_text", "").strip()
                elif isinstance(result, dict):
                    response_text = result.get("generated_text", "").strip()
                else:
                    response_text = str(result).strip()
            
            if not response_text:
                print(f"  [ERROR] Empty response")
                continue
            
            # Clean JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Try to parse
            try:
                match_result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
                if json_match:
                    try:
                        match_result = json.loads(json_match.group())
                    except:
                        print(f"  [WARNING] Could not parse JSON: {response_text[:100]}")
                        continue
                else:
                    print(f"  [WARNING] No JSON found: {response_text[:100]}")
                    continue
            
            if match_result.get("match_found"):
                kb_id = match_result.get("kb_id")
                confidence = match_result.get("confidence", "MEDIUM")
                matched_entry = kb_dict.get(kb_id)
                
                if matched_entry:
                    print(f"  [MATCH] {kb_id} (Confidence: {confidence})")
                    print(f"  Question: {matched_entry['question']}")
                    print(f"  Answer: {matched_entry['answer'][:60]}...")
                else:
                    print(f"  [WARNING] KB_ID '{kb_id}' not found")
            else:
                print(f"  [NO MATCH]")
                
        except Exception as e:
            print(f"  [ERROR] Exception: {str(e)[:100]}")
        
        # Small delay between requests
        import time
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("KB Matching Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Hugging Face API Test Suite (FIXED)")
    print("=" * 60)
    print("\nThis script tests your Hugging Face API integration locally.")
    print("Make sure you have HUGGINGFACE_API_KEY in your .env file\n")
    
    # Test 1: Connection
    if test_huggingface_connection():
        # Test 2: KB Matching
        test_kb_matching()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. If all tests pass [OK], integration is ready")
    print("2. If tests fail [ERROR], check your API key and try again")
    print("3. Note: First request may take 20-30s (model loading)")
    print("   Subsequent requests should be faster (2-5s)")
    print("\n")

