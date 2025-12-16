#!/usr/bin/env python3
"""
Import health data from local check-in-log.md to remote database.
Run this script after connecting to your remote server or via SSH tunnel.
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import from website
sys.path.insert(0, str(Path(__file__).parent.parent))

from website import create_app, db
from website.models.health import HealthMetric


def parse_check_in_log(file_path):
    """Parse the check-in-log.md file and extract health metrics."""

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return []

    print(f"📖 Reading file: {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    # Find the table in the markdown
    # Format: | Date | Weight (lbs) | Body Fat % | Notes |
    lines = content.split('\n')

    metrics = []
    in_table = False

    for line in lines:
        line = line.strip()

        # Check if we're entering a table
        if line.startswith('| Date'):
            in_table = True
            continue

        # Skip separator line
        if line.startswith('| :--'):
            continue

        # Parse data rows
        if in_table and line.startswith('|'):
            # Split by pipe and clean up
            parts = [p.strip() for p in line.split('|')]

            # parts[0] is empty, parts[1] is date, parts[2] is weight, parts[3] is bodyfat, parts[4] is notes
            if len(parts) >= 5:
                try:
                    date_str = parts[1]
                    weight_str = parts[2]
                    bodyfat_str = parts[3]
                    notes = parts[4] if len(parts) > 4 else ""

                    # Parse date
                    recorded_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    # Parse weight (handle empty or N/A)
                    weight = None
                    if weight_str and weight_str.lower() not in ['n/a', 'none', '-', '']:
                        weight = float(weight_str.replace('lbs', '').strip())

                    # Parse body fat (handle empty or N/A)
                    bodyfat = None
                    if bodyfat_str and bodyfat_str.lower() not in ['n/a', 'none', '-', '']:
                        bodyfat = float(bodyfat_str.replace('%', '').strip())

                    # Calculate BMI if we have weight (assuming average height of 5'10" = 70 inches)
                    # BMI = (weight in lbs / (height in inches)^2) * 703
                    # You can adjust height as needed
                    bmi = None
                    if weight:
                        HEIGHT_INCHES = 70  # Adjust this to your actual height
                        bmi = round((weight / (HEIGHT_INCHES ** 2)) * 703, 1)

                    metrics.append({
                        'recorded_date': recorded_date,
                        'weight_lbs': weight,
                        'body_fat_percentage': bodyfat,
                        'bmi': bmi,
                        'notes': notes if notes else None
                    })

                except (ValueError, IndexError) as e:
                    print(f"⚠️  Skipping malformed line: {line}")
                    print(f"   Error: {e}")
                    continue

        # Stop if we hit another section
        if in_table and not line.startswith('|') and line:
            break

    return metrics


def import_to_database(metrics, skip_duplicates=True):
    """Import health metrics to the database."""

    print(f"\n📊 Found {len(metrics)} health metrics to import")

    app = create_app()

    with app.app_context():
        # Get the admin user (or first user) to associate metrics with
        from website.models.user import User
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User.query.first()

        if not user:
            print("❌ No users found in database! Please create a user first.")
            return False

        print(f"📌 Associating all health metrics with user: {user.username} (ID: {user.id})")

        imported = 0
        skipped = 0
        errors = 0

        for metric_data in metrics:
            # Add user_id to metric data
            metric_data['user_id'] = user.id
            try:
                # Check if metric already exists for this date and user
                existing = HealthMetric.query.filter_by(
                    user_id=user.id,
                    recorded_date=metric_data['recorded_date']
                ).first()

                if existing:
                    if skip_duplicates:
                        print(f"⏭️  Skipping {metric_data['recorded_date']} (already exists)")
                        skipped += 1
                        continue
                    else:
                        # Update existing metric
                        existing.weight_lbs = metric_data['weight_lbs']
                        existing.body_fat_percentage = metric_data['body_fat_percentage']
                        existing.bmi = metric_data['bmi']
                        existing.notes = metric_data['notes']
                        print(f"🔄 Updated {metric_data['recorded_date']}")
                else:
                    # Create new metric
                    metric = HealthMetric(**metric_data)
                    db.session.add(metric)
                    print(f"✅ Imported {metric_data['recorded_date']} - Weight: {metric_data['weight_lbs']} lbs, Body Fat: {metric_data['body_fat_percentage']}%")

                imported += 1

            except Exception as e:
                print(f"❌ Error importing {metric_data.get('recorded_date', 'unknown')}: {e}")
                errors += 1

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Database commit successful!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Database commit failed: {e}")
            return False

        print(f"\n📈 Import Summary:")
        print(f"   Imported: {imported}")
        print(f"   Skipped: {skipped}")
        print(f"   Errors: {errors}")
        print(f"   Total: {len(metrics)}")

        return True


def main():
    """Main function."""

    print("====================================")
    print("Health Data Import Tool")
    print("====================================")
    print()

    # Default path - check if in Docker container (data at root) or local dev (relative path)
    docker_path = Path("/Health_and_Fitness/data/check-in-log.md")
    local_path = Path(__file__).parent.parent / "Health_and_Fitness" / "data" / "check-in-log.md"

    # Use Docker path if it exists, otherwise local path
    default_path = docker_path if docker_path.exists() else local_path

    # Allow custom path as command line argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = str(default_path)

    print(f"📂 Looking for: {file_path}")

    # Parse the file
    metrics = parse_check_in_log(file_path)

    if not metrics:
        print("❌ No health metrics found in file")
        return 1

    # Ask for confirmation
    print(f"\n⚠️  About to import {len(metrics)} health metrics to the database")
    print("   Duplicates will be skipped.")
    response = input("\n   Continue? (y/n): ")

    if response.lower() != 'y':
        print("❌ Import cancelled")
        return 0

    # Import to database
    success = import_to_database(metrics)

    if success:
        print("\n✅ Import complete!")
        return 0
    else:
        print("\n❌ Import failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
