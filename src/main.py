#!/usr/bin/env python3
"""
Bevy Engine Migration Tool
Main entry point for migrating Bevy projects from version 0.15 to 0.18
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from core.migration_engine import MigrationEngine
from utils.version_detector import VersionDetector


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Bevy Engine Migration Tool - Migrate from v0.12 to v0.18',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py /path/to/bevy/project
  python src/main.py /path/to/bevy/project --target-version 0.17
  python src/main.py /path/to/bevy/project --dry-run --verbose
  python src/main.py /path/to/bevy/project --backup-dir ./backups
        """
    )
    
    parser.add_argument(
        'project_path',
        type=str,
        help='Path to the Bevy project directory'
    )
    
    parser.add_argument(
        '--target-version',
        type=str,
        default='0.18',
        choices=['0.13', '0.16', '0.17', '0.18'],
        help='Target Bevy version to migrate to (default: 0.18)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making actual changes'
    )
    
    parser.add_argument(
        '--backup-dir',
        type=str,
        help='Directory to store backup files (default: project_path/migration_backup)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force migration even if project version is unclear'
    )
    
    parser.add_argument(
        '--exclude',
        type=str,
        nargs='*',
        default=[],
        help='Exclude specific files or directories from migration'
    )
    
    return parser.parse_args()


def validate_project_path(project_path: Path) -> bool:
    """Validate that the project path exists and looks like a Rust project"""
    if not project_path.exists():
        logging.error(f"Project path does not exist: {project_path}")
        return False
    
    if not project_path.is_dir():
        logging.error(f"Project path is not a directory: {project_path}")
        return False
    
    # Check for Cargo.toml
    cargo_toml = project_path / "Cargo.toml"
    if not cargo_toml.exists():
        logging.error(f"No Cargo.toml found in project directory: {project_path}")
        return False
    
    return True


def main() -> int:
    """Main entry point"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Setup logging
        setup_logging(args.verbose)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting Bevy Engine Migration Tool")
        logger.info(f"Project path: {args.project_path}")
        logger.info(f"Target version: {args.target_version}")
        
        # Validate project path
        project_path = Path(args.project_path).resolve()
        if not validate_project_path(project_path):
            return 1
        
        # Detect current Bevy version
        version_detector = VersionDetector()
        current_version = version_detector.detect_version(project_path)
        
        if current_version is None:
            if not args.force:
                logger.error("Could not detect current Bevy version. Use --force to proceed anyway.")
                return 1
            else:
                logger.warning("Could not detect current Bevy version, proceeding with --force")
                current_version = "0.12"  # Assume oldest supported version
        
        logger.info(f"Detected current Bevy version: {current_version}")
        
        # Check if migration is needed
        if current_version == args.target_version:
            logger.info(f"Project is already at target version {args.target_version}")
            return 0
        
        # Validate version progression
        version_order = ["0.12", "0.13", "0.15", "0.16", "0.17", "0.18"]
        try:
            current_idx = version_order.index(current_version)
            target_idx = version_order.index(args.target_version)
        except ValueError:
            logger.error(f"Unsupported version detected: {current_version}")
            return 1
        
        if current_idx >= target_idx:
            logger.error(f"Cannot migrate backwards from {current_version} to {args.target_version}")
            return 1
        
        # Setup backup directory
        backup_dir = None
        if args.backup_dir:
            backup_dir = Path(args.backup_dir).resolve()
        else:
            backup_dir = project_path / "migration_backup"
        
        # Initialize migration engine
        migration_engine = MigrationEngine(
            project_path=project_path,
            backup_dir=backup_dir,
            dry_run=args.dry_run,
            exclude_patterns=args.exclude
        )
        
        # Perform migration
        logger.info(f"Starting migration from {current_version} to {args.target_version}")
        
        success = migration_engine.migrate(
            from_version=current_version,
            to_version=args.target_version
        )
        
        if success:
            if args.dry_run:
                logger.info("Dry run completed successfully. No files were modified.")
            else:
                logger.info(f"Migration completed successfully!")
                logger.info(f"Project migrated from Bevy {current_version} to {args.target_version}")
                if backup_dir.exists():
                    logger.info(f"Backup files stored in: {backup_dir}")
            return 0
        else:
            logger.error("Migration failed. Check the logs for details.")
            return 1
            
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Migration interrupted by user")
        return 130
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())