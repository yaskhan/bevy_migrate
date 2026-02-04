"""
Migration Engine - Core component for managing Bevy version migrations
Handles the orchestration of migration steps and coordination between modules
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Type
from datetime import datetime

from migrations.base_migration import BaseMigration
from migrations.v0_12_to_0_13 import Migration_0_12_to_0_13
from migrations.v0_13_to_0_14 import Migration_0_13_to_0_14
from migrations.v0_14_to_0_15_part1 import Migration_0_14_to_0_15_Part1
from migrations.v0_14_to_0_15_part2 import Migration_0_14_to_0_15_Part2
from migrations.v0_15_to_0_16 import Migration_0_15_to_0_16
from migrations.v0_16_to_0_17_part1 import Migration_0_16_to_0_17_Part1
from migrations.v0_16_to_0_17_part2 import Migration_0_16_to_0_17_Part2
from migrations.v0_16_to_0_17_part3 import Migration_0_16_to_0_17_Part3
from migrations.v0_17_to_0_18 import Migration_0_17_to_0_18
from core.file_manager import FileManager
from utils.version_detector import VersionDetector


class MigrationEngine:
    """
    Core migration engine that orchestrates the migration process
    """
    
    def __init__(
        self,
        project_path: Path,
        backup_dir: Optional[Path] = None,
        dry_run: bool = False,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Initialize the migration engine
        
        Args:
            project_path: Path to the Bevy project
            backup_dir: Directory to store backups (optional)
            dry_run: If True, only show what would be changed
            exclude_patterns: List of file/directory patterns to exclude
        """
        self.project_path = project_path
        self.backup_dir = backup_dir or (project_path / "migration_backup")
        self.dry_run = dry_run
        self.exclude_patterns = exclude_patterns or []
        
        self.logger = logging.getLogger(__name__)
        self.file_manager = FileManager(project_path, exclude_patterns)
        self.version_detector = VersionDetector()
        
        # Registry of available migrations
        self._migration_registry: Dict[str, Type[BaseMigration]] = {
            "0.12->0.13": Migration_0_12_to_0_13,
            "0.13->0.14": Migration_0_13_to_0_14,
            "0.14->0.15-part1": Migration_0_14_to_0_15_Part1,
            "0.15-part1->0.15": Migration_0_14_to_0_15_Part2,
            "0.15->0.16": Migration_0_15_to_0_16,
            "0.16->0.17-part1": Migration_0_16_to_0_17_Part1,
            "0.17-part1->0.17-part2": Migration_0_16_to_0_17_Part2,
            "0.17-part2->0.17": Migration_0_16_to_0_17_Part3,
            "0.17->0.18": Migration_0_17_to_0_18,
        }
        
        # Version progression mapping
        self._version_progression = {
            "0.12": "0.13",
            "0.13": "0.14",
            "0.14": "0.15-part1",
            "0.15-part1": "0.15",
            "0.15": "0.16",
            "0.16": "0.17-part1",
            "0.17-part1": "0.17-part2",
            "0.17-part2": "0.17",
            "0.17": "0.18"
        }
        
        self.logger.info(f"Migration engine initialized for project: {project_path}")
        self.logger.info(f"Dry run mode: {dry_run}")
        self.logger.info(f"Backup directory: {self.backup_dir}")
    
    def migrate(self, from_version: str, to_version: str) -> bool:
        """
        Perform migration from one version to another
        
        Args:
            from_version: Starting Bevy version
            to_version: Target Bevy version
            
        Returns:
            True if migration was successful, False otherwise
        """
        try:
            self.logger.info(f"Starting migration from {from_version} to {to_version}")
            
            # Validate versions
            if not self._validate_versions(from_version, to_version):
                return False
            
            # Create backup if not in dry run mode
            if not self.dry_run:
                if not self._create_backup():
                    self.logger.error("Failed to create backup")
                    return False
            
            # Get migration path
            migration_steps = self._get_migration_path(from_version, to_version)
            if not migration_steps:
                self.logger.error(f"No migration path found from {from_version} to {to_version}")
                return False
            
            self.logger.info(f"Migration path: {' -> '.join([step[0] for step in migration_steps] + [migration_steps[-1][1]])}")
            
            # Execute migration steps
            for step_from, step_to in migration_steps:
                if not self._execute_migration_step(step_from, step_to):
                    self.logger.error(f"Migration step {step_from} -> {step_to} failed")
                    return False
            
            # Update project version if not in dry run mode
            if not self.dry_run:
                self._update_project_version(to_version)
            
            self.logger.info(f"Migration from {from_version} to {to_version} completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration failed with error: {e}", exc_info=True)
            return False
    
    def _validate_versions(self, from_version: str, to_version: str) -> bool:
        """Validate that the version migration is supported"""
        supported_versions = ["0.12", "0.13", "0.14", "0.15", "0.16", "0.17", "0.18"]
        
        if from_version not in supported_versions:
            self.logger.error(f"Unsupported source version: {from_version}")
            return False
        
        if to_version not in supported_versions:
            self.logger.error(f"Unsupported target version: {to_version}")
            return False
        
        # Check version order
        version_order = {v: i for i, v in enumerate(supported_versions)}
        if version_order[from_version] >= version_order[to_version]:
            self.logger.error(f"Cannot migrate backwards from {from_version} to {to_version}")
            return False
        
        return True
    
    def _get_migration_path(self, from_version: str, to_version: str) -> List[tuple]:
        """
        Get the sequence of migration steps needed to go from one version to another
        
        Returns:
            List of (from_version, to_version) tuples representing migration steps
        """
        path = []
        current_version = from_version
        
        while current_version != to_version:
            next_version = self._version_progression.get(current_version)
            if not next_version:
                self.logger.error(f"No migration path from {current_version}")
                return []
            
            path.append((current_version, next_version))
            current_version = next_version
            
            # Safety check to prevent infinite loops
            if len(path) > 10:
                self.logger.error("Migration path too long, possible circular dependency")
                return []
        
        return path
    
    def _execute_migration_step(self, from_version: str, to_version: str) -> bool:
        """Execute a single migration step"""
        migration_key = f"{from_version}->{to_version}"
        
        if migration_key not in self._migration_registry:
            self.logger.error(f"No migration available for {migration_key}")
            return False
        
        self.logger.info(f"Executing migration step: {migration_key}")
        
        # Get migration class and instantiate
        migration_class = self._migration_registry[migration_key]
        migration = migration_class(
            project_path=self.project_path,
            file_manager=self.file_manager,
            dry_run=self.dry_run
        )
        
        # Execute the migration
        try:
            success = migration.execute()
            if success:
                self.logger.info(f"Migration step {migration_key} completed successfully")
            else:
                self.logger.error(f"Migration step {migration_key} failed")
            return success
        except Exception as e:
            self.logger.error(f"Migration step {migration_key} failed with error: {e}", exc_info=True)
            return False
    
    def _create_backup(self) -> bool:
        """Create a backup of the project before migration"""
        try:
            if self.backup_dir.exists():
                # Create timestamped backup directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.backup_dir / f"backup_{timestamp}"
            else:
                backup_path = self.backup_dir
            
            self.logger.info(f"Creating backup at: {backup_path}")
            
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy important files
            files_to_backup = [
                "Cargo.toml",
                "Cargo.lock",
                "src/",
                "examples/",
                "assets/",
                "benches/",
                "tests/"
            ]
            
            for file_pattern in files_to_backup:
                source_path = self.project_path / file_pattern
                if source_path.exists():
                    dest_path = backup_path / file_pattern
                    
                    if source_path.is_file():
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, dest_path)
                    elif source_path.is_dir():
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                    
                    self.logger.debug(f"Backed up: {source_path} -> {dest_path}")
            
            self.logger.info("Backup created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}", exc_info=True)
            return False
    
    def _update_project_version(self, new_version: str) -> None:
        """Update the project's Bevy version in Cargo.toml"""
        try:
            cargo_toml_path = self.project_path / "Cargo.toml"
            if not cargo_toml_path.exists():
                self.logger.warning("Cargo.toml not found, cannot update version")
                return
            
            # Read current content
            content = cargo_toml_path.read_text(encoding='utf-8')
            
            # Update bevy dependency version
            # This is a simple regex-based approach
            import re
            
            # Pattern to match bevy dependency lines
            patterns = [
                r'(bevy\s*=\s*")[^"]*(")',  # bevy = "0.15"
                r'(bevy\s*=\s*\{\s*version\s*=\s*")[^"]*(")',  # bevy = { version = "0.15" }
            ]
            
            updated = False
            for pattern in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, f'\\g<1>{new_version}\\g<2>', content)
                    updated = True
            
            if updated:
                cargo_toml_path.write_text(content, encoding='utf-8')
                self.logger.info(f"Updated Cargo.toml with Bevy version {new_version}")
            else:
                self.logger.warning("Could not find Bevy dependency in Cargo.toml to update")
                
        except Exception as e:
            self.logger.error(f"Failed to update project version: {e}", exc_info=True)
    
    def get_available_migrations(self) -> List[str]:
        """Get list of available migration paths"""
        return list(self._migration_registry.keys())
    
    def validate_project(self) -> bool:
        """Validate that the project is a valid Bevy project"""
        try:
            # Check for Cargo.toml
            cargo_toml = self.project_path / "Cargo.toml"
            if not cargo_toml.exists():
                self.logger.error("No Cargo.toml found in project")
                return False
            
            # Check for src directory
            src_dir = self.project_path / "src"
            if not src_dir.exists():
                self.logger.error("No src directory found in project")
                return False
            
            # Try to detect if Bevy is used
            cargo_content = cargo_toml.read_text(encoding='utf-8')
            if 'bevy' not in cargo_content.lower():
                self.logger.warning("Bevy dependency not found in Cargo.toml")
                # Don't return False here as it might be in a workspace
            
            return True
            
        except Exception as e:
            self.logger.error(f"Project validation failed: {e}", exc_info=True)
            return False
    
    def get_migration_summary(self, from_version: str, to_version: str) -> Dict:
        """Get a summary of what the migration will do"""
        summary = {
            "from_version": from_version,
            "to_version": to_version,
            "migration_steps": [],
            "estimated_files": 0,
            "backup_required": not self.dry_run
        }
        
        try:
            migration_steps = self._get_migration_path(from_version, to_version)
            
            for step_from, step_to in migration_steps:
                migration_key = f"{step_from}->{step_to}"
                if migration_key in self._migration_registry:
                    migration_class = self._migration_registry[migration_key]
                    migration = migration_class(
                        project_path=self.project_path,
                        file_manager=self.file_manager,
                        dry_run=True  # Always dry run for summary
                    )
                    
                    step_summary = {
                        "step": migration_key,
                        "description": migration.get_description(),
                        "affected_patterns": migration.get_affected_patterns()
                    }
                    summary["migration_steps"].append(step_summary)
            
            # Estimate number of files that will be processed
            rust_files = self.file_manager.find_rust_files()
            summary["estimated_files"] = len(rust_files)
            
        except Exception as e:
            self.logger.error(f"Failed to generate migration summary: {e}")
            summary["error"] = str(e)
        
        return summary