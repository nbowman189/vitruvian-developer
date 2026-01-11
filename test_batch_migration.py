#!/usr/bin/env python3
"""
Test script to verify Google Gemini SDK migration and batch records functionality.
Tests that multiple function calls work correctly with the new google.genai SDK.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8001"
LOGIN_URL = f"{BASE_URL}/auth/login"
AI_COACH_URL = f"{BASE_URL}/api/ai-coach/message"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"


def login():
    """Login and get session cookie."""
    print("🔐 Logging in...")

    # Create session
    session = requests.Session()

    # Get login page to obtain CSRF token
    response = session.get(f"{BASE_URL}/auth/login")

    # Extract CSRF token from HTML
    import re
    csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)

    if not csrf_match:
        print("❌ Could not find CSRF token")
        return None

    csrf_token = csrf_match.group(1)
    print(f"   CSRF token: {csrf_token[:20]}...")

    # Login with CSRF token
    data = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrf_token": csrf_token
    }

    response = session.post(LOGIN_URL, data=data, allow_redirects=False)

    if response.status_code in [200, 302]:
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text[:500])
        return None


def test_simple_message(session):
    """Test 1: Simple greeting (no function calling)"""
    print("\n📝 Test 1: Simple greeting")

    payload = {
        "message": "Hello",
        "conversation_id": None
    }

    response = session.post(AI_COACH_URL, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response received: {data.get('message', '')[:100]}")
        return data.get('conversation_id')
    else:
        print(f"❌ Test failed: {response.status_code}")
        print(response.text[:500])
        return None


def test_single_function_call(session, conversation_id):
    """Test 2: Single function call (create_health_metric)"""
    print("\n📝 Test 2: Single function call")

    payload = {
        "message": "I weighed 176 lbs today",
        "conversation_id": conversation_id
    }

    response = session.post(AI_COACH_URL, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data.get('message', '')[:100]}")

        # Check if function call was made
        if data.get('function_call'):
            fc = data['function_call']
            print(f"   Function called: {fc.get('name')}")
            print(f"   Args: {json.dumps(fc.get('args', {}), indent=2)[:200]}")

        return data.get('conversation_id')
    else:
        print(f"❌ Test failed: {response.status_code}")
        print(response.text[:500])
        return conversation_id


def test_batch_function_calls(session, conversation_id):
    """Test 3: Multiple function calls in single message (CRITICAL TEST)"""
    print("\n📝 Test 3: Batch function calls (CRITICAL)")

    payload = {
        "message": "Today I weighed 176.5 lbs, did a 60-minute strength workout, and ate breakfast with 650 calories and 45g protein",
        "conversation_id": conversation_id
    }

    response = session.post(AI_COACH_URL, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response: {data.get('message', '')[:100]}")

        # Check if function call was made
        if data.get('function_call'):
            fc = data['function_call']

            # Check if multiple function calls
            if fc.get('name') == 'multiple_function_calls':
                function_calls = fc.get('function_calls', [])
                print(f"   ✅ MULTIPLE FUNCTION CALLS DETECTED: {len(function_calls)}")

                for i, call in enumerate(function_calls, 1):
                    print(f"   {i}. {call.get('name')}")
                    print(f"      Args: {json.dumps(call.get('args', {}), indent=6)[:150]}")

                return True
            else:
                print(f"   ⚠️  Single function call: {fc.get('name')}")
                print(f"      Expected multiple_function_calls wrapper")
                return False
        else:
            print("   ⚠️  No function call in response")
            return False
    else:
        print(f"❌ Test failed: {response.status_code}")
        print(response.text[:500])
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Google Gemini SDK Migration Test Suite")
    print("Testing: google-genai SDK and batch function calling")
    print("=" * 60)

    # Login
    session = login()
    if not session:
        print("\n❌ Cannot proceed without authentication")
        return

    time.sleep(1)

    # Test 1: Simple message
    conversation_id = test_simple_message(session)
    time.sleep(2)

    # Test 2: Single function call
    if conversation_id:
        conversation_id = test_single_function_call(session, conversation_id)
        time.sleep(2)

    # Test 3: Batch function calls (CRITICAL)
    if conversation_id:
        batch_success = test_batch_function_calls(session, conversation_id)

        print("\n" + "=" * 60)
        if batch_success:
            print("🎉 MIGRATION SUCCESSFUL!")
            print("✅ Multiple function calls working correctly")
        else:
            print("⚠️  MIGRATION INCOMPLETE")
            print("❌ Multiple function calls not detected")
        print("=" * 60)


if __name__ == "__main__":
    main()
