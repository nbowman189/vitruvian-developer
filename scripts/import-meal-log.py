#!/usr/bin/env python3
"""
Import meal data from meal-log.md to database.
Aggregates individual meals into daily totals.
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from website import create_app, db
from website.models.nutrition import MealLog
from website.models.user import User


def parse_meal_log(file_path):
    """Parse meal-log.md and aggregate by date."""

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return []

    print(f"📖 Reading file: {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')

    # Dictionary to aggregate meals by date: {date: {'calories': total, 'meals': [meal_details]}}
    daily_data = defaultdict(lambda: {'calories': 0, 'meals': []})

    in_table = False

    for line in lines:
        line = line.strip()

        # Check if we're in the table
        if line.startswith('| Date'):
            in_table = True
            continue

        # Skip separator
        if line.startswith('| :---'):
            continue

        # Parse data rows
        if in_table and line.startswith('|'):
            parts = [p.strip() for p in line.split('|')]

            # parts[0] is empty, parts[1] is date, parts[2] is meal, parts[3] is food, parts[4] is calories, parts[5] is notes
            if len(parts) >= 5:
                try:
                    date_str = parts[1]
                    meal_type = parts[2]
                    food = parts[3]
                    calories_str = parts[4]
                    notes = parts[5] if len(parts) > 5 else ""

                    # Skip bold date rows (daily totals)
                    if '**' in date_str:
                        continue

                    # Parse date
                    try:
                        meal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        continue

                    # Parse calories (remove ~ and other characters)
                    calories = 0
                    if calories_str:
                        calories_clean = re.sub(r'[^0-9]', '', calories_str)
                        if calories_clean:
                            calories = int(calories_clean)

                    # Aggregate to daily total
                    daily_data[meal_date]['calories'] += calories
                    daily_data[meal_date]['meals'].append({
                        'meal_type': meal_type,
                        'food': food,
                        'calories': calories,
                        'notes': notes
                    })

                except (ValueError, IndexError) as e:
                    continue

        # Stop if we're out of the table
        if in_table and not line.startswith('|') and line:
            in_table = False

    # Convert to list of daily entries
    meal_entries = []
    for meal_date, data in sorted(daily_data.items()):
        # Build summary notes
        meal_summary = "\n".join([
            f"{m['meal_type']}: {m['food'][:50]}..." if len(m['food']) > 50 else f"{m['meal_type']}: {m['food']}"
            for m in data['meals'] if m['meal_type']
        ])

        meal_entries.append({
            'meal_date': meal_date,
            'calories': data['calories'],
            'notes': meal_summary[:500]  # Limit notes length
        })

    return meal_entries


def import_to_database(meal_entries, skip_duplicates=True):
    """Import meal log entries to database."""

    print(f"\n📊 Found {len(meal_entries)} daily meal entries to import")

    app = create_app()

    with app.app_context():
        # Get admin user
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User.query.first()

        if not user:
            print("❌ No users found in database!")
            return False

        print(f"📌 Associating all meal logs with user: {user.username} (ID: {user.id})")

        imported = 0
        skipped = 0
        errors = 0

        for entry in meal_entries:
            try:
                # Check if entry exists
                existing = MealLog.query.filter_by(
                    user_id=user.id,
                    meal_date=entry['meal_date']
                ).first()

                if existing:
                    if skip_duplicates:
                        print(f"⏭️  Skipping {entry['meal_date']} (already exists)")
                        skipped += 1
                        continue
                    else:
                        existing.calories = entry['calories']
                        existing.notes = entry['notes']
                        print(f"🔄 Updated {entry['meal_date']}")
                else:
                    meal_log = MealLog(
                        user_id=user.id,
                        meal_date=entry['meal_date'],
                        meal_type='Daily Total',  # Aggregated from all meals
                        calories=entry['calories'],
                        notes=entry['notes']
                    )
                    db.session.add(meal_log)
                    print(f"✅ Imported {entry['meal_date']} - {entry['calories']} calories")

                imported += 1

            except Exception as e:
                print(f"❌ Error importing {entry.get('meal_date', 'unknown')}: {e}")
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
        print(f"   Total: {len(meal_entries)}")

        return True


def main():
    """Main function."""

    print("====================================")
    print("Meal Log Import Tool")
    print("====================================")
    print()

    # Default path
    default_path = Path(__file__).parent.parent / "Health_and_Fitness" / "data" / "meal-log.md"

    # Allow custom path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = str(default_path)

    print(f"📂 Looking for: {file_path}")

    # Parse the file
    meal_entries = parse_meal_log(file_path)

    if not meal_entries:
        print("❌ No meal entries found in file")
        return 1

    # Ask for confirmation
    print(f"\n⚠️  About to import {len(meal_entries)} daily meal logs to the database")
    print("   Daily totals will be calculated from individual meals.")
    print("   Duplicates will be skipped.")
    response = input("\n   Continue? (y/n): ")

    if response.lower() != 'y':
        print("❌ Import cancelled")
        return 0

    # Import to database
    success = import_to_database(meal_entries)

    if success:
        print("\n✅ Import complete!")
        return 0
    else:
        print("\n❌ Import failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
