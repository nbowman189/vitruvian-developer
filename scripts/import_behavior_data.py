#!/usr/bin/env python3
"""
Behavior Tracker Data Import Script
====================================

Parses behavior-tracker.md and imports behavior definitions and historical logs
into the PostgreSQL database.

Usage:
    python import_behavior_data.py /path/to/behavior-tracker.md
"""

import sys
import re
from datetime import datetime
from pathlib import Path

# Add the website directory to the path
sys.path.insert(0, '/app')

from website import create_app, db
from website.models.behavior import BehaviorDefinition, BehaviorLog, BehaviorCategory
from website.models.user import User


# Mapping of behavior names to categories and icons
BEHAVIOR_MAPPING = {
    'Weigh-In': {
        'category': BehaviorCategory.HEALTH,
        'icon': 'bi-heart-pulse',
        'color': '#E27D60',
        'target_frequency': 7
    },
    'Breakfast Logged': {
        'category': BehaviorCategory.NUTRITION,
        'icon': 'bi-egg-fried',
        'color': '#E8A87C',
        'target_frequency': 7
    },
    'Lunch Logged': {
        'category': BehaviorCategory.NUTRITION,
        'icon': 'bi-bowl-hot-fill',
        'color': '#E8A87C',
        'target_frequency': 7
    },
    'Dinner Logged': {
        'category': BehaviorCategory.NUTRITION,
        'icon': 'bi-cup-hot-fill',
        'color': '#E8A87C',
        'target_frequency': 7
    },
    'Morning Snack': {
        'category': BehaviorCategory.NUTRITION,
        'icon': 'bi-apple',
        'color': '#E8A87C',
        'target_frequency': 5
    },
    'Afternoon Snack': {
        'category': BehaviorCategory.NUTRITION,
        'icon': 'bi-cookie',
        'color': '#E8A87C',
        'target_frequency': 5
    },
    'Evening Snack': {
        'category': BehaviorCategory.NUTRITION,
        'icon': 'bi-moon-stars',
        'color': '#E8A87C',
        'target_frequency': 3
    },
    'Resistance Workout': {
        'category': BehaviorCategory.FITNESS,
        'icon': 'bi-fire',
        'color': '#C38D9E',
        'target_frequency': 4
    },
    'Cardio / Walk': {
        'category': BehaviorCategory.FITNESS,
        'icon': 'bi-heart',
        'color': '#C38D9E',
        'target_frequency': 5
    },
    'Tai Chi': {
        'category': BehaviorCategory.WELLNESS,
        'icon': 'bi-yin-yang',
        'color': '#41B3A3',
        'target_frequency': 7
    },
    'AI Curriculum': {
        'category': BehaviorCategory.LEARNING,
        'icon': 'bi-brain',
        'color': '#4A90E2',
        'target_frequency': 7
    },
    'Due Lingo Practice': {
        'category': BehaviorCategory.LEARNING,
        'icon': 'bi-translate',
        'color': '#4A90E2',
        'target_frequency': 7
    }
}


def parse_markdown_table(file_path):
    """Parse the behavior tracker markdown table."""
    print(f"Reading file: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into lines
    lines = content.strip().split('\n')

    # Find the table header (starts with |)
    table_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('| Date |'):
            table_start = i
            break

    if table_start is None:
        raise ValueError("Could not find table header in markdown file")

    # Parse header row
    header_line = lines[table_start]
    headers = [h.strip() for h in header_line.split('|')[1:-1]]  # Skip first and last empty

    print(f"Found {len(headers)} columns: {headers}")

    # Skip separator line (dashes)
    data_start = table_start + 2

    # Parse data rows
    data_rows = []
    for line in lines[data_start:]:
        line = line.strip()
        if not line or not line.startswith('|'):
            continue

        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) != len(headers):
            print(f"Warning: Row has {len(cells)} cells, expected {len(headers)}: {line}")
            continue

        data_rows.append(cells)

    print(f"Found {len(data_rows)} data rows")

    return headers, data_rows


def import_behaviors(user_id, headers, data_rows):
    """Import behavior definitions and logs into database."""

    # Skip the 'Date' column
    behavior_names = headers[1:]

    print(f"\nImporting {len(behavior_names)} behavior definitions...")

    # Create behavior definitions
    behavior_map = {}  # Maps behavior name to BehaviorDefinition object

    for idx, name in enumerate(behavior_names):
        # Check if behavior already exists
        existing = BehaviorDefinition.query.filter_by(
            user_id=user_id,
            name=name,
            is_active=True
        ).first()

        if existing:
            print(f"  - '{name}' already exists (ID: {existing.id})")
            behavior_map[name] = existing
            continue

        # Get mapping or use defaults
        mapping = BEHAVIOR_MAPPING.get(name, {
            'category': BehaviorCategory.CUSTOM,
            'icon': 'bi-check-circle',
            'color': '#4A90E2',
            'target_frequency': 7
        })

        # Create new behavior definition
        behavior = BehaviorDefinition(
            user_id=user_id,
            name=name,
            description=f"Imported from behavior-tracker.md",
            category=mapping['category'],
            icon=mapping['icon'],
            color=mapping['color'],
            display_order=idx,
            target_frequency=mapping['target_frequency'],
            is_active=True
        )

        db.session.add(behavior)
        db.session.flush()  # Get the ID

        behavior_map[name] = behavior
        print(f"  ✓ Created '{name}' (Category: {mapping['category'].value}, ID: {behavior.id})")

    db.session.commit()
    print(f"\n✓ Behavior definitions created/verified")

    # Import historical logs
    print(f"\nImporting historical behavior logs...")

    logs_created = 0
    logs_skipped = 0

    for row in data_rows:
        date_str = row[0]

        # Parse date (format: YYYY-MM-DD)
        try:
            tracked_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"  Warning: Invalid date format: {date_str}")
            continue

        # Process each behavior column
        for i, behavior_name in enumerate(behavior_names):
            status = row[i + 1]  # +1 because first column is date

            # Only import completed behaviors (✅)
            # Skip N/A (-) and empty cells
            if status != '✅':
                continue

            behavior_def = behavior_map[behavior_name]

            # Check if log already exists
            existing_log = BehaviorLog.query.filter_by(
                user_id=user_id,
                behavior_definition_id=behavior_def.id,
                tracked_date=tracked_date
            ).first()

            if existing_log:
                logs_skipped += 1
                continue

            # Create behavior log
            log = BehaviorLog(
                user_id=user_id,
                behavior_definition_id=behavior_def.id,
                tracked_date=tracked_date,
                completed=True,
                notes="Imported from behavior-tracker.md"
            )

            db.session.add(log)
            logs_created += 1

    db.session.commit()
    print(f"\n✓ Imported {logs_created} behavior logs ({logs_skipped} skipped as duplicates)")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python import_behavior_data.py /path/to/behavior-tracker.md")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print("=" * 60)
    print("Behavior Tracker Data Import")
    print("=" * 60)
    print()

    # Create Flask app context
    app = create_app()

    with app.app_context():
        # Get the admin user (assuming user_id=1)
        user = User.query.filter_by(username='admin').first()

        if not user:
            print("Error: Admin user not found. Please create an admin user first.")
            sys.exit(1)

        print(f"Importing data for user: {user.username} (ID: {user.id})")
        print()

        try:
            # Parse the markdown file
            headers, data_rows = parse_markdown_table(file_path)

            # Import behaviors and logs
            import_behaviors(user.id, headers, data_rows)

            print()
            print("=" * 60)
            print("Import Complete!")
            print("=" * 60)
            print()
            print("Summary:")
            print(f"  - Behavior Definitions: {len(headers) - 1}")
            print(f"  - Historical Records: {len(data_rows)} days")
            print()
            print("Next steps:")
            print("  1. Visit the dashboard to view imported behaviors")
            print("  2. Check the behavior completion trends")
            print("  3. Verify historical data accuracy")

        except Exception as e:
            print(f"\nError during import: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()
