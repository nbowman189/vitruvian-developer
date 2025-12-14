#!/usr/bin/env python3
"""
Configuration Verification Script

This script verifies that the configuration and dependencies are properly set up.

Usage:
    python scripts/verify_configuration.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_header(message):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")


def print_success(message):
    """Print success message"""
    print(f"✓ {message}")


def print_error(message):
    """Print error message"""
    print(f"✗ {message}")


def print_warning(message):
    """Print warning message"""
    print(f"⚠ {message}")


def check_env_file():
    """Check if .env file exists and has required variables"""
    print_header("Checking Environment File")

    env_file = PROJECT_ROOT / '.env'

    if not env_file.exists():
        print_error(".env file not found")
        print("  Run: cp .env.example .env")
        return False

    print_success(".env file exists")

    # Read and check for required variables
    required_vars = ['SECRET_KEY', 'POSTGRES_PASSWORD']
    placeholder_values = [
        'your-secret-key-here-generate-with-script',
        'your-secure-database-password-here',
        'CHANGE_THIS_SECURE_PASSWORD',
        'GENERATE_A_SECURE_KEY_HERE',
    ]

    with open(env_file, 'r') as f:
        content = f.read()

    issues = []
    for var in required_vars:
        if var not in content:
            issues.append(f"{var} not found in .env")
        else:
            # Extract value
            for line in content.split('\n'):
                if line.startswith(f"{var}="):
                    value = line.split('=', 1)[1].strip()
                    if value in placeholder_values or not value:
                        issues.append(f"{var} appears to be a placeholder value")
                    break

    if issues:
        for issue in issues:
            print_warning(issue)
        print("\n  Generate SECRET_KEY with: python scripts/generate_secret_key.py")
        return False
    else:
        print_success("Required environment variables are set")
        return True


def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")

    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_migrate',
        'flask_login',
        'flask_wtf',
        'bcrypt',
        'flask_limiter',
        'psycopg2',
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package} is installed")
        except ImportError:
            missing.append(package)
            print_error(f"{package} is NOT installed")

    if missing:
        print("\n  Install with: pip install -r website/requirements.txt")
        return False

    return True


def check_configuration():
    """Check if configuration can be loaded"""
    print_header("Checking Configuration")

    # Temporarily set environment variables if not set
    env_vars_to_set = {}
    if not os.environ.get('SECRET_KEY'):
        env_vars_to_set['SECRET_KEY'] = 'test-key-for-verification'
    if not os.environ.get('POSTGRES_PASSWORD'):
        env_vars_to_set['POSTGRES_PASSWORD'] = 'test-password'

    # Set temporary variables
    for key, value in env_vars_to_set.items():
        os.environ[key] = value

    try:
        from website.config import get_config, config

        # Test loading each config
        for config_name in ['development', 'production', 'testing']:
            try:
                cfg = get_config(config_name)
                print_success(f"{config_name.capitalize()}Config loaded successfully")
            except Exception as e:
                print_error(f"{config_name.capitalize()}Config failed: {e}")
                return False

        # Verify config dictionary
        if len(config) == 4:  # development, production, testing, default
            print_success("All configuration classes available")
        else:
            print_warning(f"Expected 4 configs, found {len(config)}")

        return True

    except Exception as e:
        print_error(f"Configuration import failed: {e}")
        return False
    finally:
        # Clean up temporary variables
        for key in env_vars_to_set:
            del os.environ[key]


def check_app_factory():
    """Check if application factory works"""
    print_header("Checking Application Factory")

    # Set required environment variables for testing
    os.environ['SECRET_KEY'] = 'test-secret-key-for-verification'
    os.environ['POSTGRES_PASSWORD'] = 'test-password-for-verification'

    try:
        from website import create_app

        # Try creating app with testing config (doesn't need real database)
        app = create_app('testing')
        print_success("Application factory works")
        print_success(f"App created: {app.name}")
        print_success(f"Testing mode: {app.testing}")

        # Check extensions
        from website import db, login_manager, csrf, limiter, cache

        print_success("Database extension initialized")
        print_success("Login manager initialized")
        print_success("CSRF protection initialized")
        print_success("Rate limiter initialized")
        print_success("Cache initialized")

        return True

    except Exception as e:
        print_error(f"Application factory failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        del os.environ['SECRET_KEY']
        del os.environ['POSTGRES_PASSWORD']


def check_directories():
    """Check if necessary directories exist"""
    print_header("Checking Directories")

    website_dir = PROJECT_ROOT / 'website'
    directories = [
        website_dir / 'logs',
        website_dir / 'instance',
        website_dir / 'instance' / 'uploads',
        website_dir / 'templates',
        website_dir / 'static',
        website_dir / 'routes',
        website_dir / 'utils',
    ]

    all_exist = True
    for directory in directories:
        if directory.exists():
            print_success(f"{directory.name}/ exists")
        else:
            print_error(f"{directory.name}/ NOT found")
            all_exist = False

    if not all_exist:
        print("\n  Run: python scripts/setup_environment.py")

    return all_exist


def check_scripts():
    """Check if utility scripts exist"""
    print_header("Checking Utility Scripts")

    scripts = [
        SCRIPT_DIR / 'generate_secret_key.py',
        SCRIPT_DIR / 'setup_environment.py',
    ]

    all_exist = True
    for script in scripts:
        if script.exists():
            print_success(f"{script.name} exists")
        else:
            print_error(f"{script.name} NOT found")
            all_exist = False

    return all_exist


def print_summary(checks):
    """Print summary of all checks"""
    print_header("Verification Summary")

    passed = sum(checks.values())
    total = len(checks)

    for check_name, result in checks.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")

    print()
    print(f"Results: {passed}/{total} checks passed")

    if passed == total:
        print("\n✓ All verification checks passed!")
        print("  You're ready to proceed with development.")
        return 0
    else:
        print("\n⚠ Some checks failed. Please address the issues above.")
        return 1


def main():
    """Main verification function"""
    print("\n" + "=" * 80)
    print("  CONFIGURATION VERIFICATION")
    print("=" * 80)

    # Run all checks
    checks = {
        "Environment File": check_env_file(),
        "Dependencies": check_dependencies(),
        "Configuration": check_configuration(),
        "Application Factory": check_app_factory(),
        "Directories": check_directories(),
        "Utility Scripts": check_scripts(),
    }

    # Print summary
    return print_summary(checks)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
