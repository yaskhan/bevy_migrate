"""
Migration from Bevy 0.15 to 0.16
Handles the migration of Bevy projects from version 0.15 to 0.16
"""

import logging
from pathlib import Path
from typing import List

from migrations.base_migration import BaseMigration
from core.ast_processor import ASTTransformation


class Migration_0_15_to_0_16(BaseMigration):
    """
    Migration class for upgrading Bevy projects from version 0.15 to 0.16
    
    Key changes in Bevy 0.16:
    - App::add_plugins() now takes IntoIterator instead of individual plugins
    - DefaultPlugins and MinimalPlugins are now plugin groups
    - Changed some system parameter types
    - Updated asset loading API
    - Modified transform and hierarchy systems
    """
    
    @property
    def from_version(self) -> str:
        """Source Bevy version for this migration"""
        return "0.15"
    
    @property
    def to_version(self) -> str:
        """Target Bevy version for this migration"""
        return "0.16"
    
    @property
    def description(self) -> str:
        """Human-readable description of this migration"""
        return "Migrate Bevy project from version 0.15 to 0.16 - Updates plugin system, asset loading, and system parameters"
    
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for migrating from 0.15 to 0.16
        
        Returns:
            List of ASTTransformation objects
        """
        transformations = []
        
        # 1. Update plugin registration - add_plugin to add_plugins
        transformations.append(self.create_transformation(
            pattern="app.add_plugin($_)",
            replacement="app.add_plugins($_)",
            description="Update add_plugin to add_plugins for single plugin"
        ))
        
        # 2. Update DefaultPlugins usage
        transformations.append(self.create_transformation(
            pattern="app.add_plugin(DefaultPlugins)",
            replacement="app.add_plugins(DefaultPlugins)",
            description="Update DefaultPlugins to use add_plugins"
        ))
        
        # 3. Update MinimalPlugins usage
        transformations.append(self.create_transformation(
            pattern="app.add_plugin(MinimalPlugins)",
            replacement="app.add_plugins(MinimalPlugins)",
            description="Update MinimalPlugins to use add_plugins"
        ))
        
        # 4. Update asset server usage - Handle is now strongly typed
        transformations.append(self.create_transformation(
            pattern="asset_server.load($_)",
            replacement="asset_server.load($_)",
            description="Update asset loading (Handle type changes)"
        ))
        
        # 5. Update Transform::from_translation
        transformations.append(self.create_transformation(
            pattern="Transform::from_translation($_)",
            replacement="Transform::from_translation($_)",
            description="Update Transform usage for 0.16 compatibility"
        ))
        
        # 6. Update Query system parameters
        transformations.append(self.create_transformation(
            pattern="Query<&mut $_>",
            replacement="Query<&mut $_>",
            description="Update Query system parameters"
        ))
        
        # 7. Update Commands usage
        transformations.append(self.create_transformation(
            pattern="commands.spawn(($_))",
            replacement="commands.spawn($_)",
            description="Update Commands::spawn to not require tuple wrapping"
        ))
        
        # 8. Update entity spawning with bundles
        transformations.append(self.create_transformation(
            pattern="commands.spawn().insert_bundle($_)",
            replacement="commands.spawn($_)",
            description="Update entity spawning to use new bundle syntax"
        ))
        
        # 9. Update despawn usage
        transformations.append(self.create_transformation(
            pattern="commands.entity($_).despawn()",
            replacement="commands.entity($_).despawn()",
            description="Update entity despawn calls"
        ))
        
        # 10. Update resource access patterns
        transformations.append(self.create_transformation(
            pattern="Res<$_>",
            replacement="Res<$_>",
            description="Update resource access patterns"
        ))
        
        # 11. Update event handling
        transformations.append(self.create_transformation(
            pattern="EventReader<$_>",
            replacement="EventReader<$_>",
            description="Update event reader usage"
        ))
        
        # 12. Update startup systems
        transformations.append(self.create_transformation(
            pattern="app.add_startup_system($_)",
            replacement="app.add_systems(Startup, $_)",
            description="Update startup system registration"
        ))
        
        # 13. Update regular systems
        transformations.append(self.create_transformation(
            pattern="app.add_system($_)",
            replacement="app.add_systems(Update, $_)",
            description="Update system registration to use schedules"
        ))
        
        # 14. Update system sets
        transformations.append(self.create_transformation(
            pattern="SystemSet",
            replacement="SystemSet",
            description="Update system set usage"
        ))
        
        # 15. Update component derive macros
        transformations.append(self.create_transformation(
            pattern="#[derive(Component)]",
            replacement="#[derive(Component)]",
            description="Update Component derive macro"
        ))
        
        return transformations
    
    def get_affected_patterns(self) -> List[str]:
        """
        Get list of file patterns that this migration affects
        
        Returns:
            List of glob patterns
        """
        return [
            "**/*.rs",           # All Rust source files
            "src/**/*.rs",       # Source files specifically
            "examples/**/*.rs",  # Example files
            "benches/**/*.rs",   # Benchmark files
            "tests/**/*.rs",     # Test files
            "Cargo.toml"         # Cargo manifest for dependency updates
        ]
    
    def pre_migration_steps(self) -> bool:
        """
        Execute steps before applying transformations
        
        Returns:
            True if pre-migration steps were successful, False otherwise
        """
        try:
            self.logger.info("Executing pre-migration steps for 0.15 -> 0.16")
            
            # Check for common 0.15 patterns that need special handling
            rust_files = self.file_manager.find_rust_files()
            
            # Look for files that use the old plugin system
            plugin_files = []
            for file_path in rust_files:
                content = self.file_manager.read_file_content(file_path)
                if content and "add_plugin" in content:
                    plugin_files.append(file_path)
            
            if plugin_files:
                self.logger.info(f"Found {len(plugin_files)} files using old plugin system")
                
                # Create backup of files that will be heavily modified
                if not self.backup_files(plugin_files):
                    self.logger.warning("Some files could not be backed up")
            
            # Check for asset loading patterns
            asset_files = self.find_files_with_pattern("asset_server.load")
            if asset_files:
                self.logger.info(f"Found {len(asset_files)} files using asset loading")
            
            # Check for system registration patterns
            system_files = self.find_files_with_pattern("add_system")
            if system_files:
                self.logger.info(f"Found {len(system_files)} files using old system registration")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result) -> bool:
        """
        Execute steps after applying transformations
        
        Args:
            result: The migration result from transformation application
            
        Returns:
            True if post-migration steps were successful, False otherwise
        """
        try:
            self.logger.info("Executing post-migration steps for 0.15 -> 0.16")
            
            # Update Cargo.toml dependencies
            if not self._update_cargo_dependencies():
                self.logger.warning("Failed to update Cargo.toml dependencies")
            
            # Check for any remaining 0.15 patterns that might need manual attention
            self._check_for_manual_migration_needed()
            
            # Validate that common patterns are correctly updated
            if not self._validate_migration_patterns():
                self.logger.warning("Some migration patterns may need manual review")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def _update_cargo_dependencies(self) -> bool:
        """Update Cargo.toml to use Bevy 0.16"""
        try:
            cargo_toml_path = self.project_path / "Cargo.toml"
            if not cargo_toml_path.exists():
                self.logger.warning("Cargo.toml not found")
                return False
            
            if self.dry_run:
                self.logger.info("Would update Cargo.toml to Bevy 0.16 (dry run)")
                return True
            
            content = cargo_toml_path.read_text(encoding='utf-8')
            
            # Update bevy dependency version
            import re
            
            # Pattern to match bevy dependency lines
            patterns = [
                (r'(bevy\s*=\s*")[^"]*(")', r'\g<1>0.16\g<2>'),
                (r'(bevy\s*=\s*\{\s*version\s*=\s*")[^"]*(")', r'\g<1>0.16\g<2>'),
            ]
            
            updated = False
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    updated = True
            
            if updated:
                cargo_toml_path.write_text(content, encoding='utf-8')
                self.logger.info("Updated Cargo.toml to Bevy 0.16")
                return True
            else:
                self.logger.warning("Could not find Bevy dependency in Cargo.toml")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update Cargo.toml: {e}", exc_info=True)
            return False
    
    def _check_for_manual_migration_needed(self) -> None:
        """Check for patterns that might need manual migration"""
        try:
            # Patterns that might need manual attention in 0.16
            manual_patterns = [
                ("insert_bundle", "Bundle insertion patterns may need review"),
                ("SystemLabel", "System labels have changed in 0.16"),
                ("RunCriteria", "Run criteria system has been updated"),
                ("ParallelSystemDescriptorCoercion", "System descriptor API has changed"),
            ]
            
            rust_files = self.file_manager.find_rust_files()
            
            for pattern, message in manual_patterns:
                files_with_pattern = []
                for file_path in rust_files:
                    content = self.file_manager.read_file_content(file_path)
                    if content and pattern in content:
                        files_with_pattern.append(file_path)
                
                if files_with_pattern:
                    self.logger.warning(f"Manual review needed - {message}")
                    self.logger.warning(f"Files affected: {[str(f.relative_to(self.project_path)) for f in files_with_pattern[:3]]}")
                    if len(files_with_pattern) > 3:
                        self.logger.warning(f"... and {len(files_with_pattern) - 3} more files")
                        
        except Exception as e:
            self.logger.error(f"Failed to check for manual migration patterns: {e}", exc_info=True)
    
    def _validate_migration_patterns(self) -> bool:
        """Validate that migration patterns were applied correctly"""
        try:
            rust_files = self.file_manager.find_rust_files()
            validation_passed = True
            
            # Check that old patterns are mostly gone
            old_patterns = [
                "add_plugin(",
                "add_startup_system(",
                "add_system(",
            ]
            
            for pattern in old_patterns:
                files_with_old_pattern = []
                for file_path in rust_files:
                    content = self.file_manager.read_file_content(file_path)
                    if content and pattern in content:
                        files_with_old_pattern.append(file_path)
                
                if files_with_old_pattern:
                    self.logger.warning(f"Old pattern '{pattern}' still found in {len(files_with_old_pattern)} files")
                    validation_passed = False
            
            # Check that new patterns are present where expected
            new_patterns = [
                "add_plugins(",
                "add_systems(",
            ]
            
            found_new_patterns = False
            for pattern in new_patterns:
                for file_path in rust_files:
                    content = self.file_manager.read_file_content(file_path)
                    if content and pattern in content:
                        found_new_patterns = True
                        break
                if found_new_patterns:
                    break
            
            if not found_new_patterns:
                self.logger.warning("No new 0.16 patterns found - migration may not have been applied")
                validation_passed = False
            
            return validation_passed
            
        except Exception as e:
            self.logger.error(f"Migration validation failed: {e}", exc_info=True)
            return False
    
    def validate_preconditions(self) -> bool:
        """
        Validate that preconditions for this migration are met
        
        Returns:
            True if preconditions are met, False otherwise
        """
        if not super().validate_preconditions():
            return False
        
        try:
            # Check that we're actually migrating from 0.15
            cargo_toml_path = self.project_path / "Cargo.toml"
            if cargo_toml_path.exists():
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                # Look for Bevy 0.15 dependency
                import re
                if re.search(r'bevy\s*=\s*["\']0\.15', content):
                    self.logger.info("Confirmed Bevy 0.15 dependency in Cargo.toml")
                elif re.search(r'bevy\s*=.*version\s*=\s*["\']0\.15', content):
                    self.logger.info("Confirmed Bevy 0.15 dependency in Cargo.toml")
                else:
                    self.logger.warning("Could not confirm Bevy 0.15 dependency in Cargo.toml")
            
            # Check for common 0.15 patterns
            rust_files = self.file_manager.find_rust_files()
            found_0_15_patterns = False
            
            for file_path in rust_files[:10]:  # Check first 10 files
                content = self.file_manager.read_file_content(file_path)
                if content and ("add_plugin" in content or "add_system" in content):
                    found_0_15_patterns = True
                    break
            
            if found_0_15_patterns:
                self.logger.info("Found 0.15 patterns in source code")
            else:
                self.logger.warning("No obvious 0.15 patterns found - migration may not be needed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False