#!/usr/bin/env python3
"""
Environment Setup Script

This script helps initialize the development environment by:
1. Checking for required dependencies
2. Creating .env file from template if it doesn't exist
3. Generating SECRET_KEY if needed
4. Verifying PostgreSQL installation
5. Creating necessary directories

Usage:
    python scripts/setup_environment.py
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path


# Project paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
WEBSITE_DIR = PROJECT_ROOT / 'website'
ENV_EXAMPLE = PROJECT_ROOT / '.env.example'
ENV_FILE = PROJECT_ROOT / '.env'


def print_header(message):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80 + "\n")


def print_success(message):
    """Print a success message"""
    print(f"✓ {message}")


def print_warning(message):
    """Print a warning message"""
    print(f"⚠ {message}")


def print_error(message):
    """Print an error message"""
    print(f"✗ {message}")


def check_python_version():
    """Check if Python version is 3.8+"""
    print_header("Checking Python Version")

    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
        return False


def check_postgresql():
    """Check if PostgreSQL is installed"""
    print_header("Checking PostgreSQL Installation")

    try:
        result = subprocess.run(
            ['psql', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success(f"PostgreSQL installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print_warning("PostgreSQL not found")
    print("  Install with: brew install postgresql")
    print("  Or use SQLite for development: Set USE_SQLITE_DEV=true in .env")
    return False


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    print_header("Setting Up Environment File")

    if ENV_FILE.exists():
        print_warning(f".env file already exists at {ENV_FILE}")
        print("  Skipping creation to avoid overwriting existing configuration")
        return True

    if not ENV_EXAMPLE.exists():
        print_error(f".env.example not found at {ENV_EXAMPLE}")
        return False

    # Copy template
    try:
        with open(ENV_EXAMPLE, 'r') as src:
            content = src.read()

        with open(ENV_FILE, 'w') as dst:
            dst.write(content)

        print_success(f"Created .env file at {ENV_FILE}")
        print("  IMPORTANT: Update the following values in .env:")
        print("    - SECRET_KEY (generate with next step)")
        print("    - POSTGRES_PASSWORD")
        return True

    except Exception as e:
        print_error(f"Failed to create .env file: {e}")
        return False


def generate_secret_key():
    """Generate a SECRET_KEY and offer to update .env"""
    print_header("Generating SECRET_KEY")

    secret_key = secrets.token_urlsafe(32)

    print("Generated SECRET_KEY:")
    print(f"\n  {secret_key}\n")

    if ENV_FILE.exists():
        response = input("Would you like to automatically update .env with this key? (y/n): ")

        if response.lower() in ['y', 'yes']:
            try:
                with open(ENV_FILE, 'r') as f:
                    content = f.read()

                # Replace placeholder SECRET_KEY
                content = content.replace(
                    'SECRET_KEY=your-secret-key-here-generate-with-script',
                    f'SECRET_KEY={secret_key}'
                )

                with open(ENV_FILE, 'w') as f:
                    f.write(content)

                print_success("Updated .env with generated SECRET_KEY")
                return True

            except Exception as e:
                print_error(f"Failed to update .env: {e}")
                print("  Please manually copy the key above to your .env file")
                return False
        else:
            print("  Please manually copy the key above to your .env file")
    else:
        print("  .env file not found. Copy this key to your .env file when created.")

    return True


def create_directories():
    """Create necessary directories"""
    print_header("Creating Necessary Directories")

    directories = [
        WEBSITE_DIR / 'logs',
        WEBSITE_DIR / 'instance',
        WEBSITE_DIR / 'instance' / 'uploads',
    ]

    for directory in directories:
        if directory.exists():
            print_success(f"Directory exists: {directory}")
        else:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print_success(f"Created directory: {directory}")
            except Exception as e:
                print_error(f"Failed to create {directory}: {e}")
                return False

    return True


def check_requirements():
    """Check if requirements.txt exists"""
    print_header("Checking Requirements")

    requirements_file = WEBSITE_DIR / 'requirements.txt'

    if requirements_file.exists():
        print_success(f"requirements.txt found at {requirements_file}")
        print("\n  To install dependencies, run:")
        print(f"    cd {WEBSITE_DIR}")
        print("    pip install -r requirements.txt")
        return True
    else:
        print_error(f"requirements.txt not found at {requirements_file}")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print_header("Next Steps")

    print("1. Review and update .env file:")
    print(f"     nano {ENV_FILE}")
    print()
    print("2. Install Python dependencies:")
    print(f"     cd {WEBSITE_DIR}")
    print("     pip install -r requirements.txt")
    print()
    print("3. Set up PostgreSQL database (if using PostgreSQL):")
    print("     psql postgres")
    print("     CREATE DATABASE portfolio_db;")
    print("     CREATE USER portfolio_user WITH PASSWORD 'your-password';")
    print("     GRANT ALL PRIVILEGES ON DATABASE portfolio_db TO portfolio_user;")
    print()
    print("4. Initialize database migrations:")
    print(f"     cd {WEBSITE_DIR}")
    print("     flask db init")
    print("     flask db migrate -m 'Initial schema'")
    print("     flask db upgrade")
    print()
    print("5. Run the application:")
    print(f"     cd {WEBSITE_DIR}")
    print("     python app.py")
    print()
    print("For detailed instructions, see:")
    print(f"     {WEBSITE_DIR / 'CONFIGURATION_GUIDE.md'}")
    print()


def main():
    """Main setup function"""
    print("\n" + "=" * 80)
    print("  PRIMARY ASSISTANT - ENVIRONMENT SETUP")
    print("=" * 80)

    checks_passed = True

    # Run all checks
    checks_passed &= check_python_version()
    check_postgresql()  # Warning only, not required
    checks_passed &= create_env_file()
    checks_passed &= generate_secret_key()
    checks_passed &= create_directories()
    checks_passed &= check_requirements()

    # Print summary
    print_header("Setup Summary")

    if checks_passed:
        print_success("Environment setup completed successfully!")
        print_next_steps()
        return 0
    else:
        print_error("Some setup steps failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
