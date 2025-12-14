"""
Meal Log Migration
===================

Migrates meal data from meal-log.md to MealLog table.
Parses markdown table format and extracts nutritional information.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict
import logging
import re

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migrations.validators import (
    validate_date, validate_calories, validate_text, sanitize_notes
)

logger = logging.getLogger(__name__)


class MealMigrator:
    """Migrates meal logs from markdown to database"""

    def __init__(self, db_session, user_id: int):
        self.session = db_session
        self.user_id = user_id
        self.source_file = PROJECT_ROOT / 'Health_and_Fitness' / 'data' / 'meal-log.md'

    def parse_markdown_table(self) -> List[Dict]:
        """
        Parse meal logs from meal-log.md table format.

        Expected format:
        | Date | Meal | Food/Drink | Calories (est.) | Notes |

        Returns:
            List of parsed meal dictionaries
        """
        if not self.source_file.exists():
            logger.error(f"Source file not found: {self.source_file}")
            return []

        meals = []
        with open(self.source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line.startswith('|'):
                continue
            if '| :' in line or 'Date' in line:  # Skip header
                continue
            if 'DAILY TOTAL' in line:  # Skip summary rows
                continue

            try:
                parts = [p.strip() for p in line.split('|')]
                parts = [p for p in parts if p]

                if len(parts) < 4:
                    continue

                date_str = parts[0]
                meal_type = parts[1]
                description = parts[2]
                calories_str = parts[3]
                notes = parts[4] if len(parts) > 4 else ''

                # Extract calorie number from string like "~800" or "800"
                cal_match = re.search(r'~?(\d+)', calories_str)
                calories = int(cal_match.group(1)) if cal_match else None

                meal = {
                    'date': date_str,
                    'meal_type': meal_type,
                    'description': description,
                    'calories': calories,
                    'notes': notes,
                    'line_number': line_num
                }

                meals.append(meal)

            except Exception as e:
                logger.error(f"Line {line_num}: Parse error: {e}")
                continue

        logger.info(f"Parsed {len(meals)} meal entries")
        return meals

    def insert_meals(self, meals: List[Dict], dry_run: bool = False) -> Dict:
        """Insert meal logs into database."""
        from website.models import MealLog, MealType

        stats = {
            'inserted': 0,
            'failed': 0,
            'errors': []
        }

        # Map meal type strings to MealType enum
        type_mapping = {
            'breakfast': MealType.BREAKFAST,
            'lunch': MealType.LUNCH,
            'dinner': MealType.DINNER,
            'morning snack': MealType.SNACK,
            'afternoon snack': MealType.SNACK,
            'evening snack': MealType.SNACK,
            'snack': MealType.SNACK,
        }

        for meal in meals:
            try:
                # Validate date
                date_result = validate_date(meal['date'], 'meal_date')
                if not date_result:
                    logger.warning(f"Skipping meal with invalid date: {meal['date']}")
                    stats['failed'] += 1
                    continue

                # Determine meal type
                meal_type_str = meal['meal_type'].lower()
                meal_type = type_mapping.get(meal_type_str, MealType.OTHER)

                if dry_run:
                    logger.info(f"DRY RUN: Would insert {meal_type_str} on {date_result.value}")
                    stats['inserted'] += 1
                    continue

                # Create MealLog entry
                meal_log = MealLog(
                    user_id=self.user_id,
                    meal_date=date_result.value,
                    meal_type=meal_type,
                    description=sanitize_notes(meal.get('description')),
                    calories=meal.get('calories'),
                    notes=sanitize_notes(meal.get('notes'))
                )

                self.session.add(meal_log)
                stats['inserted'] += 1

            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Failed to insert meal on {meal['date']}: {e}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)

        # Commit
        if not dry_run and stats['inserted'] > 0:
            try:
                self.session.commit()
                logger.info(f"Committed {stats['inserted']} meal logs")
            except Exception as e:
                self.session.rollback()
                error_msg = f"Commit failed, rolled back: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                stats['failed'] += stats['inserted']
                stats['inserted'] = 0

        return stats

    def migrate(self, dry_run: bool = False) -> Dict:
        """Execute meal migration."""
        logger.info("="*60)
        logger.info("Starting Meal Migration")
        logger.info("="*60)

        # Parse meals
        logger.info("Step 1: Parsing meal-log.md...")
        meals = self.parse_markdown_table()

        if not meals:
            return {'status': 'error', 'message': 'No meals found'}

        # Insert meals
        logger.info(f"Step 2: Inserting {len(meals)} meals (dry_run={dry_run})...")
        stats = self.insert_meals(meals, dry_run=dry_run)

        results = {
            'status': 'success' if stats['failed'] == 0 else 'partial',
            'dry_run': dry_run,
            'source_file': str(self.source_file),
            'statistics': {
                'total_parsed': len(meals),
                'inserted': stats['inserted'],
                'failed': stats['failed']
            },
            'errors': stats['errors']
        }

        logger.info("="*60)
        logger.info(f"Meal Migration Complete: {stats['inserted']} inserted")
        logger.info("="*60)

        return results


def migrate_meals(session, user_id: int, dry_run: bool = False) -> Dict:
    """Convenience function to run meal migration."""
    migrator = MealMigrator(session, user_id)
    return migrator.migrate(dry_run=dry_run)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("\n=== Meal Migration Module ===")
    print("Run: python scripts/migrate_to_database.py --meals --user-id 1")
