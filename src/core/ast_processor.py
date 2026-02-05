"""
AST Processor - Core component for parsing and transforming Rust AST
Handles AST-based code transformations for Bevy migrations using ast-grep
"""


import logging
import subprocess
import json
import tempfile
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable

from dataclasses import dataclass


@dataclass
class ASTTransformation:
    """Represents a single AST transformation rule"""
    file_patterns: List[str] = None
    # New fields for complex logic
    callback: Optional[Callable[[Dict[str, str], Path], str]] = None
    rule_yaml: Optional[str] = None
    
    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.rs"]


@dataclass
class TransformationResult:
    """Result of applying AST transformations"""
    file_path: Path
    original_content: str
    transformed_content: str
    applied_transformations: List[str]
    success: bool
    error_message: Optional[str] = None


class ASTProcessor:
    """
    AST processor that uses ast-grep for Rust code transformations
    """
    
    def __init__(self, project_path: Path, dry_run: bool = False):
        """
        Initialize the AST processor
        
        Args:
            project_path: Path to the project root
            dry_run: If True, don't modify files, just return what would be changed
        """
        self.project_path = project_path
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Check if ast-grep is available
        self.ast_grep_available = self._check_ast_grep_availability()
        
        self.logger.info(f"AST processor initialized for project: {project_path}")
        self.logger.info(f"Dry run mode: {dry_run}")
    
    def _check_ast_grep_availability(self) -> bool:
        """Check if ast-grep is available in the system"""
        try:
            result = subprocess.run(
                ["ast-grep", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.logger.info(f"ast-grep available: {result.stdout.strip()}")
                return True
            else:
                self.logger.warning("ast-grep not found, falling back to regex-based transformations")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.logger.warning("ast-grep not found, falling back to regex-based transformations")
            return False
    
    def apply_transformations(
        self,
        file_paths: List[Path],
        transformations: List[ASTTransformation]
    ) -> List[TransformationResult]:
        """
        Apply AST transformations to a list of files
        
        Args:
            file_paths: List of file paths to transform
            transformations: List of transformation rules to apply
            
        Returns:
            List of transformation results
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = self._process_file(file_path, transformations)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process file {file_path}: {e}", exc_info=True)
                results.append(TransformationResult(
                    file_path=file_path,
                    original_content="",
                    transformed_content="",
                    applied_transformations=[],
                    success=False,
                    error_message=str(e)
                ))
        
        return results
    
    def _process_file(
        self,
        file_path: Path,
        transformations: List[ASTTransformation]
    ) -> TransformationResult:
        """Process a single file with the given transformations"""
        try:
            # Read original content
            original_content = file_path.read_text(encoding='utf-8')
            transformed_content = original_content
            applied_transformations = []
            
            # Apply each transformation
            for transformation in transformations:
                if self._should_apply_transformation(file_path, transformation):
                    new_content = self._apply_single_transformation(
                        transformed_content,
                        transformation,
                        file_path
                    )
                    
                    if new_content != transformed_content:
                        transformed_content = new_content
                        applied_transformations.append(transformation.description)
                        self.logger.debug(f"Applied transformation '{transformation.description}' to {file_path}")
            
            # Write transformed content if not in dry run mode
            if not self.dry_run and transformed_content != original_content:
                file_path.write_text(transformed_content, encoding='utf-8')
                self.logger.info(f"Updated file: {file_path}")
            
            return TransformationResult(
                file_path=file_path,
                original_content=original_content,
                transformed_content=transformed_content,
                applied_transformations=applied_transformations,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
            return TransformationResult(
                file_path=file_path,
                original_content="",
                transformed_content="",
                applied_transformations=[],
                success=False,
                error_message=str(e)
            )
    
    def _should_apply_transformation(
        self,
        file_path: Path,
        transformation: ASTTransformation
    ) -> bool:
        """Check if a transformation should be applied to a file"""
        import fnmatch
        
        file_name = file_path.name
        relative_path = str(file_path.relative_to(self.project_path))
        
        for pattern in transformation.file_patterns:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(relative_path, pattern):
                return True
        
        return False
    
    def _apply_single_transformation(
        self,
        content: str,
        transformation: ASTTransformation,
        file_path: Path
    ) -> Optional[str]:
        """Apply a single transformation to content"""
        try:
            # Try ast-grep first if available
            if self.ast_grep_available:
                result = self._apply_ast_grep_transformation(content, transformation, file_path)
                if result is not None:
                    return result
                # Fallback to regex if ast-grep failed
            
            # Fallback to regex-based transformation
            return self._apply_regex_transformation(content, transformation)
        except Exception as e:
            self.logger.warning(f"AST transformation failed, falling back to regex: {e}")
            return self._apply_regex_transformation(content, transformation)
    
    def _apply_ast_grep_transformation(
        self,
        content: str,
        transformation: ASTTransformation,
        file_path: Path
    ) -> Optional[str]:
        """Apply transformation using ast-grep"""
        try:
            # Create temporary files for ast-grep
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # If there's a callback, we need to find matches first
                if transformation.callback:
                    # Determine the rule to use: either direct YAML or pattern-based
                    if transformation.rule_yaml:
                        inline_rule = transformation.rule_yaml
                    else:
                        rule_obj = {
                            "id": "callback-query",
                            "language": "rust",
                            "rule": {
                                "pattern": transformation.pattern
                            }
                        }
                        inline_rule = yaml.dump(rule_obj)
                    
                    cmd = [
                        "ast-grep",
                        "scan",
                        "--inline-rules", inline_rule,
                        "--json",
                        temp_file_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        matches = json.loads(result.stdout)
                        if not matches:
                            return content
                        
                        # Apply replacements using byte offsets
                        content_bytes = content.encode('utf-8')
                        matches.sort(key=lambda x: x['range']['byteOffset']['start'], reverse=True)
                        
                        new_content_bytes = content_bytes
                        for match in matches:
                            meta_vars = {}
                            if 'metaVariables' in match:
                                mvars = match['metaVariables']
                                if 'single' in mvars:
                                    for var_name, var_data in mvars['single'].items():
                                        meta_vars[var_name] = var_data['text']
                            
                            replacement = transformation.callback(meta_vars, file_path)
                            replacement_bytes = replacement.encode('utf-8')
                            
                            start_byte = match['range']['byteOffset']['start']
                            end_byte = match['range']['byteOffset']['end']
                            new_content_bytes = new_content_bytes[:start_byte] + replacement_bytes + new_content_bytes[end_byte:]
                        
                        return new_content_bytes.decode('utf-8')
                    else:
                        self.logger.debug(f"ast-grep scan failed: {result.stderr}")
                        return None

                # Standard replacement if no callback
                if transformation.rule_yaml:
                    inline_rule = transformation.rule_yaml
                else:
                    rule_obj = {
                        "id": "migration-rule",
                        "language": "rust",
                        "rule": {
                            "pattern": transformation.pattern
                        },
                        "fix": transformation.replacement
                    }
                    inline_rule = yaml.dump(rule_obj)
                
                # Run ast-grep with inline rules
                result = subprocess.run([
                    "ast-grep",
                    "scan",
                    "--inline-rules", inline_rule,
                    "--update-all",
                    temp_file_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Read the transformed content
                    transformed_content = Path(temp_file_path).read_text(encoding='utf-8')
                    return transformed_content
                else:
                    self.logger.debug(f"ast-grep failed: {result.stderr}")
                    return None
                    
            finally:
                # Clean up temp file
                Path(temp_file_path).unlink(missing_ok=True)
                
        except Exception as e:
            self.logger.debug(f"ast-grep transformation failed: {e}")
            return None
    
    def _apply_regex_transformation(
        self,
        content: str,
        transformation: ASTTransformation
    ) -> str:
        """Apply transformation using regex as fallback"""
        import re
        
        try:
            # Convert ast-grep pattern to regex (simplified approach)
            pattern = self._convert_ast_pattern_to_regex(transformation.pattern)
            replacement = transformation.replacement
            
            # Apply regex substitution
            transformed_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            return transformed_content
            
        except Exception as e:
            self.logger.warning(f"Regex transformation failed: {e}")
            return content
    
    def _convert_ast_pattern_to_regex(self, ast_pattern: str) -> str:
        """
        Convert ast-grep pattern to regex pattern (simplified)
        This is a basic conversion for common patterns
        """
        # This is a simplified conversion - in practice, you'd need more sophisticated parsing
        pattern = ast_pattern
        
        # Replace common ast-grep metavariables with regex groups
        pattern = pattern.replace("$_", r"(\w+)")
        pattern = pattern.replace("$$$", r"(.*?)")
        
        # Escape special regex characters that might be in Rust code
        pattern = re.escape(pattern)
        
        # Restore the regex groups we want
        pattern = pattern.replace(r"\(\\\w\+\)", r"(\w+)")
        pattern = pattern.replace(r"\(\.\*\?\)", r"(.*?)")
        
        return pattern
    
    def create_bevy_transformation(
        self,
        pattern: str,
        replacement: str,
        description: str,
        file_patterns: Optional[List[str]] = None,
        callback: Optional[Callable[[Dict[str, str], Path], str]] = None
    ) -> ASTTransformation:
        """
        Create a Bevy-specific AST transformation
        
        Args:
            pattern: ast-grep pattern to match
            replacement: Replacement pattern
            description: Human-readable description
            file_patterns: File patterns to apply to (defaults to *.rs)
            callback: Optional Python callback to handle complex logic
            
        Returns:
            ASTTransformation object
        """
        if file_patterns is None:
            file_patterns = ["*.rs"]
        
        return ASTTransformation(
            pattern=pattern,
            replacement=replacement,
            description=description,
            file_patterns=file_patterns,
            callback=callback
        )
    
    def validate_transformation(self, transformation: ASTTransformation) -> bool:
        """
        Validate that a transformation is syntactically correct
        
        Args:
            transformation: The transformation to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - check that pattern and replacement are not empty
            if not transformation.pattern.strip():
                self.logger.error("Transformation pattern cannot be empty")
                return False
            
            if not transformation.replacement.strip():
                self.logger.error("Transformation replacement cannot be empty")
                return False
            
            # Try to compile the pattern as regex (fallback validation)
            try:
                regex_pattern = self._convert_ast_pattern_to_regex(transformation.pattern)
                re.compile(regex_pattern)
            except re.error as e:
                self.logger.warning(f"Pattern may not be valid regex: {e}")
                # Don't fail validation for this, as it might be valid ast-grep syntax
            
            return True
            
        except Exception as e:
            self.logger.error(f"Transformation validation failed: {e}")
            return False
    
    def get_transformation_preview(
        self,
        content: str,
        transformation: ASTTransformation
    ) -> Dict[str, Any]:
        """
        Get a preview of what a transformation would do to content
        
        Args:
            content: The content to transform
            transformation: The transformation to apply
            
        Returns:
            Dictionary with preview information
        """
        try:
            # Apply transformation in preview mode
            transformed_content = self._apply_single_transformation(
                content,
                transformation,
                Path("preview.rs")  # Dummy path for preview
            )
            
            # Calculate diff information
            original_lines = content.splitlines()
            transformed_lines = transformed_content.splitlines()
            
            import difflib
            diff = list(difflib.unified_diff(
                original_lines,
                transformed_lines,
                fromfile="original",
                tofile="transformed",
                lineterm=""
            ))
            
            return {
                "original_content": content,
                "transformed_content": transformed_content,
                "has_changes": content != transformed_content,
                "diff": diff,
                "transformation_description": transformation.description
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate transformation preview: {e}")
            return {
                "original_content": content,
                "transformed_content": content,
                "has_changes": False,
                "diff": [],
                "error": str(e),
                "transformation_description": transformation.description
            }
    
    def batch_transform_files(
        self,
        transformations: List[ASTTransformation],
        file_patterns: Optional[List[str]] = None
    ) -> List[TransformationResult]:
        """
        Apply transformations to all matching files in the project
        
        Args:
            transformations: List of transformations to apply
            file_patterns: File patterns to match (defaults to ["**/*.rs"])
            
        Returns:
            List of transformation results
        """
        if file_patterns is None:
            file_patterns = ["**/*.rs"]
        
        # Find all matching files
        matching_files = []
        for pattern in file_patterns:
            matching_files.extend(self.project_path.glob(pattern))
        
        # Remove duplicates and filter out non-files
        unique_files = list(set(f for f in matching_files if f.is_file()))
        
        self.logger.info(f"Found {len(unique_files)} files to process")
        
        # Apply transformations
        return self.apply_transformations(unique_files, transformations)
    
    def get_statistics(self, results: List[TransformationResult]) -> Dict[str, Any]:
        """
        Get statistics about transformation results
        
        Args:
            results: List of transformation results
            
        Returns:
            Dictionary with statistics
        """
        total_files = len(results)
        successful_files = sum(1 for r in results if r.success)
        failed_files = total_files - successful_files
        modified_files = sum(1 for r in results if r.success and r.original_content != r.transformed_content)
        
        # Count transformations applied
        all_transformations = []
        for result in results:
            all_transformations.extend(result.applied_transformations)
        
        transformation_counts = {}
        for transformation in all_transformations:
            transformation_counts[transformation] = transformation_counts.get(transformation, 0) + 1
        
        return {
            "total_files": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "modified_files": modified_files,
            "transformation_counts": transformation_counts,
            "success_rate": successful_files / total_files if total_files > 0 else 0.0
        }