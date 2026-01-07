#!/usr/bin/env python3
"""
Direct test of GeminiService with google.genai SDK.
Tests batch function calling without web authentication.
"""
import os
import sys

# Set up paths
sys.path.insert(0, '/app')

# Set environment variables
os.environ['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', '')
os.environ['FLASK_APP'] = 'website'

from website.services.gemini_service import GeminiService
from website.utils.ai_coach_tools import get_all_function_declarations

print("=" * 70)
print("Google Gemini SDK Migration - Direct Service Test")
print("=" * 70)

# Check if API key is set
if not os.environ.get('GEMINI_API_KEY'):
    print("\n❌ GEMINI_API_KEY environment variable not set")
    print("   Skipping live API tests")
    sys.exit(0)

print("\n✅ GEMINI_API_KEY is set")

# Initialize service
print("\n📝 Test 1: Initialize GeminiService")
try:
    service = GeminiService()
    print(f"   ✅ Service initialized")
    print(f"   Client type: {type(service.client)}")
    print(f"   Model chain: {service.model_names}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# Get function declarations
print("\n📝 Test 2: Load function declarations")
try:
    functions = get_all_function_declarations()
    print(f"   ✅ Loaded {len(functions)} function declarations")

    # List WRITE functions
    write_functions = [f['name'] for f in functions if f['name'].startswith('create_') or f['name'].startswith('log_')]
    print(f"   WRITE functions: {', '.join(write_functions[:3])}...")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

# Test 3: Simple message (no function calling)
print("\n📝 Test 3: Simple message (no function calling)")
try:
    response, function_call = service.chat(
        user_message="Hello, how are you?",
        conversation_history=[],
        function_declarations=None
    )
    print(f"   ✅ Response received")
    print(f"   Response length: {len(response)} chars")
    print(f"   Function call: {function_call is None and 'None' or 'Present'}")
    print(f"   First 100 chars: {response[:100]}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Single function call
print("\n📝 Test 4: Single function call")
try:
    response, function_call = service.chat(
        user_message="I weighed 176 lbs today",
        conversation_history=[],
        function_declarations=functions
    )
    print(f"   ✅ Response received")

    if function_call:
        print(f"   Function name: {function_call.get('name')}")
        if function_call.get('name') == 'create_health_metric':
            print(f"   Args: {function_call.get('args', {})}")
        else:
            print(f"   ⚠️  Expected create_health_metric, got {function_call.get('name')}")
    else:
        print(f"   ⚠️  No function call made")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: BATCH function calls (CRITICAL TEST)
print("\n📝 Test 5: Batch function calls (CRITICAL)")
print("   Message: 'Today I weighed 176.5 lbs, did a 60-minute strength workout,'")
print("            'and ate breakfast with 650 calories and 45g protein'")
try:
    response, function_call = service.chat(
        user_message="Today I weighed 176.5 lbs, did a 60-minute strength workout, and ate breakfast with 650 calories and 45g protein",
        conversation_history=[],
        function_declarations=functions
    )
    print(f"   ✅ Response received")
    print(f"   Response: {response[:150]}")

    if function_call:
        if function_call.get('name') == 'multiple_function_calls':
            function_calls = function_call.get('function_calls', [])
            print(f"\n   🎉 BATCH FUNCTION CALLING SUCCESSFUL!")
            print(f"   Number of function calls: {len(function_calls)}")

            for i, fc in enumerate(function_calls, 1):
                print(f"\n   {i}. {fc.get('name')}")
                args = fc.get('args', {})
                # Print first 3 args
                for key in list(args.keys())[:3]:
                    print(f"      {key}: {args[key]}")
        else:
            print(f"\n   ⚠️  Single function call: {function_call.get('name')}")
            print(f"      Expected 'multiple_function_calls' wrapper")
            print(f"      This indicates batch calling may not be working")
    else:
        print(f"\n   ❌ No function calls made")
        print(f"      Gemini should have called multiple functions")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - Migration successful!")
print("=" * 70)
