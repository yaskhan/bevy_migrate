"""
Base Migration - Abstract base class for all Bevy version migrations
Provides common functionality and interface for migration modules
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.file_manager import FileManager
from core.ast_processor import ASTProcessor, ASTTransformation


@dataclass
class MigrationResult:
    """Result of a migration operation"""
    success: bool
    files_processed: int
    files_modified: int
    transformations_applied: int
    errors: List[str]
    warnings: List[str]
    
    def add_error(self, error: str) -> None:
        """Add an error message to the result"""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message to the result"""
        self.warnings.append(warning)


class BaseMigration(ABC):
    """
    Abstract base class for all Bevy version migrations
    
    Each migration module should inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(
        self,
        project_path: Path,
        file_manager: FileManager,
        dry_run: bool = False
    ):
        """
        Initialize the base migration
        
        Args:
            project_path: Path to the Bevy project
            file_manager: File manager instance for file operations
            dry_run: If True, only show what would be changed
        """
        self.project_path = project_path
        self.file_manager = file_manager
        self.dry_run = dry_run
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize AST processor
        self.ast_processor = ASTProcessor(project_path, dry_run)
        
        # Migration metadata
        self._from_version: Optional[str] = None
        self._to_version: Optional[str] = None
        self._description: Optional[str] = None
        
        self.logger.info(f"Initialized migration: {self.__class__.__name__}")
        self.logger.info(f"Project path: {project_path}")
        self.logger.info(f"Dry run mode: {dry_run}")
    
    @property
    @abstractmethod
    def from_version(self) -> str:
        """Source Bevy version for this migration"""
        pass
    
    @property
    @abstractmethod
    def to_version(self) -> str:
        """Target Bevy version for this migration"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this migration"""
        pass
    
    @abstractmethod
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for this migration
        
        Returns:
            List of ASTTransformation objects
        """
        pass
    
    @abstractmethod
    def get_affected_patterns(self) -> List[str]:
        """
        Get list of file patterns that this migration affects
        
        Returns:
            List of glob patterns (e.g., ["**/*.rs", "Cargo.toml"])
        """
        pass
    
    def execute(self) -> bool:
        """
        Execute the migration
        
        Returns:
            True if migration was successful, False otherwise
        """
        try:
            self.logger.info(f"Starting migration from {self.from_version} to {self.to_version}")
            
            # Pre-migration validation
            if not self.validate_preconditions():
                self.logger.error("Pre-migration validation failed")
                return False
            
            # Get files to process
            files_to_process = self._get_files_to_process()
            if not files_to_process:
                self.logger.warning("No files found to process")
                return True  # Not an error, just nothing to do
            
            self.logger.info(f"Found {len(files_to_process)} files to process")
            
            # Execute pre-migration steps
            if not self.pre_migration_steps():
                self.logger.error("Pre-migration steps failed")
                return False
            
            # Apply transformations
            result = self._apply_transformations(files_to_process)
            
            # Execute post-migration steps
            if not self.post_migration_steps(result):
                self.logger.error("Post-migration steps failed")
                return False
            
            # Log results
            self._log_migration_results(result)
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"Migration failed with error: {e}", exc_info=True)
            return False
    
    def validate_preconditions(self) -> bool:
        """
        Validate that preconditions for this migration are met
        
        Returns:
            True if preconditions are met, False otherwise
        """
        try:
            # Check that project path exists
            if not self.project_path.exists():
                self.logger.error(f"Project path does not exist: {self.project_path}")
                return False
            
            # Check for Cargo.toml
            cargo_toml = self.file_manager.find_cargo_toml()
            if not cargo_toml:
                self.logger.error("Cargo.toml not found in project")
                return False
            
            # Check for src directory
            src_dir = self.project_path / "src"
            if not src_dir.exists():
                self.logger.error("src directory not found in project")
                return False
            
            # Validate transformations
            transformations = self.get_transformations()
            for transformation in transformations:
                if not self.ast_processor.validate_transformation(transformation):
                    self.logger.error(f"Invalid transformation: {transformation.description}")
                    return False
            
            self.logger.debug("Pre-migration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration validation failed: {e}", exc_info=True)
            return False
    
    def pre_migration_steps(self) -> bool:
        """
        Execute steps before applying transformations
        
        Override this method in subclasses to add custom pre-migration logic
        
        Returns:
            True if pre-migration steps were successful, False otherwise
        """
        self.logger.debug("Executing pre-migration steps")
        return True
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        """
        Execute steps after applying transformations
        
        Override this method in subclasses to add custom post-migration logic
        
        Args:
            result: The migration result from transformation application
            
        Returns:
            True if post-migration steps were successful, False otherwise
        """
        self.logger.debug("Executing post-migration steps")
        return True
    
    def _get_files_to_process(self) -> List[Path]:
        """Get list of files that should be processed by this migration"""
        all_files = []
        
        try:
            patterns = self.get_affected_patterns()
            
            for pattern in patterns:
                matching_files = self.file_manager.find_files_by_pattern(pattern)
                all_files.extend(matching_files)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_files = []
            for file_path in all_files:
                if file_path not in seen:
                    seen.add(file_path)
                    unique_files.append(file_path)
            
            return unique_files
            
        except Exception as e:
            self.logger.error(f"Failed to get files to process: {e}", exc_info=True)
            return []
    
    def _apply_transformations(self, files_to_process: List[Path]) -> MigrationResult:
        """Apply AST transformations to the files"""
        result = MigrationResult(
            success=True,
            files_processed=0,
            files_modified=0,
            transformations_applied=0,
            errors=[],
            warnings=[]
        )
        
        try:
            transformations = self.get_transformations()
            if not transformations:
                self.logger.warning("No transformations defined for this migration")
                return result
            
            # Apply transformations using AST processor
            transformation_results = self.ast_processor.apply_transformations(
                files_to_process,
                transformations
            )
            
            # Process results
            for transform_result in transformation_results:
                result.files_processed += 1
                
                if not transform_result.success:
                    result.success = False
                    error_msg = f"Failed to process {transform_result.file_path}"
                    if transform_result.error_message:
                        error_msg += f": {transform_result.error_message}"
                    result.add_error(error_msg)
                    continue
                
                # Check if file was modified
                if transform_result.original_content != transform_result.transformed_content:
                    result.files_modified += 1
                    self.logger.info(f"Modified file: {transform_result.file_path}")
                
                # Count applied transformations
                result.transformations_applied += len(transform_result.applied_transformations)
                
                # Log applied transformations
                for transformation_desc in transform_result.applied_transformations:
                    self.logger.debug(f"Applied '{transformation_desc}' to {transform_result.file_path}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to apply transformations: {e}", exc_info=True)
            result.success = False
            result.add_error(f"Transformation application failed: {e}")
            return result
    
    def _log_migration_results(self, result: MigrationResult) -> None:
        """Log the results of the migration"""
        if result.success:
            self.logger.info(f"Migration completed successfully!")
            self.logger.info(f"Files processed: {result.files_processed}")
            self.logger.info(f"Files modified: {result.files_modified}")
            self.logger.info(f"Transformations applied: {result.transformations_applied}")
        else:
            self.logger.error(f"Migration failed!")
            self.logger.error(f"Files processed: {result.files_processed}")
            self.logger.error(f"Files modified: {result.files_modified}")
            self.logger.error(f"Errors: {len(result.errors)}")
        
        # Log warnings
        for warning in result.warnings:
            self.logger.warning(warning)
        
        # Log errors
        for error in result.errors:
            self.logger.error(error)
    
    def get_description(self) -> str:
        """Get the migration description (wrapper for property)"""
        return self.description
    
    def create_transformation(
        self,
        pattern: str,
        replacement: str,
        description: str,
        file_patterns: Optional[List[str]] = None,
        callback: Optional[Callable[[Dict[str, str], Path], str]] = None
    ) -> ASTTransformation:
        """
        Helper method to create AST transformations
        
        Args:
            pattern: ast-grep pattern to match
            replacement: Replacement pattern
            description: Human-readable description
            file_patterns: File patterns to apply to (defaults to *.rs)
            callback: Optional Python callback to handle complex logic
            
        Returns:
            ASTTransformation object
        """
        return self.ast_processor.create_bevy_transformation(
            pattern=pattern,
            replacement=replacement,
            description=description,
            file_patterns=file_patterns,
            callback=callback
        )
    
    def find_files_with_pattern(self, search_pattern: str) -> List[Path]:
        """
        Find files containing a specific pattern
        
        Args:
            search_pattern: Text pattern to search for
            
        Returns:
            List of file paths containing the pattern
        """
        return self.file_manager.find_files_containing_pattern(
            pattern=search_pattern,
            file_types=['.rs']
        )
    
    def backup_files(self, file_paths: List[Path]) -> bool:
        """
        Create backups of specified files
        
        Args:
            file_paths: List of file paths to backup
            
        Returns:
            True if all backups were successful, False otherwise
        """
        if self.dry_run:
            self.logger.info(f"Would backup {len(file_paths)} files (dry run)")
            return True
        
        backup_dir = self.project_path / "migration_backup" / f"{self.from_version}_to_{self.to_version}"
        success_count = 0
        
        for file_path in file_paths:
            if self.file_manager.backup_file(file_path, backup_dir):
                success_count += 1
            else:
                self.logger.warning(f"Failed to backup file: {file_path}")
        
        self.logger.info(f"Backed up {success_count}/{len(file_paths)} files")
        return success_count == len(file_paths)
    
    def get_migration_info(self) -> Dict[str, Any]:
        """
        Get information about this migration
        
        Returns:
            Dictionary with migration information
        """
        return {
            "class_name": self.__class__.__name__,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "description": self.description,
            "affected_patterns": self.get_affected_patterns(),
            "transformation_count": len(self.get_transformations()),
            "dry_run": self.dry_run
        }
    
    def preview_changes(self, max_files: int = 5) -> Dict[str, Any]:
        """
        Preview what changes this migration would make
        
        Args:
            max_files: Maximum number of files to preview
            
        Returns:
            Dictionary with preview information
        """
        try:
            files_to_process = self._get_files_to_process()[:max_files]
            transformations = self.get_transformations()
            
            previews = []
            for file_path in files_to_process:
                content = self.file_manager.read_file_content(file_path)
                if content is None:
                    continue
                
                file_previews = []
                for transformation in transformations:
                    if self.ast_processor._should_apply_transformation(file_path, transformation):
                        preview = self.ast_processor.get_transformation_preview(content, transformation)
                        if preview.get("has_changes", False):
                            file_previews.append(preview)
                
                if file_previews:
                    previews.append({
                        "file_path": str(file_path.relative_to(self.project_path)),
                        "transformations": file_previews
                    })
            
            return {
                "migration_info": self.get_migration_info(),
                "total_files_to_process": len(self._get_files_to_process()),
                "previewed_files": len(previews),
                "file_previews": previews
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate preview: {e}", exc_info=True)
            return {
                "error": str(e),
                "migration_info": self.get_migration_info()
            }
    
    def validate_migration_result(self, result: MigrationResult) -> bool:
        """
        Validate that the migration result is acceptable
        
        Override this method in subclasses to add custom validation logic
        
        Args:
            result: The migration result to validate
            
        Returns:
            True if result is valid, False otherwise
        """
        # Basic validation - check that we didn't have too many errors
        error_rate = len(result.errors) / max(result.files_processed, 1)
        if error_rate > 0.1:  # More than 10% error rate
            self.logger.warning(f"High error rate in migration: {error_rate:.2%}")
            return False
        
        return result.success
    
    def __str__(self) -> str:
        """String representation of the migration"""
        return f"{self.__class__.__name__}: {self.from_version} -> {self.to_version}"
    
    def __repr__(self) -> str:
        """Detailed string representation of the migration"""
        return (
            f"{self.__class__.__name__}("
            f"from_version='{self.from_version}', "
            f"to_version='{self.to_version}', "
            f"dry_run={self.dry_run})"
        )