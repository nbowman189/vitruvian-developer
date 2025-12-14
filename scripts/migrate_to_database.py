#!/usr/bin/env python3
"""
Main Migration Orchestrator
============================

Comprehensive data migration tool for moving markdown files to PostgreSQL database.

Usage:
    # Full migration with backup
    python scripts/migrate_to_database.py --all --user-id 1 --backup

    # Specific migrations
    python scripts/migrate_to_database.py --health --user-id 1
    python scripts/migrate_to_database.py --workouts --meals --user-id 1

    # Dry run (preview only)
    python scripts/migrate_to_database.py --all --user-id 1 --dry-run

    # Rollback
    python scripts/migrate_to_database.py --rollback --user-id 1

    # List migration history
    python scripts/migrate_to_database.py --list-migrations
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
LOG_DIR = PROJECT_ROOT / 'logs'
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def setup_database():
    """Setup database connection and session."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Initialize Flask app and database
    from website import create_app
    from website.models import db

    app = create_app()

    with app.app_context():
        # Test database connection
        try:
            db.session.execute(db.text('SELECT 1'))
            logger.info("Database connection successful")
            return db.session
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            sys.exit(1)


def run_backup():
    """Create full backup before migration."""
    from scripts.migrations.backup import BackupManager

    logger.info("=" * 70)
    logger.info("Creating backup before migration...")
    logger.info("=" * 70)

    manager = BackupManager()
    result = manager.create_full_backup()

    if result.get('database', {}).get('status') == 'success':
        logger.info(f"Backup completed: {result['backup_dir']}")
        return result['backup_dir']
    else:
        logger.warning("Backup partially failed, but continuing with migration")
        return None


def run_health_migration(session, user_id: int, dry_run: bool = False):
    """Run health metrics migration."""
    from scripts.migrations.migrate_health import migrate_health_metrics

    logger.info("\n" + "=" * 70)
    logger.info("HEALTH METRICS MIGRATION")
    logger.info("=" * 70)

    results = migrate_health_metrics(session, user_id, dry_run=dry_run)
    return results


def run_workouts_migration(session, user_id: int, dry_run: bool = False):
    """Run workouts migration."""
    from scripts.migrations.migrate_workouts import migrate_workouts

    logger.info("\n" + "=" * 70)
    logger.info("WORKOUTS MIGRATION")
    logger.info("=" * 70)

    results = migrate_workouts(session, user_id, dry_run=dry_run)
    return results


def run_meals_migration(session, user_id: int, dry_run: bool = False):
    """Run meals migration."""
    from scripts.migrations.migrate_meals import migrate_meals

    logger.info("\n" + "=" * 70)
    logger.info("MEALS MIGRATION")
    logger.info("=" * 70)

    results = migrate_meals(session, user_id, dry_run=dry_run)
    return results


def run_coaching_migration(session, user_id: int, coach_id: int, dry_run: bool = False):
    """Run coaching migration."""
    from scripts.migrations.migrate_coaching import migrate_coaching

    logger.info("\n" + "=" * 70)
    logger.info("COACHING MIGRATION")
    logger.info("=" * 70)

    results = migrate_coaching(session, user_id, coach_id, dry_run=dry_run)
    return results


def run_rollback(session, user_id: int, migration_type: str = 'all', dry_run: bool = False):
    """Run rollback for migrations."""
    from scripts.migrations.rollback import RollbackManager

    logger.info("\n" + "=" * 70)
    logger.info(f"ROLLBACK: {migration_type.upper()}")
    logger.info("=" * 70)

    manager = RollbackManager(session)

    if migration_type == 'all':
        results = manager.rollback_all(user_id, dry_run=dry_run)
    elif migration_type == 'health':
        results = manager.rollback_health_metrics(user_id, dry_run=dry_run)
    elif migration_type == 'workouts':
        results = manager.rollback_workouts(user_id, dry_run=dry_run)
    elif migration_type == 'meals':
        results = manager.rollback_meals(user_id, dry_run=dry_run)
    elif migration_type == 'coaching':
        results = manager.rollback_coaching(user_id, dry_run=dry_run)
    else:
        logger.error(f"Unknown migration type: {migration_type}")
        return {'status': 'error', 'error': 'Unknown migration type'}

    return results


def list_migrations(user_id: int = None):
    """List migration history."""
    from scripts.migrations.rollback import MigrationTracker

    tracker = MigrationTracker()
    migrations = tracker.list_migrations(user_id=user_id)

    print("\n" + "=" * 70)
    print("MIGRATION HISTORY")
    print("=" * 70)

    if not migrations:
        print("No migrations found")
        return

    for mig in migrations:
        print(f"\nMigration ID: {mig['migration_id']}")
        print(f"  Type: {mig['type']}")
        print(f"  User ID: {mig['user_id']}")
        print(f"  Timestamp: {mig['timestamp']}")
        print(f"  Status: {mig['status']}")


def print_summary(all_results: dict):
    """Print migration summary."""
    print("\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)

    for name, results in all_results.items():
        print(f"\n{name.upper()}:")
        if results:
            print(f"  Status: {results.get('status', 'unknown')}")
            if 'statistics' in results:
                for key, value in results['statistics'].items():
                    print(f"  {key}: {value}")
            if results.get('errors'):
                print(f"  Errors: {len(results['errors'])}")
        else:
            print("  Not run")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Migrate markdown data to PostgreSQL database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Migration selection
    parser.add_argument('--all', action='store_true', help='Run all migrations')
    parser.add_argument('--health', action='store_true', help='Migrate health metrics')
    parser.add_argument('--workouts', action='store_true', help='Migrate workouts')
    parser.add_argument('--meals', action='store_true', help='Migrate meals')
    parser.add_argument('--coaching', action='store_true', help='Migrate coaching sessions')

    # User identification
    parser.add_argument('--user-id', type=int, help='User ID to migrate data for', required=False)
    parser.add_argument('--coach-id', type=int, help='Coach ID for coaching sessions (default: same as user-id)')

    # Options
    parser.add_argument('--dry-run', action='store_true', help='Simulate migration without inserting data')
    parser.add_argument('--backup', action='store_true', help='Create backup before migration')
    parser.add_argument('--skip-duplicates', action='store_true', default=True,
                       help='Skip duplicate entries (default: True)')

    # Rollback
    parser.add_argument('--rollback', action='store_true', help='Rollback migrations')
    parser.add_argument('--rollback-type', choices=['all', 'health', 'workouts', 'meals', 'coaching'],
                       default='all', help='Type of rollback to perform')

    # Utilities
    parser.add_argument('--list-migrations', action='store_true', help='List migration history')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # List migrations mode
    if args.list_migrations:
        list_migrations(user_id=args.user_id)
        return

    # Rollback mode
    if args.rollback:
        if not args.user_id:
            logger.error("--user-id is required for rollback")
            sys.exit(1)

        session = setup_database()
        results = run_rollback(session, args.user_id, args.rollback_type, args.dry_run)

        if results['status'] == 'success':
            logger.info("Rollback completed successfully")
        else:
            logger.error("Rollback failed or partial")
        return

    # Migration mode
    if not any([args.all, args.health, args.workouts, args.meals, args.coaching]):
        parser.print_help()
        sys.exit(1)

    if not args.user_id:
        logger.error("--user-id is required for migration")
        sys.exit(1)

    # Set coach ID (default to user ID if not specified)
    coach_id = args.coach_id if args.coach_id else args.user_id

    logger.info("=" * 70)
    logger.info("MIGRATION ORCHESTRATOR")
    logger.info("=" * 70)
    logger.info(f"User ID: {args.user_id}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info(f"Backup: {args.backup}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 70)

    # Create backup if requested
    if args.backup and not args.dry_run:
        backup_dir = run_backup()
    else:
        backup_dir = None

    # Setup database
    session = setup_database()

    # Track results
    all_results = {}

    # Run selected migrations
    try:
        if args.all or args.health:
            all_results['health'] = run_health_migration(session, args.user_id, args.dry_run)

        if args.all or args.workouts:
            all_results['workouts'] = run_workouts_migration(session, args.user_id, args.dry_run)

        if args.all or args.meals:
            all_results['meals'] = run_meals_migration(session, args.user_id, args.dry_run)

        if args.all or args.coaching:
            all_results['coaching'] = run_coaching_migration(session, args.user_id, coach_id, args.dry_run)

    except Exception as e:
        logger.error(f"Migration failed with exception: {e}", exc_info=True)
        sys.exit(1)

    # Print summary
    print_summary(all_results)

    # Log migration for rollback tracking
    if not args.dry_run:
        from scripts.migrations.rollback import MigrationTracker
        tracker = MigrationTracker()

        for migration_type, results in all_results.items():
            if results and results.get('status') in ['success', 'partial']:
                tracker.log_migration(migration_type, args.user_id, results)

    logger.info(f"\nMigration log saved to: {log_file}")

    if args.dry_run:
        logger.info("\nDRY RUN COMPLETE - No data was modified")
    else:
        logger.info("\nMIGRATION COMPLETE")


if __name__ == '__main__':
    main()
