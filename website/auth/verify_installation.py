#!/usr/bin/env python3
"""
Authentication System Verification Script

Run this script to verify the authentication system is properly installed
and integrated with the Flask application.

Usage:
    python website/auth/verify_installation.py
"""

import sys
import os
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_success(message):
    print(f"{GREEN}✓{RESET} {message}")


def print_error(message):
    print(f"{RED}✗{RESET} {message}")


def print_warning(message):
    print(f"{YELLOW}⚠{RESET} {message}")


def print_info(message):
    print(f"{BLUE}ℹ{RESET} {message}")


def check_file_exists(filepath, description):
    """Check if a file exists and report the result."""
    if os.path.exists(filepath):
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} not found: {filepath}")
        return False


def check_import(module_path, description):
    """Check if a module can be imported."""
    try:
        __import__(module_path)
        print_success(f"{description} can be imported")
        return True
    except ImportError as e:
        print_error(f"{description} import failed: {e}")
        return False


def main():
    print("\n" + "="*70)
    print(f"{BLUE}Authentication System Verification{RESET}")
    print("="*70 + "\n")

    all_checks_passed = True

    # 1. Check Python Files
    print(f"\n{BLUE}[1] Checking Python Files{RESET}")
    print("-" * 70)

    website_dir = Path(__file__).parent.parent
    auth_dir = website_dir / 'auth'

    python_files = [
        (auth_dir / '__init__.py', "Auth blueprint init"),
        (auth_dir / 'routes.py', "Auth routes"),
        (auth_dir / 'forms.py', "Auth forms"),
        (auth_dir / 'decorators.py', "Auth decorators"),
    ]

    for filepath, description in python_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False

    # 2. Check Template Files
    print(f"\n{BLUE}[2] Checking Template Files{RESET}")
    print("-" * 70)

    template_dir = website_dir / 'templates' / 'auth'

    template_files = [
        (template_dir / 'login.html', "Login template"),
        (template_dir / 'register.html', "Register template"),
        (template_dir / 'reset_password_request.html', "Password reset request template"),
        (template_dir / 'reset_password.html', "Password reset template"),
        (template_dir / 'profile.html', "Profile template"),
    ]

    for filepath, description in template_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False

    # 3. Check Documentation Files
    print(f"\n{BLUE}[3] Checking Documentation{RESET}")
    print("-" * 70)

    doc_files = [
        (auth_dir / 'AUTH_README.md', "Auth README"),
        (auth_dir / 'IMPLEMENTATION_SUMMARY.md', "Implementation summary"),
    ]

    for filepath, description in doc_files:
        if not check_file_exists(filepath, description):
            all_checks_passed = False

    # 4. Check Module Imports
    print(f"\n{BLUE}[4] Checking Module Imports{RESET}")
    print("-" * 70)

    # Add parent directory to Python path
    sys.path.insert(0, str(website_dir.parent))

    imports = [
        ('website.auth', "Auth blueprint"),
        ('website.auth.routes', "Auth routes"),
        ('website.auth.forms', "Auth forms"),
        ('website.auth.decorators', "Auth decorators"),
    ]

    for module_path, description in imports:
        if not check_import(module_path, description):
            all_checks_passed = False

    # 5. Check Flask-Login Integration
    print(f"\n{BLUE}[5] Checking Flask-Login Integration{RESET}")
    print("-" * 70)

    try:
        from website import create_app
        app = create_app('testing')

        with app.app_context():
            # Check if login_manager is configured
            from flask_login import LoginManager, current_user
            login_manager = app.extensions.get('login_manager')

            if login_manager:
                print_success("Flask-Login is configured")

                if hasattr(login_manager, 'login_view'):
                    if login_manager.login_view == 'auth.login':
                        print_success(f"Login view set correctly: {login_manager.login_view}")
                    else:
                        print_warning(f"Login view: {login_manager.login_view} (expected 'auth.login')")
                else:
                    print_error("Login view not configured")
                    all_checks_passed = False
            else:
                print_error("Flask-Login not initialized")
                all_checks_passed = False

    except Exception as e:
        print_error(f"Flask-Login check failed: {e}")
        all_checks_passed = False

    # 6. Check Blueprint Registration
    print(f"\n{BLUE}[6] Checking Blueprint Registration{RESET}")
    print("-" * 70)

    try:
        from website import create_app
        app = create_app('testing')

        # Check if auth blueprint is registered
        auth_bp_registered = any(bp.name == 'auth' for bp in app.blueprints.values())

        if auth_bp_registered:
            print_success("Auth blueprint is registered")

            # Check if routes are accessible
            with app.test_client() as client:
                routes_to_check = [
                    ('/auth/login', 'Login route'),
                    ('/auth/register', 'Register route'),
                    ('/auth/reset-password-request', 'Password reset request route'),
                ]

                for route, description in routes_to_check:
                    response = client.get(route)
                    if response.status_code == 200:
                        print_success(f"{description} accessible: {route}")
                    else:
                        print_error(f"{description} returned {response.status_code}: {route}")
                        all_checks_passed = False
        else:
            print_error("Auth blueprint not registered")
            all_checks_passed = False

    except Exception as e:
        print_error(f"Blueprint registration check failed: {e}")
        all_checks_passed = False

    # 7. Check User Model Integration
    print(f"\n{BLUE}[7] Checking User Model Integration{RESET}")
    print("-" * 70)

    try:
        from website.models.user import User, UserRole

        print_success("User model imported successfully")

        # Check if UserRole enum exists
        if hasattr(UserRole, 'USER') and hasattr(UserRole, 'ADMIN') and hasattr(UserRole, 'COACH'):
            print_success("UserRole enum has all required roles")
        else:
            print_error("UserRole enum missing required roles")
            all_checks_passed = False

        # Check if User model has required methods
        required_methods = ['set_password', 'check_password', 'is_locked', 'lock_account',
                          'unlock_account', 'is_admin', 'is_coach']

        for method in required_methods:
            if hasattr(User, method):
                print_success(f"User model has method: {method}")
            else:
                print_error(f"User model missing method: {method}")
                all_checks_passed = False

    except Exception as e:
        print_error(f"User model check failed: {e}")
        all_checks_passed = False

    # 8. Check Dependencies
    print(f"\n{BLUE}[8] Checking Dependencies{RESET}")
    print("-" * 70)

    dependencies = [
        ('flask', 'Flask'),
        ('flask_login', 'Flask-Login'),
        ('flask_wtf', 'Flask-WTF'),
        ('wtforms', 'WTForms'),
        ('bcrypt', 'bcrypt'),
        ('itsdangerous', 'itsdangerous'),
    ]

    for module, name in dependencies:
        if not check_import(module, name):
            print_warning(f"{name} not installed (may be needed)")

    # Final Summary
    print("\n" + "="*70)
    if all_checks_passed:
        print(f"{GREEN}✓ All Checks Passed!{RESET}")
        print("\nThe authentication system is properly installed and ready to use.")
        print("\nNext Steps:")
        print("  1. Set environment variables (SECRET_KEY, POSTGRES_PASSWORD)")
        print("  2. Run database migrations: flask db upgrade")
        print("  3. Start the Flask application")
        print("  4. Test routes manually:")
        print("     - http://localhost:8080/auth/register")
        print("     - http://localhost:8080/auth/login")
        print("     - http://localhost:8080/auth/profile")
        return 0
    else:
        print(f"{RED}✗ Some Checks Failed{RESET}")
        print("\nPlease review the errors above and fix any issues.")
        return 1
    print("="*70 + "\n")


if __name__ == '__main__':
    sys.exit(main())
