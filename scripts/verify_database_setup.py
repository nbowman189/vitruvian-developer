#!/usr/bin/env python3
"""
Database Setup Verification Script
===================================

Verifies that all database models, migrations, and configuration files
are properly created and can be imported successfully.

Usage:
    python scripts/verify_database_setup.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"❌ {text}")

def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")

def verify_file_exists(filepath, description):
    """Verify a file exists."""
    if filepath.exists():
        print_success(f"{description}: {filepath.name}")
        return True
    else:
        print_error(f"{description} NOT FOUND: {filepath}")
        return False

def verify_directory_structure():
    """Verify all required directories exist."""
    print_header("Verifying Directory Structure")

    directories = [
        (project_root / "website" / "models", "Models directory"),
        (project_root / "migrations", "Migrations directory"),
        (project_root / "migrations" / "versions", "Migration versions directory"),
    ]

    all_exist = True
    for directory, description in directories:
        if directory.exists() and directory.is_dir():
            print_success(f"{description}: {directory.relative_to(project_root)}")
        else:
            print_error(f"{description} NOT FOUND: {directory.relative_to(project_root)}")
            all_exist = False

    return all_exist

def verify_model_files():
    """Verify all model files exist."""
    print_header("Verifying Model Files")

    models_dir = project_root / "website" / "models"
    model_files = [
        ("__init__.py", "Models package init"),
        ("user.py", "User model"),
        ("health.py", "Health model"),
        ("workout.py", "Workout models"),
        ("coaching.py", "Coaching models"),
        ("nutrition.py", "Nutrition model"),
        ("session.py", "Session model"),
    ]

    all_exist = True
    for filename, description in model_files:
        filepath = models_dir / filename
        if not verify_file_exists(filepath, description):
            all_exist = False

    return all_exist

def verify_migration_files():
    """Verify migration files exist."""
    print_header("Verifying Migration Files")

    migration_files = [
        (project_root / "migrations" / "env.py", "Alembic environment"),
        (project_root / "migrations" / "script.py.mako", "Migration template"),
        (project_root / "migrations" / "versions" / "001_initial_schema.py", "Initial migration"),
        (project_root / "alembic.ini", "Alembic configuration"),
    ]

    all_exist = True
    for filepath, description in migration_files:
        if not verify_file_exists(filepath, description):
            all_exist = False

    return all_exist

def verify_initialization_files():
    """Verify database initialization files exist."""
    print_header("Verifying Database Initialization Files")

    files = [
        (project_root / "scripts" / "init_db.sql", "PostgreSQL init script"),
    ]

    all_exist = True
    for filepath, description in files:
        if not verify_file_exists(filepath, description):
            all_exist = False

    return all_exist

def verify_documentation():
    """Verify documentation files exist."""
    print_header("Verifying Documentation")

    doc_files = [
        (project_root / "DATABASE_README.md", "Database README"),
        (project_root / "DATABASE_SCHEMA.md", "Schema diagram"),
        (project_root / "DATABASE_IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
    ]

    all_exist = True
    for filepath, description in doc_files:
        if not verify_file_exists(filepath, description):
            all_exist = False

    return all_exist

def verify_model_imports():
    """Verify all models can be imported."""
    print_header("Verifying Model Imports")

    try:
        from website.models import (
            db, User, HealthMetric, WorkoutSession, ExerciseLog,
            ExerciseDefinition, CoachingSession, UserGoal,
            ProgressPhoto, MealLog, UserSession
        )
        print_success("All models imported successfully")

        # Verify model attributes
        models_info = [
            (User, "User", ["username", "email", "password_hash"]),
            (HealthMetric, "HealthMetric", ["user_id", "recorded_date", "weight_lbs"]),
            (WorkoutSession, "WorkoutSession", ["user_id", "session_date", "session_type"]),
            (ExerciseLog, "ExerciseLog", ["workout_session_id", "exercise_name", "sets"]),
            (ExerciseDefinition, "ExerciseDefinition", ["name", "category", "muscle_groups"]),
            (CoachingSession, "CoachingSession", ["user_id", "coach_id", "session_date"]),
            (UserGoal, "UserGoal", ["user_id", "goal_type", "title"]),
            (ProgressPhoto, "ProgressPhoto", ["user_id", "photo_date", "photo_url"]),
            (MealLog, "MealLog", ["user_id", "meal_date", "meal_type"]),
            (UserSession, "UserSession", ["session_id", "user_id", "expires_at"]),
        ]

        for model_class, model_name, required_attrs in models_info:
            missing_attrs = [attr for attr in required_attrs if not hasattr(model_class, attr)]
            if missing_attrs:
                print_error(f"{model_name} missing attributes: {', '.join(missing_attrs)}")
                return False
            else:
                print_success(f"{model_name} has all required attributes")

        return True

    except ImportError as e:
        print_error(f"Failed to import models: {e}")
        return False
    except Exception as e:
        print_error(f"Error verifying models: {e}")
        return False

def print_statistics():
    """Print file statistics."""
    print_header("File Statistics")

    models_dir = project_root / "website" / "models"
    migration_dir = project_root / "migrations"

    # Count model files
    model_files = list(models_dir.glob("*.py"))
    total_model_lines = 0
    for model_file in model_files:
        with open(model_file, 'r') as f:
            total_model_lines += len(f.readlines())

    print_info(f"Model files: {len(model_files)}")
    print_info(f"Total model lines: {total_model_lines:,}")

    # Count migration files
    migration_files = list(migration_dir.glob("**/*.py"))
    total_migration_lines = 0
    for migration_file in migration_files:
        with open(migration_file, 'r') as f:
            total_migration_lines += len(f.readlines())

    print_info(f"Migration files: {len(migration_files)}")
    print_info(f"Total migration lines: {total_migration_lines:,}")

    # Documentation
    doc_files = list(project_root.glob("DATABASE_*.md"))
    total_doc_lines = 0
    for doc_file in doc_files:
        with open(doc_file, 'r') as f:
            total_doc_lines += len(f.readlines())

    print_info(f"Documentation files: {len(doc_files)}")
    print_info(f"Total documentation lines: {total_doc_lines:,}")

    print_info(f"Total implementation lines: {total_model_lines + total_migration_lines + total_doc_lines:,}")

def print_next_steps():
    """Print next steps."""
    print_header("Next Steps")

    print("""
1. Start PostgreSQL Database:
   docker run --name fitness-postgres \\
     -e POSTGRES_USER=fitness_user \\
     -e POSTGRES_PASSWORD=fitness_password \\
     -e POSTGRES_DB=fitness_db \\
     -p 5432:5432 \\
     -d postgres:15

2. Initialize Database:
   docker exec -i fitness-postgres psql -U fitness_user -d fitness_db < scripts/init_db.sql

3. Configure Environment:
   export DATABASE_URL="postgresql://fitness_user:fitness_password@localhost:5432/fitness_db"

4. Run Migrations:
   alembic upgrade head

5. Verify Tables Created:
   docker exec -it fitness-postgres psql -U fitness_user -d fitness_db -c "\\dt"

6. Create First User (via Flask shell):
   flask shell
   >>> from website.models import db, User
   >>> user = User(username='admin', email='admin@example.com')
   >>> user.set_password('secure_password')
   >>> user.role = 'admin'
   >>> db.session.add(user)
   >>> db.session.commit()
""")

def main():
    """Main verification function."""
    print_header("Database Architecture Verification")
    print_info(f"Project root: {project_root}")

    results = []

    # Run all verifications
    results.append(("Directory Structure", verify_directory_structure()))
    results.append(("Model Files", verify_model_files()))
    results.append(("Migration Files", verify_migration_files()))
    results.append(("Initialization Files", verify_initialization_files()))
    results.append(("Documentation", verify_documentation()))
    results.append(("Model Imports", verify_model_imports()))

    # Print statistics
    print_statistics()

    # Summary
    print_header("Verification Summary")

    all_passed = all(result for _, result in results)

    for name, passed in results:
        if passed:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")

    print("\n" + "=" * 80)
    if all_passed:
        print_success("ALL VERIFICATIONS PASSED!")
        print_success("Database architecture implementation is complete and ready to use.")
        print_next_steps()
        return 0
    else:
        print_error("SOME VERIFICATIONS FAILED")
        print_error("Please review the errors above and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
