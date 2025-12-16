#!/usr/bin/env python3
"""
Master import script to import all health data from markdown files to database.
Runs all individual import scripts in sequence with error handling.
"""

import sys
import subprocess
from pathlib import Path


def run_import_script(script_name, description):
    """Run an import script and return success status."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}\n")

    script_path = Path(__file__).parent / script_name

    try:
        # Run the import script with 'y' as input to auto-confirm
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input='y\n',
            text=True,
            capture_output=False,  # Let output show in real-time
            timeout=120  # 2 minute timeout per script
        )

        if result.returncode == 0:
            print(f"\n✅ {description} completed successfully!")
            return True
        else:
            print(f"\n❌ {description} failed with exit code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print(f"\n⏱️  {description} timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"\n❌ Error running {description}: {e}")
        return False


def main():
    """Main function to run all import scripts."""

    print("="*70)
    print("MASTER HEALTH DATA IMPORT TOOL")
    print("="*70)
    print()
    print("This script will import all health data from markdown files:")
    print("  1. Health Metrics (check-in-log.md)")
    print("  2. Meal Log (meal-log.md)")
    print("  3. Exercise Log (exercise-log.md)")
    print("  4. Coaching Sessions (Coaching_sessions.md)")
    print()
    print("⚠️  Existing data will not be duplicated (duplicates are skipped)")
    print()

    response = input("Continue with all imports? (y/n): ")
    if response.lower() != 'y':
        print("\n❌ Import cancelled by user")
        return 1

    # Track results
    results = {}

    # Run each import script in sequence
    imports = [
        ('import-health-data.py', 'Health Metrics Import'),
        ('import-meal-log.py', 'Meal Log Import'),
        ('import-exercise-log.py', 'Exercise Log Import'),
        ('import-coaching-sessions.py', 'Coaching Sessions Import'),
    ]

    for script_name, description in imports:
        success = run_import_script(script_name, description)
        results[description] = success

    # Print summary
    print(f"\n\n{'='*70}")
    print("IMPORT SUMMARY")
    print(f"{'='*70}\n")

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for description, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"  {status} - {description}")

    print(f"\n📊 Overall: {success_count}/{total_count} imports successful")

    if success_count == total_count:
        print("\n🎉 All health data imported successfully!")
        return 0
    elif success_count > 0:
        print("\n⚠️  Some imports failed - check logs above for details")
        return 1
    else:
        print("\n❌ All imports failed - check logs above for details")
        return 2


if __name__ == '__main__':
    sys.exit(main())
