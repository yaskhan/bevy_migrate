"""
Version Detector - Utility for detecting current Bevy version in projects
Analyzes Cargo.toml and source code to determine the current Bevy version
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class VersionInfo:
    """Information about detected Bevy version"""
    version: str
    source: str  # Where the version was detected from
    confidence: float  # Confidence level (0.0 to 1.0)
    details: str  # Additional details about the detection


class VersionDetector:
    """
    Utility class for detecting the current Bevy version in a project
    """
    
    def __init__(self):
        """Initialize the version detector"""
        self.logger = logging.getLogger(__name__)
        
        # Version patterns for different sources
        self.cargo_patterns = [
            # Standard dependency format
            r'bevy\s*=\s*["\']([0-9]+\.[0-9]+(?:\.[0-9]+)?)["\']',
            # Table format with version
            r'bevy\s*=\s*\{\s*version\s*=\s*["\']([0-9]+\.[0-9]+(?:\.[0-9]+)?)["\']',
            # Git dependency with tag
            r'bevy\s*=\s*\{[^}]*tag\s*=\s*["\']v?([0-9]+\.[0-9]+(?:\.[0-9]+)?)["\']',
            # Git dependency with branch
            r'bevy\s*=\s*\{[^}]*branch\s*=\s*["\']release-([0-9]+\.[0-9]+)["\']',
        ]
        
        # Code patterns that indicate specific versions
        self.code_patterns = {
            "0.15": [
                r'\.add_plugin\(',
                r'\.add_system\(',
                r'\.add_startup_system\(',
                r'SystemSet',
                r'Commands::spawn\(\(',
            ],
            "0.16": [
                r'\.add_plugins\(',
                r'\.add_systems\(',
                r'DefaultPlugins',
                r'MinimalPlugins',
                r'Commands::spawn\([^(]',
            ],
            "0.17": [
                r'Camera2d(?!Bundle)',
                r'Camera3d(?!Bundle)',
                r'ButtonInput<',
                r'\.observe\(',
                r'Text::new\(',
            ],
            "0.18": [
                r'Window\s*\{',
                r'Cuboid::',
                r'TextFont',
                r'InheritedVisibility',
                r'Position::',
                r'Interaction::Pressed',
            ]
        }
        
        # Supported versions in order
        self.supported_versions = ["0.15", "0.16", "0.17", "0.18"]
        
        self.logger.info("Version detector initialized")
    
        self.logger.info("Version detector initialized")
    
    def _find_cargo_toml(self, path: Path) -> Optional[Path]:
        """Find Cargo.toml in path (case-insensitive)"""
        try:
            if not path.is_dir():
                return None
            
            # Check case-insensitive using iterdir to get actual filename
            for f in path.iterdir():
                if f.is_file() and f.name.lower() == "cargo.toml":
                    return f
            return None
        except Exception:
            return None

    def detect_version(self, project_path: Path) -> Optional[str]:
        """
        Detect the current Bevy version in a project
        
        Args:
            project_path: Path to the project root
            
        Returns:
            Detected version string or None if not detected
        """
        try:
            self.logger.info(f"Detecting Bevy version in project: {project_path}")
            
            # Collect version information from different sources
            version_candidates = []
            
            # 1. Check Cargo.toml
            cargo_version = self._detect_from_cargo_toml(project_path)
            if cargo_version:
                version_candidates.append(cargo_version)
            
            # 2. Check Cargo.lock
            lock_version = self._detect_from_cargo_lock(project_path)
            if lock_version:
                version_candidates.append(lock_version)
            
            # 3. Analyze source code patterns
            code_version = self._detect_from_source_code(project_path)
            if code_version:
                version_candidates.append(code_version)
            
            # 4. Check workspace Cargo.toml if exists
            workspace_version = self._detect_from_workspace(project_path)
            if workspace_version:
                version_candidates.append(workspace_version)
            
            # Select the best version candidate
            best_version = self._select_best_version(version_candidates)
            
            if best_version:
                self.logger.info(f"Detected Bevy version: {best_version.version} (from {best_version.source}, confidence: {best_version.confidence:.2f})")
                return best_version.version
            else:
                self.logger.warning("Could not detect Bevy version")
                return None
                
        except Exception as e:
            self.logger.error(f"Version detection failed: {e}", exc_info=True)
            return None
    
    def _detect_from_cargo_toml(self, project_path: Path) -> Optional[VersionInfo]:
        """Detect version from Cargo.toml"""
        try:
            cargo_toml_path = self._find_cargo_toml(project_path)
            if not cargo_toml_path:
                return None
            
            content = cargo_toml_path.read_text(encoding='utf-8')
            
            for pattern in self.cargo_patterns:
                match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                if match:
                    version = match.group(1)
                    # Normalize version (add .0 if needed)
                    if version.count('.') == 1:
                        version += ".0"
                    
                    # Convert to major.minor format for our purposes
                    version_parts = version.split('.')
                    normalized_version = f"{version_parts[0]}.{version_parts[1]}"
                    
                    self.logger.debug(f"Found version {normalized_version} in Cargo.toml")
                    return VersionInfo(
                        version=normalized_version,
                        source="Cargo.toml",
                        confidence=0.9,
                        details=f"Matched pattern: {pattern}"
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to read Cargo.toml: {e}")
            return None
    
    def _detect_from_cargo_lock(self, project_path: Path) -> Optional[VersionInfo]:
        """Detect version from Cargo.lock"""
        try:
            cargo_lock_path = project_path / "Cargo.lock"
            if not cargo_lock_path.exists():
                return None
            
            content = cargo_lock_path.read_text(encoding='utf-8')
            
            # Look for bevy entries in Cargo.lock
            pattern = r'\[\[package\]\]\s*name\s*=\s*["\']bevy["\'][\s\S]*?version\s*=\s*["\']([0-9]+\.[0-9]+(?:\.[0-9]+)?)["\']'
            match = re.search(pattern, content, re.MULTILINE)
            
            if match:
                version = match.group(1)
                # Convert to major.minor format
                version_parts = version.split('.')
                normalized_version = f"{version_parts[0]}.{version_parts[1]}"
                
                self.logger.debug(f"Found version {normalized_version} in Cargo.lock")
                return VersionInfo(
                    version=normalized_version,
                    source="Cargo.lock",
                    confidence=0.8,
                    details="Found in lock file"
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to read Cargo.lock: {e}")
            return None
    
    def _detect_from_source_code(self, project_path: Path) -> Optional[VersionInfo]:
        """Detect version from source code patterns"""
        try:
            # Find Rust files
            rust_files = []
            for pattern in ["src/**/*.rs", "examples/**/*.rs"]:
                rust_files.extend(project_path.glob(pattern))
            
            if not rust_files:
                return None
            
            # Analyze patterns in source files
            version_scores = {version: 0 for version in self.supported_versions}
            total_files_analyzed = 0
            
            for file_path in rust_files[:20]:  # Limit to first 20 files for performance
                try:
                    content = file_path.read_text(encoding='utf-8')
                    total_files_analyzed += 1
                    
                    # Check patterns for each version
                    for version, patterns in self.code_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, content):
                                version_scores[version] += 1
                                self.logger.debug(f"Found {version} pattern '{pattern}' in {file_path.name}")
                                
                except Exception as e:
                    self.logger.warning(f"Could not analyze file {file_path}: {e}")
                    continue
            
            if total_files_analyzed == 0:
                return None
            
            # Find the version with the highest score
            best_version = max(version_scores.items(), key=lambda x: x[1])
            
            if best_version[1] > 0:
                confidence = min(best_version[1] / (total_files_analyzed * 2), 1.0)  # Normalize confidence
                
                self.logger.debug(f"Code analysis scores: {version_scores}")
                return VersionInfo(
                    version=best_version[0],
                    source="source code analysis",
                    confidence=confidence,
                    details=f"Found {best_version[1]} patterns in {total_files_analyzed} files"
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Source code analysis failed: {e}")
            return None
    
    def _detect_from_workspace(self, project_path: Path) -> Optional[VersionInfo]:
        """Detect version from workspace Cargo.toml"""
        try:
            # Check if we're in a workspace
            current_path = project_path
            while current_path != current_path.parent:
                workspace_cargo = self._find_cargo_toml(current_path)
                if workspace_cargo:
                    content = workspace_cargo.read_text(encoding='utf-8')
                    if '[workspace]' in content:
                        # This is a workspace, check for bevy dependency
                        for pattern in self.cargo_patterns:
                            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                            if match:
                                version = match.group(1)
                                version_parts = version.split('.')
                                normalized_version = f"{version_parts[0]}.{version_parts[1]}"
                                
                                self.logger.debug(f"Found version {normalized_version} in workspace Cargo.toml")
                                return VersionInfo(
                                    version=normalized_version,
                                    source="workspace Cargo.toml",
                                    confidence=0.85,
                                    details="Found in workspace configuration"
                                )
                
                current_path = current_path.parent
            
            return None
            
        except Exception as e:
            self.logger.error(f"Workspace analysis failed: {e}")
            return None
    
    def _select_best_version(self, candidates: List[VersionInfo]) -> Optional[VersionInfo]:
        """Select the best version from candidates"""
        if not candidates:
            return None
        
        # Sort by confidence (highest first)
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        # Log all candidates
        self.logger.debug("Version candidates:")
        for candidate in candidates:
            self.logger.debug(f"  {candidate.version} from {candidate.source} (confidence: {candidate.confidence:.2f})")
        
        # If top candidate has high confidence, use it
        best_candidate = candidates[0]
        if best_candidate.confidence >= 0.8:
            return best_candidate
        
        # If multiple candidates agree, increase confidence
        version_counts = {}
        for candidate in candidates:
            version_counts[candidate.version] = version_counts.get(candidate.version, 0) + 1
        
        # Find most common version
        most_common_version = max(version_counts.items(), key=lambda x: x[1])
        
        if most_common_version[1] > 1:  # Multiple sources agree
            # Find the best candidate with this version
            for candidate in candidates:
                if candidate.version == most_common_version[0]:
                    # Boost confidence due to agreement
                    candidate.confidence = min(candidate.confidence + 0.2, 1.0)
                    return candidate
        
        return best_candidate
    
    def get_version_info(self, project_path: Path) -> Dict[str, any]:
        """
        Get detailed version information about a project
        
        Args:
            project_path: Path to the project root
            
        Returns:
            Dictionary with detailed version information
        """
        try:
            info = {
                "detected_version": None,
                "confidence": 0.0,
                "sources": {},
                "supported_versions": self.supported_versions,
                "analysis_details": {}
            }
            
            # Collect information from all sources
            cargo_version = self._detect_from_cargo_toml(project_path)
            if cargo_version:
                info["sources"]["cargo_toml"] = {
                    "version": cargo_version.version,
                    "confidence": cargo_version.confidence,
                    "details": cargo_version.details
                }
            
            lock_version = self._detect_from_cargo_lock(project_path)
            if lock_version:
                info["sources"]["cargo_lock"] = {
                    "version": lock_version.version,
                    "confidence": lock_version.confidence,
                    "details": lock_version.details
                }
            
            code_version = self._detect_from_source_code(project_path)
            if code_version:
                info["sources"]["source_code"] = {
                    "version": code_version.version,
                    "confidence": code_version.confidence,
                    "details": code_version.details
                }
            
            workspace_version = self._detect_from_workspace(project_path)
            if workspace_version:
                info["sources"]["workspace"] = {
                    "version": workspace_version.version,
                    "confidence": workspace_version.confidence,
                    "details": workspace_version.details
                }
            
            # Get the best version
            candidates = [v for v in [cargo_version, lock_version, code_version, workspace_version] if v]
            best_version = self._select_best_version(candidates)
            
            if best_version:
                info["detected_version"] = best_version.version
                info["confidence"] = best_version.confidence
                info["primary_source"] = best_version.source
            
            # Add analysis details
            info["analysis_details"] = {
                "total_sources_checked": 4,
                "sources_with_results": len([s for s in info["sources"].values() if s]),
                "cargo_toml_exists": self._find_cargo_toml(project_path) is not None,
                "cargo_lock_exists": (project_path / "Cargo.lock").exists(),
                "rust_files_found": len(list(project_path.glob("src/**/*.rs"))),
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get version info: {e}", exc_info=True)
            return {
                "detected_version": None,
                "confidence": 0.0,
                "sources": {},
                "error": str(e)
            }
    
    def is_version_supported(self, version: str) -> bool:
        """
        Check if a version is supported for migration
        
        Args:
            version: Version string to check
            
        Returns:
            True if version is supported, False otherwise
        """
        return version in self.supported_versions
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """
        Get the migration path between two versions
        
        Args:
            from_version: Starting version
            to_version: Target version
            
        Returns:
            List of versions in migration path
        """
        try:
            if from_version not in self.supported_versions:
                return []
            
            if to_version not in self.supported_versions:
                return []
            
            from_idx = self.supported_versions.index(from_version)
            to_idx = self.supported_versions.index(to_version)
            
            if from_idx >= to_idx:
                return []  # Cannot migrate backwards or to same version
            
            return self.supported_versions[from_idx:to_idx + 1]
            
        except ValueError:
            return []
    
    def validate_project_structure(self, project_path: Path) -> Dict[str, bool]:
        """
        Validate that the project has the expected structure for a Bevy project
        
        Args:
            project_path: Path to the project root
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation = {
                "is_rust_project": False,
                "has_cargo_toml": False,
                "has_src_directory": False,
                "has_main_rs": False,
                "has_lib_rs": False,
                "has_bevy_dependency": False,
                "is_workspace": False,
                "has_examples": False,
                "has_assets": False
            }
            
            # Check for Cargo.toml
            cargo_toml_path = self._find_cargo_toml(project_path)
            validation["has_cargo_toml"] = cargo_toml_path is not None
            
            if validation["has_cargo_toml"]:
                validation["is_rust_project"] = True
                
                # Check Cargo.toml content
                try:
                    content = cargo_toml_path.read_text(encoding='utf-8')
                    validation["has_bevy_dependency"] = 'bevy' in content.lower()
                    validation["is_workspace"] = '[workspace]' in content
                except Exception:
                    pass
            
            # Check for src directory and main files
            src_dir = project_path / "src"
            validation["has_src_directory"] = src_dir.exists() and src_dir.is_dir()
            validation["has_main_rs"] = (src_dir / "main.rs").exists()
            validation["has_lib_rs"] = (src_dir / "lib.rs").exists()
            
            # Check for examples and assets
            validation["has_examples"] = (project_path / "examples").exists()
            validation["has_assets"] = (project_path / "assets").exists()
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Project structure validation failed: {e}")
            return {"error": str(e)}
    
    def suggest_migration_strategy(self, project_path: Path) -> Dict[str, any]:
        """
        Suggest a migration strategy based on project analysis
        
        Args:
            project_path: Path to the project root
            
        Returns:
            Dictionary with migration suggestions
        """
        try:
            version_info = self.get_version_info(project_path)
            structure_info = self.validate_project_structure(project_path)
            
            suggestions = {
                "recommended_approach": "unknown",
                "estimated_complexity": "unknown",
                "backup_recommended": True,
                "manual_review_areas": [],
                "automated_migration_feasible": False,
                "warnings": [],
                "next_steps": []
            }
            
            current_version = version_info.get("detected_version")
            
            if not current_version:
                suggestions["warnings"].append("Could not detect current Bevy version")
                suggestions["next_steps"].append("Manually verify Bevy version in Cargo.toml")
                return suggestions
            
            if not structure_info.get("has_bevy_dependency", False):
                suggestions["warnings"].append("Bevy dependency not clearly identified")
                suggestions["manual_review_areas"].append("Verify Bevy usage in project")
            
            # Determine migration complexity
            if current_version == "0.15":
                suggestions["estimated_complexity"] = "high"
                suggestions["manual_review_areas"].extend([
                    "Plugin system changes",
                    "System registration updates",
                    "Entity spawning patterns"
                ])
            elif current_version == "0.16":
                suggestions["estimated_complexity"] = "medium"
                suggestions["manual_review_areas"].extend([
                    "Bundle system changes",
                    "Observer system updates",
                    "Input system changes"
                ])
            elif current_version == "0.17":
                suggestions["estimated_complexity"] = "medium"
                suggestions["manual_review_areas"].extend([
                    "Rendering system updates",
                    "UI system changes",
                    "Asset system improvements"
                ])
            else:
                suggestions["estimated_complexity"] = "low"
            
            # Determine if automated migration is feasible
            confidence = version_info.get("confidence", 0.0)
            if confidence >= 0.7 and structure_info.get("is_rust_project", False):
                suggestions["automated_migration_feasible"] = True
                suggestions["recommended_approach"] = "automated_with_review"
            else:
                suggestions["recommended_approach"] = "manual_with_guidance"
            
            # Add general next steps
            suggestions["next_steps"].extend([
                "Create backup of project",
                "Review migration documentation",
                "Test migration on a copy first"
            ])
            
            if suggestions["automated_migration_feasible"]:
                suggestions["next_steps"].append("Run automated migration tool")
            
            suggestions["next_steps"].extend([
                "Compile and test after migration",
                "Review and update any custom code"
            ])
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Migration strategy suggestion failed: {e}")
            return {"error": str(e)}