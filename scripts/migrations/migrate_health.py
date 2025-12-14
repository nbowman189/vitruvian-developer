"""
Health Metrics Migration
=========================

Migrates health data from check-in-log.md to the HealthMetric database table.
Parses markdown table format and validates before insertion.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import date

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migrations.validators import (
    validate_date, validate_weight, validate_body_fat,
    sanitize_notes, validate_health_metric_row
)

logger = logging.getLogger(__name__)


class HealthMetricsMigrator:
    """Migrates health metrics from markdown to database"""

    def __init__(self, db_session, user_id: int):
        """
        Initialize health metrics migrator.

        Args:
            db_session: SQLAlchemy database session
            user_id: User ID to associate metrics with
        """
        self.session = db_session
        self.user_id = user_id
        self.source_file = PROJECT_ROOT / 'Health_and_Fitness' / 'data' / 'check-in-log.md'

    def parse_markdown_table(self) -> List[Dict]:
        """
        Parse health metrics from check-in-log.md table format.

        Expected format:
        | Date | Weight (lbs) | Body Fat % | Notes |
        | 2024-11-14 | 175.5 | 22.3 | Feeling strong |

        Returns:
            List of dictionaries with parsed health metrics
        """
        if not self.source_file.exists():
            logger.error(f"Source file not found: {self.source_file}")
            return []

        metrics = []
        with open(self.source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Skip header and separator lines
        data_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('|') and not line.startswith('| :'):
                # Check if this is not the header line
                if 'Date' not in line and 'Weight' not in line:
                    data_lines.append(line)

        logger.info(f"Found {len(data_lines)} data rows in {self.source_file.name}")

        for line_num, line in enumerate(data_lines, start=1):
            try:
                # Split by pipe and strip whitespace
                parts = [p.strip() for p in line.split('|')]
                # Remove empty first and last elements from splitting
                parts = [p for p in parts if p]

                if len(parts) < 3:
                    logger.warning(f"Line {line_num}: Insufficient columns: {line}")
                    continue

                # Extract fields
                date_str = parts[0] if len(parts) > 0 else ''
                weight_str = parts[1] if len(parts) > 1 else ''
                body_fat_str = parts[2] if len(parts) > 2 else ''
                notes_str = parts[3] if len(parts) > 3 else ''

                metric = {
                    'date': date_str,
                    'weight': weight_str,
                    'body_fat': body_fat_str,
                    'notes': notes_str,
                    'line_number': line_num
                }

                metrics.append(metric)

            except Exception as e:
                logger.error(f"Line {line_num}: Parse error: {e}")
                continue

        logger.info(f"Parsed {len(metrics)} health metric entries")
        return metrics

    def validate_metrics(self, metrics: List[Dict]) -> tuple:
        """
        Validate parsed health metrics.

        Args:
            metrics: List of parsed metric dictionaries

        Returns:
            Tuple of (valid_metrics, invalid_metrics)
        """
        valid = []
        invalid = []

        for metric in metrics:
            is_valid, validated_data, errors = validate_health_metric_row(metric)

            if is_valid:
                valid.append({
                    **validated_data,
                    'line_number': metric.get('line_number')
                })
            else:
                invalid.append({
                    'line_number': metric.get('line_number'),
                    'data': metric,
                    'errors': errors
                })
                logger.warning(f"Line {metric.get('line_number')}: Validation failed: {errors}")

        logger.info(f"Validation: {len(valid)} valid, {len(invalid)} invalid")
        return valid, invalid

    def check_existing_metrics(self, metrics: List[Dict]) -> tuple:
        """
        Check which metrics already exist in database.

        Args:
            metrics: List of validated metric dictionaries

        Returns:
            Tuple of (new_metrics, duplicate_metrics)
        """
        from website.models import HealthMetric

        new_metrics = []
        duplicates = []

        for metric in metrics:
            recorded_date = metric['recorded_date']

            # Check if entry exists for this user and date
            existing = self.session.query(HealthMetric).filter_by(
                user_id=self.user_id,
                recorded_date=recorded_date
            ).first()

            if existing:
                duplicates.append({
                    'date': recorded_date,
                    'existing_weight': existing.weight_lbs,
                    'new_weight': metric.get('weight_lbs'),
                    'metric': metric
                })
                logger.debug(f"Duplicate found for {recorded_date}")
            else:
                new_metrics.append(metric)

        logger.info(f"Duplicate check: {len(new_metrics)} new, {len(duplicates)} duplicates")
        return new_metrics, duplicates

    def insert_metrics(self, metrics: List[Dict], dry_run: bool = False) -> Dict:
        """
        Insert health metrics into database.

        Args:
            metrics: List of validated metric dictionaries
            dry_run: If True, don't actually insert (just simulate)

        Returns:
            Dictionary with insertion statistics
        """
        from website.models import HealthMetric

        stats = {
            'total': len(metrics),
            'inserted': 0,
            'failed': 0,
            'errors': []
        }

        if dry_run:
            logger.info(f"DRY RUN: Would insert {len(metrics)} health metrics")
            stats['inserted'] = len(metrics)
            return stats

        for metric in metrics:
            try:
                # Create HealthMetric instance
                health_metric = HealthMetric(
                    user_id=self.user_id,
                    recorded_date=metric['recorded_date'],
                    weight_lbs=metric.get('weight_lbs'),
                    body_fat_percentage=metric.get('body_fat_percentage'),
                    notes=metric.get('notes')
                )

                self.session.add(health_metric)
                stats['inserted'] += 1

                logger.debug(f"Inserted: {metric['recorded_date']} - {metric.get('weight_lbs')} lbs")

            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Failed to insert {metric['recorded_date']}: {e}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)

        # Commit all insertions
        if stats['inserted'] > 0 and not dry_run:
            try:
                self.session.commit()
                logger.info(f"Successfully committed {stats['inserted']} health metrics")
            except Exception as e:
                self.session.rollback()
                error_msg = f"Commit failed, rolled back: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
                stats['failed'] = stats['inserted']
                stats['inserted'] = 0

        return stats

    def migrate(self, dry_run: bool = False, skip_duplicates: bool = True) -> Dict:
        """
        Execute complete health metrics migration.

        Args:
            dry_run: If True, don't actually insert data
            skip_duplicates: If True, skip existing entries

        Returns:
            Dictionary with migration results and statistics
        """
        logger.info("="*60)
        logger.info("Starting Health Metrics Migration")
        logger.info("="*60)

        # Step 1: Parse markdown file
        logger.info("Step 1: Parsing check-in-log.md...")
        raw_metrics = self.parse_markdown_table()

        if not raw_metrics:
            logger.error("No metrics found to migrate")
            return {'status': 'error', 'message': 'No data found'}

        # Step 2: Validate metrics
        logger.info("Step 2: Validating metrics...")
        valid_metrics, invalid_metrics = self.validate_metrics(raw_metrics)

        # Step 3: Check for duplicates
        if skip_duplicates:
            logger.info("Step 3: Checking for existing entries...")
            new_metrics, duplicates = self.check_existing_metrics(valid_metrics)
        else:
            new_metrics = valid_metrics
            duplicates = []

        # Step 4: Insert new metrics
        logger.info(f"Step 4: Inserting {len(new_metrics)} metrics (dry_run={dry_run})...")
        insert_stats = self.insert_metrics(new_metrics, dry_run=dry_run)

        # Compile results
        results = {
            'status': 'success' if insert_stats['failed'] == 0 else 'partial',
            'dry_run': dry_run,
            'source_file': str(self.source_file),
            'statistics': {
                'total_rows_parsed': len(raw_metrics),
                'valid_rows': len(valid_metrics),
                'invalid_rows': len(invalid_metrics),
                'duplicate_rows': len(duplicates),
                'new_rows': len(new_metrics),
                'inserted': insert_stats['inserted'],
                'failed': insert_stats['failed']
            },
            'invalid_entries': invalid_metrics if invalid_metrics else [],
            'duplicates': duplicates if duplicates else [],
            'errors': insert_stats.get('errors', [])
        }

        logger.info("="*60)
        logger.info("Health Metrics Migration Complete")
        logger.info("="*60)
        logger.info(f"Total parsed: {results['statistics']['total_rows_parsed']}")
        logger.info(f"Valid: {results['statistics']['valid_rows']}")
        logger.info(f"Invalid: {results['statistics']['invalid_rows']}")
        logger.info(f"Duplicates skipped: {results['statistics']['duplicate_rows']}")
        logger.info(f"Inserted: {results['statistics']['inserted']}")
        logger.info(f"Failed: {results['statistics']['failed']}")
        logger.info("="*60)

        return results


def migrate_health_metrics(session, user_id: int, dry_run: bool = False,
                           skip_duplicates: bool = True) -> Dict:
    """
    Convenience function to run health metrics migration.

    Args:
        session: SQLAlchemy database session
        user_id: User ID to associate metrics with
        dry_run: If True, simulate without inserting
        skip_duplicates: If True, skip existing entries

    Returns:
        Migration results dictionary
    """
    migrator = HealthMetricsMigrator(session, user_id)
    return migrator.migrate(dry_run=dry_run, skip_duplicates=skip_duplicates)


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # For standalone testing (requires database setup)
    print("\n=== Health Metrics Migration Module ===\n")
    print("This module migrates health data from check-in-log.md to the database.")
    print("\nTo run migration:")
    print("  python scripts/migrate_to_database.py --health --user-id 1")
    print("\nFor dry run:")
    print("  python scripts/migrate_to_database.py --health --user-id 1 --dry-run")
