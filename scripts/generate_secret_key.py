#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for Flask application

This script generates a cryptographically secure random key suitable for use
as Flask's SECRET_KEY configuration value.

Usage:
    python scripts/generate_secret_key.py

The generated key should be added to your .env file:
    SECRET_KEY=<generated_key>
"""

import secrets
import sys


def generate_secret_key(length=32):
    """
    Generate a cryptographically secure random key.

    Args:
        length: Number of random bytes (default: 32)
                The resulting base64 string will be longer

    Returns:
        A URL-safe base64-encoded string
    """
    return secrets.token_urlsafe(length)


def main():
    """Generate and display a secure SECRET_KEY"""

    print("=" * 80)
    print("Flask SECRET_KEY Generator")
    print("=" * 80)
    print()

    # Generate the key
    secret_key = generate_secret_key(32)

    # Display the key
    print("Your new SECRET_KEY:")
    print()
    print(f"  {secret_key}")
    print()
    print("=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print()
    print("1. Copy the key above")
    print("2. Open your .env file (or create it from .env.example)")
    print("3. Add or update the SECRET_KEY line:")
    print(f"   SECRET_KEY={secret_key}")
    print()
    print("4. IMPORTANT: Never commit .env to version control!")
    print("   Make sure .env is in your .gitignore file")
    print()
    print("5. For production, generate a different key with this script")
    print("   and keep it secure!")
    print()
    print("=" * 80)

    # Also generate a few alternatives
    print()
    print("Additional keys (in case you need multiple):")
    print()
    for i in range(3):
        print(f"  {generate_secret_key(32)}")
    print()
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
