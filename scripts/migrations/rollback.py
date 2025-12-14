"""
Rollback Utilities
==================

Provides rollback functionality for migrations.
Tracks migration metadata and allows reverting changes.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Optional
import logging
import json
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


class MigrationTracker:
    """Tracks migrations for rollback purposes"""

    def __init__(self, log_dir: Path = None):
        """
        Initialize migration tracker.

        Args:
            log_dir: Directory for migration logs (default: PROJECT_ROOT/logs)
        """
        if log_dir is None:
            self.log_dir = PROJECT_ROOT / 'logs' / 'migrations'
        else:
            self.log_dir = Path(log_dir)

        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_migration(self, migration_type: str, user_id: int, results: Dict) -> str:
        """
        Log migration execution for potential rollback.

        Args:
            migration_type: Type of migration (health, workouts, meals, coaching)
            user_id: User ID the migration was for
            results: Migration results dictionary

        Returns:
            Migration log ID (timestamp-based)
        """
        migration_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        log_entry = {
            'migration_id': migration_id,
            'migration_type': migration_type,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }

        log_file = self.log_dir / f'{migration_id}_{migration_type}_user{user_id}.json'

        with open(log_file, 'w') as f:
            json.dump(log_entry, f, indent=2, default=str)

        logger.info(f"Logged migration: {log_file.name}")
        return migration_id

    def get_migration_log(self, migration_id: str) -> Optional[Dict]:
        """
        Retrieve migration log by ID.

        Args:
            migration_id: Migration ID to retrieve

        Returns:
            Migration log dictionary or None if not found
        """
        # Find log file starting with migration_id
        for log_file in self.log_dir.glob(f'{migration_id}*.json'):
            with open(log_file, 'r') as f:
                return json.load(f)

        return None

    def list_migrations(self, user_id: Optional[int] = None) -> list:
        """
        List all logged migrations.

        Args:
            user_id: Filter by user ID (optional)

        Returns:
            List of migration log summaries
        """
        migrations = []

        for log_file in sorted(self.log_dir.glob('*.json'), reverse=True):
            try:
                with open(log_file, 'r') as f:
                    log_data = json.load(f)

                if user_id is None or log_data.get('user_id') == user_id:
                    migrations.append({
                        'migration_id': log_data.get('migration_id'),
                        'type': log_data.get('migration_type'),
                        'user_id': log_data.get('user_id'),
                        'timestamp': log_data.get('timestamp'),
                        'status': log_data.get('results', {}).get('status'),
                        'file': log_file.name
                    })

            except Exception as e:
                logger.error(f"Failed to read log file {log_file}: {e}")
                continue

        return migrations


class RollbackManager:
    """Manages rollback of migrations"""

    def __init__(self, db_session):
        """
        Initialize rollback manager.

        Args:
            db_session: SQLAlchemy database session
        """
        self.session = db_session
        self.tracker = MigrationTracker()

    def rollback_health_metrics(self, user_id: int, migration_id: str = None,
                                dry_run: bool = False) -> Dict:
        """
        Rollback health metrics migration.

        Args:
            user_id: User ID to rollback for
            migration_id: Specific migration to rollback (None = all)
            dry_run: If True, simulate without deleting

        Returns:
            Rollback results dictionary
        """
        from website.models import HealthMetric

        try:
            # Query all health metrics for user
            query = self.session.query(HealthMetric).filter_by(user_id=user_id)

            # If specific migration, filter by dates (would need date range in log)
            # For now, we rollback all for user

            count = query.count()

            if dry_run:
                logger.info(f"DRY RUN: Would delete {count} health metrics for user {user_id}")
                return {
                    'status': 'success',
                    'dry_run': True,
                    'would_delete': count
                }

            # Delete all health metrics
            query.delete()
            self.session.commit()

            logger.info(f"Rolled back {count} health metrics for user {user_id}")

            return {
                'status': 'success',
                'deleted': count
            }

        except Exception as e:
            self.session.rollback()
            error_msg = f"Rollback failed: {e}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }

    def rollback_workouts(self, user_id: int, dry_run: bool = False) -> Dict:
        """Rollback workout migrations."""
        from website.models import WorkoutSession

        try:
            query = self.session.query(WorkoutSession).filter_by(user_id=user_id)
            count = query.count()

            if dry_run:
                logger.info(f"DRY RUN: Would delete {count} workout sessions")
                return {'status': 'success', 'dry_run': True, 'would_delete': count}

            # Delete cascades to exercise logs
            query.delete()
            self.session.commit()

            logger.info(f"Rolled back {count} workout sessions")
            return {'status': 'success', 'deleted': count}

        except Exception as e:
            self.session.rollback()
            return {'status': 'error', 'error': str(e)}

    def rollback_meals(self, user_id: int, dry_run: bool = False) -> Dict:
        """Rollback meal log migrations."""
        from website.models import MealLog

        try:
            query = self.session.query(MealLog).filter_by(user_id=user_id)
            count = query.count()

            if dry_run:
                logger.info(f"DRY RUN: Would delete {count} meal logs")
                return {'status': 'success', 'dry_run': True, 'would_delete': count}

            query.delete()
            self.session.commit()

            logger.info(f"Rolled back {count} meal logs")
            return {'status': 'success', 'deleted': count}

        except Exception as e:
            self.session.rollback()
            return {'status': 'error', 'error': str(e)}

    def rollback_coaching(self, user_id: int, dry_run: bool = False) -> Dict:
        """Rollback coaching session migrations."""
        from website.models import CoachingSession

        try:
            query = self.session.query(CoachingSession).filter_by(user_id=user_id)
            count = query.count()

            if dry_run:
                logger.info(f"DRY RUN: Would delete {count} coaching sessions")
                return {'status': 'success', 'dry_run': True, 'would_delete': count}

            query.delete()
            self.session.commit()

            logger.info(f"Rolled back {count} coaching sessions")
            return {'status': 'success', 'deleted': count}

        except Exception as e:
            self.session.rollback()
            return {'status': 'error', 'error': str(e)}

    def rollback_all(self, user_id: int, dry_run: bool = False) -> Dict:
        """Rollback all migrations for a user."""
        logger.info(f"Rolling back ALL migrations for user {user_id} (dry_run={dry_run})")

        results = {
            'health': self.rollback_health_metrics(user_id, dry_run=dry_run),
            'workouts': self.rollback_workouts(user_id, dry_run=dry_run),
            'meals': self.rollback_meals(user_id, dry_run=dry_run),
            'coaching': self.rollback_coaching(user_id, dry_run=dry_run)
        }

        all_success = all(r['status'] == 'success' for r in results.values())

        return {
            'status': 'success' if all_success else 'partial',
            'dry_run': dry_run,
            'details': results
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("\n=== Rollback Utilities ===\n")
    print("To rollback migrations:")
    print("  python scripts/migrate_to_database.py --rollback --user-id 1")
    print("\nTo see migration history:")
    print("  python scripts/migrate_to_database.py --list-migrations")
