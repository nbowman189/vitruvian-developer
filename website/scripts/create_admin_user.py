#!/usr/bin/env python3
"""
Create Admin User Script
=========================

Creates an initial admin user for the application.
Can be run locally or in Docker container.

Usage:
    python scripts/create_admin_user.py
    # or with custom values:
    python scripts/create_admin_user.py --username admin --email admin@example.com
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import website module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from website import create_app, db
from website.models.user import User, UserRole
from werkzeug.security import generate_password_hash


def create_admin_user(username='admin', email='admin@example.com', password=None):
    """
    Create an admin user in the database.

    Args:
        username: Admin username (default: 'admin')
        email: Admin email (default: 'admin@example.com')
        password: Admin password (default: prompts for input)

    Returns:
        User object if successful, None if user already exists
    """
    app = create_app()

    with app.app_context():
        # Check if admin user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            print(f"❌ User already exists:")
            print(f"   Username: {existing_user.username}")
            print(f"   Email: {existing_user.email}")
            print(f"   Role: {existing_user.role.value}")
            return None

        # Get password from environment variable or prompt
        if password is None:
            password = os.environ.get('ADMIN_PASSWORD')

        if password is None:
            import getpass
            password = getpass.getpass('Enter admin password: ')
            password_confirm = getpass.getpass('Confirm admin password: ')

            if password != password_confirm:
                print("❌ Passwords do not match!")
                return None

        if len(password) < 8:
            print("❌ Password must be at least 8 characters long!")
            return None

        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            role=UserRole.ADMIN,
            is_active=True
        )
        admin_user.set_password(password)

        try:
            db.session.add(admin_user)
            db.session.commit()

            print("✅ Admin user created successfully!")
            print(f"   Username: {admin_user.username}")
            print(f"   Email: {admin_user.email}")
            print(f"   Role: {admin_user.role.value}")
            print(f"   ID: {admin_user.id}")

            return admin_user

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {str(e)}")
            return None


def main():
    """Main entry point for script"""
    import argparse

    parser = argparse.ArgumentParser(description='Create admin user for Primary Assistant')
    parser.add_argument('--username', default='admin', help='Admin username (default: admin)')
    parser.add_argument('--email', default='admin@example.com', help='Admin email (default: admin@example.com)')
    parser.add_argument('--password', help='Admin password (if not provided, will prompt)')

    args = parser.parse_args()

    create_admin_user(
        username=args.username,
        email=args.email,
        password=args.password
    )


if __name__ == '__main__':
    main()
