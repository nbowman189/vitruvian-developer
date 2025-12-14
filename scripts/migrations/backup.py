"""
Backup and Restore Utilities
==============================

Provides backup and restore functionality for markdown files and database.
Creates timestamped backups before migrations for safety and rollback capability.
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages backup and restore operations for migration safety"""

    def __init__(self, backup_root: str = None, project_root: str = None):
        """
        Initialize backup manager.

        Args:
            backup_root: Root directory for backups (default: project_root/backups)
            project_root: Project root directory (default: auto-detect)
        """
        if project_root is None:
            # Auto-detect project root (go up from scripts/migrations/)
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)

        if backup_root is None:
            self.backup_root = self.project_root / 'backups'
        else:
            self.backup_root = Path(backup_root)

        self.backup_root.mkdir(parents=True, exist_ok=True)

    def create_timestamped_backup_dir(self) -> Path:
        """
        Create a timestamped backup directory.

        Returns:
            Path to created backup directory
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        backup_dir = self.backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created backup directory: {backup_dir}")
        return backup_dir

    def backup_markdown_files(self, backup_dir: Path = None) -> dict:
        """
        Backup all markdown files from Health_and_Fitness/data/ directory.

        Args:
            backup_dir: Backup directory (creates new timestamped dir if None)

        Returns:
            Dictionary with backup metadata
        """
        if backup_dir is None:
            backup_dir = self.create_timestamped_backup_dir()

        source_dir = self.project_root / 'Health_and_Fitness' / 'data'
        if not source_dir.exists():
            logger.warning(f"Source directory does not exist: {source_dir}")
            return {'status': 'skipped', 'reason': 'source_not_found'}

        # Create markdown backup subdirectory
        md_backup_dir = backup_dir / 'markdown_files'
        md_backup_dir.mkdir(parents=True, exist_ok=True)

        backed_up_files = []
        errors = []

        # Backup all markdown and related files
        for file_path in source_dir.glob('**/*'):
            if file_path.is_file():
                try:
                    relative_path = file_path.relative_to(source_dir)
                    dest_path = md_backup_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    shutil.copy2(file_path, dest_path)
                    backed_up_files.append(str(relative_path))
                    logger.debug(f"Backed up: {relative_path}")

                except Exception as e:
                    error_msg = f"Failed to backup {file_path}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)

        # Write backup manifest
        manifest_path = md_backup_dir / 'BACKUP_MANIFEST.txt'
        with open(manifest_path, 'w') as f:
            f.write(f"Backup created: {datetime.now().isoformat()}\n")
            f.write(f"Source directory: {source_dir}\n")
            f.write(f"Files backed up: {len(backed_up_files)}\n")
            f.write(f"Errors: {len(errors)}\n\n")
            f.write("Files:\n")
            for file in sorted(backed_up_files):
                f.write(f"  - {file}\n")
            if errors:
                f.write("\nErrors:\n")
                for error in errors:
                    f.write(f"  - {error}\n")

        logger.info(f"Backed up {len(backed_up_files)} markdown files to {md_backup_dir}")

        return {
            'status': 'success',
            'backup_dir': str(backup_dir),
            'markdown_dir': str(md_backup_dir),
            'files_backed_up': len(backed_up_files),
            'errors': errors
        }

    def backup_database(self, backup_dir: Path = None, db_config: dict = None) -> dict:
        """
        Backup database using pg_dump.

        Args:
            backup_dir: Backup directory (creates new timestamped dir if None)
            db_config: Database configuration dict with user, password, host, port, db

        Returns:
            Dictionary with backup metadata
        """
        if backup_dir is None:
            backup_dir = self.create_timestamped_backup_dir()

        if db_config is None:
            # Load from environment
            db_config = {
                'user': os.environ.get('POSTGRES_USER', 'portfolio_user'),
                'password': os.environ.get('POSTGRES_PASSWORD', ''),
                'host': os.environ.get('POSTGRES_HOST', 'localhost'),
                'port': os.environ.get('POSTGRES_PORT', '5432'),
                'database': os.environ.get('POSTGRES_DB', 'portfolio_db'),
            }

        db_backup_file = backup_dir / 'database_backup.sql'

        try:
            # Set password environment variable for pg_dump
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']

            # Run pg_dump
            cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['user'],
                '-d', db_config['database'],
                '-f', str(db_backup_file),
                '--clean',  # Include DROP statements
                '--if-exists',  # Use IF EXISTS for drops
                '--no-owner',  # Don't set ownership
                '--no-privileges',  # Don't set privileges
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                error_msg = f"pg_dump failed: {result.stderr}"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'error': error_msg
                }

            # Write backup metadata
            metadata_path = backup_dir / 'database_backup_metadata.txt'
            with open(metadata_path, 'w') as f:
                f.write(f"Database backup created: {datetime.now().isoformat()}\n")
                f.write(f"Database: {db_config['database']}\n")
                f.write(f"Host: {db_config['host']}:{db_config['port']}\n")
                f.write(f"User: {db_config['user']}\n")
                f.write(f"Backup file: {db_backup_file.name}\n")
                f.write(f"File size: {db_backup_file.stat().st_size} bytes\n")

            logger.info(f"Database backed up to {db_backup_file}")

            return {
                'status': 'success',
                'backup_file': str(db_backup_file),
                'size_bytes': db_backup_file.stat().st_size
            }

        except Exception as e:
            error_msg = f"Database backup failed: {e}"
            logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }

    def create_full_backup(self, db_config: dict = None) -> dict:
        """
        Create a complete backup of both markdown files and database.

        Args:
            db_config: Database configuration (uses environment if None)

        Returns:
            Dictionary with complete backup metadata
        """
        logger.info("Starting full backup (markdown + database)...")

        backup_dir = self.create_timestamped_backup_dir()

        # Backup markdown files
        md_result = self.backup_markdown_files(backup_dir)

        # Backup database
        db_result = self.backup_database(backup_dir, db_config)

        # Write summary
        summary_path = backup_dir / 'BACKUP_SUMMARY.txt'
        with open(summary_path, 'w') as f:
            f.write(f"Full Backup Summary\n")
            f.write(f"==================\n\n")
            f.write(f"Created: {datetime.now().isoformat()}\n")
            f.write(f"Backup directory: {backup_dir}\n\n")

            f.write(f"Markdown Files:\n")
            f.write(f"  Status: {md_result['status']}\n")
            if md_result['status'] == 'success':
                f.write(f"  Files backed up: {md_result['files_backed_up']}\n")
                f.write(f"  Errors: {len(md_result['errors'])}\n")
            f.write(f"\n")

            f.write(f"Database:\n")
            f.write(f"  Status: {db_result['status']}\n")
            if db_result['status'] == 'success':
                f.write(f"  Backup file: {Path(db_result['backup_file']).name}\n")
                f.write(f"  Size: {db_result['size_bytes']:,} bytes\n")
            elif db_result['status'] == 'error':
                f.write(f"  Error: {db_result['error']}\n")

        logger.info(f"Full backup completed: {backup_dir}")

        return {
            'status': 'success',
            'backup_dir': str(backup_dir),
            'markdown': md_result,
            'database': db_result
        }

    def restore_markdown_files(self, backup_dir: Path, target_dir: Path = None) -> dict:
        """
        Restore markdown files from backup.

        Args:
            backup_dir: Backup directory containing markdown_files/
            target_dir: Target directory to restore to (default: original location)

        Returns:
            Dictionary with restore metadata
        """
        backup_dir = Path(backup_dir)
        md_backup_dir = backup_dir / 'markdown_files'

        if not md_backup_dir.exists():
            return {
                'status': 'error',
                'error': f"Markdown backup not found: {md_backup_dir}"
            }

        if target_dir is None:
            target_dir = self.project_root / 'Health_and_Fitness' / 'data'

        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        restored_files = []
        errors = []

        for file_path in md_backup_dir.rglob('*'):
            if file_path.is_file() and file_path.name != 'BACKUP_MANIFEST.txt':
                try:
                    relative_path = file_path.relative_to(md_backup_dir)
                    dest_path = target_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    shutil.copy2(file_path, dest_path)
                    restored_files.append(str(relative_path))
                    logger.debug(f"Restored: {relative_path}")

                except Exception as e:
                    error_msg = f"Failed to restore {file_path}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)

        logger.info(f"Restored {len(restored_files)} markdown files")

        return {
            'status': 'success' if len(errors) == 0 else 'partial',
            'files_restored': len(restored_files),
            'errors': errors
        }

    def list_backups(self) -> List[dict]:
        """
        List all available backups.

        Returns:
            List of backup metadata dictionaries
        """
        backups = []

        for backup_dir in sorted(self.backup_root.iterdir(), reverse=True):
            if backup_dir.is_dir():
                summary_file = backup_dir / 'BACKUP_SUMMARY.txt'
                metadata = {
                    'timestamp': backup_dir.name,
                    'path': str(backup_dir),
                    'has_summary': summary_file.exists()
                }

                # Check for markdown backup
                md_dir = backup_dir / 'markdown_files'
                metadata['has_markdown'] = md_dir.exists()
                if md_dir.exists():
                    md_files = list(md_dir.rglob('*.md'))
                    metadata['markdown_file_count'] = len(md_files)

                # Check for database backup
                db_file = backup_dir / 'database_backup.sql'
                metadata['has_database'] = db_file.exists()
                if db_file.exists():
                    metadata['database_size_bytes'] = db_file.stat().st_size

                backups.append(metadata)

        return backups

    def verify_backup(self, backup_dir: Path) -> dict:
        """
        Verify backup integrity.

        Args:
            backup_dir: Backup directory to verify

        Returns:
            Verification results dictionary
        """
        backup_dir = Path(backup_dir)

        if not backup_dir.exists():
            return {
                'valid': False,
                'error': 'Backup directory does not exist'
            }

        issues = []

        # Check for markdown backup
        md_dir = backup_dir / 'markdown_files'
        has_markdown = md_dir.exists()
        if has_markdown:
            md_files = list(md_dir.rglob('*'))
            md_file_count = len([f for f in md_files if f.is_file()])
        else:
            issues.append("Missing markdown_files directory")
            md_file_count = 0

        # Check for database backup
        db_file = backup_dir / 'database_backup.sql'
        has_database = db_file.exists()
        if has_database:
            db_size = db_file.stat().st_size
            if db_size == 0:
                issues.append("Database backup file is empty")
        else:
            issues.append("Missing database_backup.sql file")
            db_size = 0

        is_valid = len(issues) == 0 and (has_markdown or has_database)

        return {
            'valid': is_valid,
            'has_markdown': has_markdown,
            'markdown_file_count': md_file_count,
            'has_database': has_database,
            'database_size_bytes': db_size,
            'issues': issues
        }


if __name__ == '__main__':
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create backup manager
    manager = BackupManager()

    print("\n=== Backup Manager Demo ===\n")

    # List existing backups
    print("Existing backups:")
    backups = manager.list_backups()
    if backups:
        for backup in backups[:5]:  # Show last 5
            print(f"  - {backup['timestamp']}")
            if backup.get('markdown_file_count'):
                print(f"    Markdown files: {backup['markdown_file_count']}")
            if backup.get('database_size_bytes'):
                print(f"    Database: {backup['database_size_bytes']:,} bytes")
    else:
        print("  No backups found")

    print("\nTo create a full backup, run:")
    print("  python scripts/migrations/backup.py --create")
