#!/usr/bin/env python3
"""
Test script to verify authentication fixes:
1. Navbar z-index fix
2. Virtual pages appearing after login with credentials: 'include'
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8080"

def test_login_and_virtual_pages():
    """Test that virtual pages appear after authentication"""

    # Create a session to maintain cookies
    session = requests.Session()

    print("=" * 60)
    print("Testing Authentication and Virtual Pages")
    print("=" * 60)

    # Step 1: Get login page and extract CSRF token
    print("\n1. Fetching login page...")
    login_page = session.get(f"{BASE_URL}/auth/login")
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
    print(f"   ✓ CSRF token obtained: {csrf_token[:20]}...")

    # Step 2: Login with admin credentials
    print("\n2. Logging in as admin...")
    login_data = {
        'username_or_email': 'admin',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    login_response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=False)

    if login_response.status_code in [302, 303]:
        print(f"   ✓ Login successful (redirect to {login_response.headers.get('Location')})")
    else:
        print(f"   ✗ Login failed with status {login_response.status_code}")
        print(f"   Response: {login_response.text[:200]}")
        return False

    # Step 3: Test API endpoint without credentials (should not show virtual pages)
    print("\n3. Testing API without credentials...")
    public_response = requests.get(f"{BASE_URL}/api/project/Health_and_Fitness/files")
    public_files = public_response.json()
    print(f"   Files without auth: {len(public_files)} files")
    print(f"   Files: {public_files}")

    virtual_pages_public = [f for f in public_files if f.startswith('data/')]
    if virtual_pages_public:
        print(f"   ✗ ERROR: Virtual pages should not appear without auth!")
    else:
        print(f"   ✓ Virtual pages correctly hidden without auth")

    # Step 4: Test API endpoint with session cookies (should show virtual pages)
    print("\n4. Testing API with authenticated session...")
    auth_response = session.get(f"{BASE_URL}/api/project/Health_and_Fitness/files")
    auth_files = auth_response.json()
    print(f"   Files with auth: {len(auth_files)} files")
    print(f"   Files: {auth_files}")

    virtual_pages_auth = [f for f in auth_files if f.startswith('data/')]
    print(f"\n   Virtual pages found: {len(virtual_pages_auth)}")
    for vp in virtual_pages_auth:
        print(f"     - {vp}")

    if len(virtual_pages_auth) == 5:
        print(f"   ✓ All 5 virtual pages correctly appear with auth!")
        return True
    else:
        print(f"   ✗ ERROR: Expected 5 virtual pages, found {len(virtual_pages_auth)}")
        return False

def test_navbar_css():
    """Test that navbar has proper z-index in CSS"""
    print("\n\n" + "=" * 60)
    print("Testing Navbar Z-Index Fix")
    print("=" * 60)

    with open('/Users/nathanbowman/primary-assistant/website/static/css/style.css', 'r') as f:
        css_content = f.read()

    # Check if navbar has z-index
    if 'z-index: 1000' in css_content and '.navbar' in css_content:
        print("   ✓ Navbar CSS has z-index: 1000")

        # Extract the navbar CSS block
        navbar_start = css_content.find('.navbar {')
        if navbar_start != -1:
            navbar_end = css_content.find('}', navbar_start)
            navbar_css = css_content[navbar_start:navbar_end+1]
            print(f"\n   Navbar CSS block:\n{navbar_css}")
        return True
    else:
        print("   ✗ ERROR: Navbar CSS missing z-index: 1000")
        return False

def test_fetch_credentials():
    """Test that JavaScript fetch calls include credentials: 'include'"""
    print("\n\n" + "=" * 60)
    print("Testing JavaScript Fetch Credentials")
    print("=" * 60)

    # Check script.js
    print("\n1. Checking website/static/js/script.js...")
    with open('/Users/nathanbowman/primary-assistant/website/static/js/script.js', 'r') as f:
        script_js = f.read()

    fetch_calls = script_js.count("credentials: 'include'")
    print(f"   Found {fetch_calls} fetch calls with credentials: 'include'")

    if fetch_calls >= 3:
        print(f"   ✓ script.js has proper credentials in fetch calls")
    else:
        print(f"   ✗ ERROR: Expected at least 3 fetch calls with credentials")

    # Check graphs.js
    print("\n2. Checking website/static/js/graphs.js...")
    with open('/Users/nathanbowman/primary-assistant/website/static/js/graphs.js', 'r') as f:
        graphs_js = f.read()

    fetch_calls_graphs = graphs_js.count("credentials: 'include'")
    print(f"   Found {fetch_calls_graphs} fetch calls with credentials: 'include'")

    if fetch_calls_graphs >= 1:
        print(f"   ✓ graphs.js has proper credentials in fetch calls")
        return True
    else:
        print(f"   ✗ ERROR: Expected at least 1 fetch call with credentials")
        return False

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AUTHENTICATION FIXES VERIFICATION" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")

    # Run all tests
    css_ok = test_navbar_css()
    js_ok = test_fetch_credentials()
    api_ok = test_login_and_virtual_pages()

    # Summary
    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Navbar CSS z-index:        {'✓ PASS' if css_ok else '✗ FAIL'}")
    print(f"  JavaScript credentials:    {'✓ PASS' if js_ok else '✗ FAIL'}")
    print(f"  API authentication:        {'✓ PASS' if api_ok else '✗ FAIL'}")
    print("=" * 60)

    if css_ok and js_ok and api_ok:
        print("\n✅ ALL FIXES VERIFIED SUCCESSFULLY!")
    else:
        print("\n❌ SOME TESTS FAILED - REVIEW ABOVE OUTPUT")
    print("\n")
