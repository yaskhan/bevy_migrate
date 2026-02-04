"""
File Manager - Core component for handling file operations during migrations
Manages file discovery, filtering, and basic file operations for Bevy projects
"""

import logging
import fnmatch
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Information about a file in the project"""
    path: Path
    relative_path: Path
    size: int
    is_rust_file: bool
    is_cargo_file: bool
    is_config_file: bool
    
    @classmethod
    def from_path(cls, file_path: Path, project_root: Path) -> 'FileInfo':
        """Create FileInfo from a file path"""
        relative_path = file_path.relative_to(project_root)
        size = file_path.stat().st_size if file_path.exists() else 0
        
        return cls(
            path=file_path,
            relative_path=relative_path,
            size=size,
            is_rust_file=file_path.suffix == '.rs',
            is_cargo_file=file_path.name in ['Cargo.toml', 'Cargo.lock'],
            is_config_file=file_path.suffix in ['.toml', '.yaml', '.yml', '.json']
        )


class FileManager:
    """
    File manager for handling file operations during Bevy migrations
    """
    
    def __init__(self, project_path: Path, exclude_patterns: Optional[List[str]] = None):
        """
        Initialize the file manager
        
        Args:
            project_path: Path to the project root
            exclude_patterns: List of patterns to exclude from operations
        """
        self.project_path = project_path
        self.exclude_patterns = exclude_patterns or []
        self.logger = logging.getLogger(__name__)
        
        # Default exclude patterns for Rust/Bevy projects
        self.default_excludes = [
            'target/**',
            '.git/**',
            '.gitignore',
            '*.lock',
            '**/.DS_Store',
            '**/Thumbs.db',
            '.vscode/**',
            '.idea/**',
            '*.tmp',
            '*.bak',
            'migration_backup/**'
        ]
        
        # Combine user patterns with defaults
        self.all_exclude_patterns = self.default_excludes + self.exclude_patterns
        
        self.logger.info(f"File manager initialized for project: {project_path}")
        self.logger.debug(f"Exclude patterns: {self.all_exclude_patterns}")
    
    def find_rust_files(self) -> List[Path]:
        """
        Find all Rust source files in the project
        
        Returns:
            List of paths to Rust files
        """
        rust_files = []
        
        try:
            # Search for .rs files recursively
            for rust_file in self.project_path.rglob("*.rs"):
                if self._should_include_file(rust_file):
                    rust_files.append(rust_file)
            
            self.logger.info(f"Found {len(rust_files)} Rust files")
            return sorted(rust_files)
            
        except Exception as e:
            self.logger.error(f"Error finding Rust files: {e}", exc_info=True)
            return []
    
    def find_cargo_files(self) -> List[Path]:
        """
        Find all Cargo-related files in the project
        
        Returns:
            List of paths to Cargo files
        """
        cargo_files = []
        
        try:
            # Look for Cargo.toml files
            for cargo_file in self.project_path.rglob("Cargo.toml"):
                if self._should_include_file(cargo_file):
                    cargo_files.append(cargo_file)
            
            # Look for Cargo.lock files
            for lock_file in self.project_path.rglob("Cargo.lock"):
                if self._should_include_file(lock_file):
                    cargo_files.append(lock_file)
            
            self.logger.info(f"Found {len(cargo_files)} Cargo files")
            return sorted(cargo_files)
            
        except Exception as e:
            self.logger.error(f"Error finding Cargo files: {e}", exc_info=True)
            return []
    
    def find_cargo_toml(self) -> Optional[Path]:
        """
        Find Cargo.toml in the project root (case-insensitive)
        
        Returns:
            Path to Cargo.toml or None if not found
        """
        try:
            # Check case-insensitive using iterdir to get actual filename
            if self.project_path.exists():
                for file_path in self.project_path.iterdir():
                    if file_path.is_file() and file_path.name.lower() == "cargo.toml":
                        self.logger.debug(f"Found Cargo.toml: {file_path.name}")
                        return file_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding Cargo.toml: {e}")
            return None

    def find_config_files(self) -> List[Path]:
        """
        Find configuration files that might need migration
        
        Returns:
            List of paths to configuration files
        """
        config_files = []
        config_extensions = ['.toml', '.yaml', '.yml', '.json']
        
        try:
            for ext in config_extensions:
                for config_file in self.project_path.rglob(f"*{ext}"):
                    if self._should_include_file(config_file):
                        config_files.append(config_file)
            
            self.logger.info(f"Found {len(config_files)} configuration files")
            return sorted(config_files)
            
        except Exception as e:
            self.logger.error(f"Error finding configuration files: {e}", exc_info=True)
            return []
    
    def find_files_by_pattern(self, pattern: str) -> List[Path]:
        """
        Find files matching a specific pattern
        
        Args:
            pattern: Glob pattern to match files
            
        Returns:
            List of matching file paths
        """
        matching_files = []
        
        try:
            for file_path in self.project_path.rglob(pattern):
                if file_path.is_file() and self._should_include_file(file_path):
                    matching_files.append(file_path)
            
            self.logger.debug(f"Found {len(matching_files)} files matching pattern '{pattern}'")
            return sorted(matching_files)
            
        except Exception as e:
            self.logger.error(f"Error finding files with pattern '{pattern}': {e}", exc_info=True)
            return []
    
    def get_file_info(self, file_path: Path) -> Optional[FileInfo]:
        """
        Get detailed information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileInfo object or None if file doesn't exist
        """
        try:
            if not file_path.exists():
                return None
            
            return FileInfo.from_path(file_path, self.project_path)
            
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {e}", exc_info=True)
            return None
    
    def get_project_files(self) -> List[FileInfo]:
        """
        Get information about all relevant files in the project
        
        Returns:
            List of FileInfo objects
        """
        all_files = []
        
        try:
            # Get all files recursively
            for file_path in self.project_path.rglob("*"):
                if file_path.is_file() and self._should_include_file(file_path):
                    file_info = self.get_file_info(file_path)
                    if file_info:
                        all_files.append(file_info)
            
            self.logger.info(f"Found {len(all_files)} project files")
            return sorted(all_files, key=lambda f: f.relative_path)
            
        except Exception as e:
            self.logger.error(f"Error getting project files: {e}", exc_info=True)
            return []
    
    def _should_include_file(self, file_path: Path) -> bool:
        """
        Check if a file should be included based on exclude patterns
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file should be included, False otherwise
        """
        try:
            # Get relative path for pattern matching
            relative_path = file_path.relative_to(self.project_path)
            relative_str = str(relative_path).replace('\\', '/')  # Normalize path separators
            
            # Check against exclude patterns
            for pattern in self.all_exclude_patterns:
                # Handle different pattern types
                if fnmatch.fnmatch(relative_str, pattern):
                    self.logger.debug(f"Excluding file {relative_str} (matches pattern: {pattern})")
                    return False
                
                # Also check the filename alone
                if fnmatch.fnmatch(file_path.name, pattern):
                    self.logger.debug(f"Excluding file {relative_str} (filename matches pattern: {pattern})")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error checking file inclusion for {file_path}: {e}")
            return False
    
    def backup_file(self, file_path: Path, backup_dir: Path) -> Optional[Path]:
        """
        Create a backup of a file
        
        Args:
            file_path: Path to the file to backup
            backup_dir: Directory to store the backup
            
        Returns:
            Path to the backup file or None if backup failed
        """
        try:
            if not file_path.exists():
                self.logger.warning(f"Cannot backup non-existent file: {file_path}")
                return None
            
            # Create backup directory structure
            relative_path = file_path.relative_to(self.project_path)
            backup_file_path = backup_dir / relative_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            import shutil
            shutil.copy2(file_path, backup_file_path)
            
            self.logger.debug(f"Backed up file: {file_path} -> {backup_file_path}")
            return backup_file_path
            
        except Exception as e:
            self.logger.error(f"Failed to backup file {file_path}: {e}", exc_info=True)
            return None
    
    def restore_file(self, backup_path: Path, original_path: Path) -> bool:
        """
        Restore a file from backup
        
        Args:
            backup_path: Path to the backup file
            original_path: Path where the file should be restored
            
        Returns:
            True if restore was successful, False otherwise
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file does not exist: {backup_path}")
                return False
            
            # Create parent directory if needed
            original_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the backup back
            import shutil
            shutil.copy2(backup_path, original_path)
            
            self.logger.info(f"Restored file: {backup_path} -> {original_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore file from {backup_path}: {e}", exc_info=True)
            return False
    
    def read_file_content(self, file_path: Path) -> Optional[str]:
        """
        Read the content of a file
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File content as string or None if read failed
        """
        try:
            if not file_path.exists():
                self.logger.warning(f"Cannot read non-existent file: {file_path}")
                return None
            
            content = file_path.read_text(encoding='utf-8')
            self.logger.debug(f"Read file content: {file_path} ({len(content)} characters)")
            return content
            
        except UnicodeDecodeError:
            self.logger.warning(f"File {file_path} is not valid UTF-8, skipping")
            return None
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}", exc_info=True)
            return None
    
    def write_file_content(self, file_path: Path, content: str, create_backup: bool = True) -> bool:
        """
        Write content to a file
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            create_backup: Whether to create a backup before writing
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            # Create backup if requested and file exists
            if create_backup and file_path.exists():
                backup_dir = self.project_path / "migration_backup" / "auto_backup"
                self.backup_file(file_path, backup_dir)
            
            # Create parent directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content
            file_path.write_text(content, encoding='utf-8')
            
            self.logger.debug(f"Wrote file content: {file_path} ({len(content)} characters)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}", exc_info=True)
            return False
    
    def get_file_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about files in the project
        
        Returns:
            Dictionary with file statistics
        """
        try:
            rust_files = self.find_rust_files()
            cargo_files = self.find_cargo_files()
            config_files = self.find_config_files()
            all_files = self.get_project_files()
            
            total_size = sum(f.size for f in all_files)
            rust_size = sum(f.size for f in all_files if f.is_rust_file)
            
            return {
                "total_files": len(all_files),
                "rust_files": len(rust_files),
                "cargo_files": len(cargo_files),
                "config_files": len(config_files),
                "total_size_bytes": total_size,
                "rust_size_bytes": rust_size,
                "average_file_size": total_size / len(all_files) if all_files else 0,
                "largest_file": max(all_files, key=lambda f: f.size) if all_files else None,
                "exclude_patterns": self.all_exclude_patterns
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get file statistics: {e}", exc_info=True)
            return {}
    
    def validate_file_access(self, file_paths: List[Path]) -> Dict[Path, bool]:
        """
        Validate that files can be read and written
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dictionary mapping file paths to access status
        """
        access_status = {}
        
        for file_path in file_paths:
            try:
                # Check if file exists and is readable
                if not file_path.exists():
                    access_status[file_path] = False
                    continue
                
                # Try to read the file
                content = self.read_file_content(file_path)
                if content is None:
                    access_status[file_path] = False
                    continue
                
                # Check if file is writable (try to open in append mode)
                with open(file_path, 'a', encoding='utf-8'):
                    pass
                
                access_status[file_path] = True
                
            except Exception as e:
                self.logger.warning(f"File access validation failed for {file_path}: {e}")
                access_status[file_path] = False
        
        return access_status
    
    def find_files_containing_pattern(self, pattern: str, file_types: Optional[List[str]] = None) -> List[Path]:
        """
        Find files containing a specific text pattern
        
        Args:
            pattern: Text pattern to search for
            file_types: List of file extensions to search in (e.g., ['.rs', '.toml'])
            
        Returns:
            List of file paths containing the pattern
        """
        matching_files = []
        
        try:
            # Default to Rust files if no types specified
            if file_types is None:
                file_types = ['.rs']
            
            # Find all files of specified types
            for file_type in file_types:
                for file_path in self.project_path.rglob(f"*{file_type}"):
                    if not self._should_include_file(file_path):
                        continue
                    
                    content = self.read_file_content(file_path)
                    if content and pattern in content:
                        matching_files.append(file_path)
            
            self.logger.info(f"Found {len(matching_files)} files containing pattern '{pattern}'")
            return sorted(matching_files)
            
        except Exception as e:
            self.logger.error(f"Error searching for pattern '{pattern}': {e}", exc_info=True)
            return []
    
    def get_directory_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """
        Get a representation of the project directory structure
        
        Args:
            max_depth: Maximum depth to traverse
            
        Returns:
            Dictionary representing the directory structure
        """
        def build_tree(path: Path, current_depth: int) -> Dict[str, Any]:
            if current_depth > max_depth:
                return {"type": "directory", "truncated": True}
            
            if path.is_file():
                file_info = self.get_file_info(path)
                return {
                    "type": "file",
                    "size": file_info.size if file_info else 0,
                    "is_rust": path.suffix == '.rs',
                    "is_cargo": path.name in ['Cargo.toml', 'Cargo.lock']
                }
            
            children = {}
            try:
                for child in sorted(path.iterdir()):
                    if self._should_include_file(child):
                        children[child.name] = build_tree(child, current_depth + 1)
            except PermissionError:
                return {"type": "directory", "error": "Permission denied"}
            
            return {
                "type": "directory",
                "children": children,
                "child_count": len(children)
            }
        
        try:
            return build_tree(self.project_path, 0)
        except Exception as e:
            self.logger.error(f"Failed to build directory structure: {e}", exc_info=True)
            return {"type": "directory", "error": str(e)}