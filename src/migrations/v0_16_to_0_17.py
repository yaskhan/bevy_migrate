"""
Migration from Bevy 0.16 to 0.17
Handles the migration of Bevy projects from version 0.16 to 0.17
"""

import logging
from pathlib import Path
from typing import List

from migrations.base_migration import BaseMigration
from core.ast_processor import ASTTransformation


class Migration_0_16_to_0_17(BaseMigration):
    """
    Migration class for upgrading Bevy projects from version 0.16 to 0.17
    
    Key changes in Bevy 0.17:
    - New required components system
    - Updated ECS with component hooks
    - Changed observer system
    - Modified asset system with new loading patterns
    - Updated UI system with new node bundles
    - Changed camera and rendering systems
    - New animation system improvements
    - Updated input handling
    """
    
    @property
    def from_version(self) -> str:
        """Source Bevy version for this migration"""
        return "0.16"
    
    @property
    def to_version(self) -> str:
        """Target Bevy version for this migration"""
        return "0.17"
    
    @property
    def description(self) -> str:
        """Human-readable description of this migration"""
        return "Migrate Bevy project from version 0.16 to 0.17 - Updates required components, observers, asset system, and UI improvements"
    
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for migrating from 0.16 to 0.17
        
        Returns:
            List of ASTTransformation objects
        """
        transformations = []
        
        # 1. Update component bundles to use required components
        transformations.append(self.create_transformation(
            pattern="commands.spawn(($_bundle, $_component))",
            replacement="commands.spawn($_bundle.with($_component))",
            description="Update bundle spawning with additional components"
        ))
        
        # 2. Update SpriteBundle usage with required components
        transformations.append(self.create_transformation(
            pattern="SpriteBundle { sprite: Sprite { .. }, .. }",
            replacement="SpriteBundle::default()",
            description="Update SpriteBundle to use required components system"
        ))
        
        # 3. Update Camera2dBundle and Camera3dBundle
        transformations.append(self.create_transformation(
            pattern="Camera2dBundle::default()",
            replacement="Camera2d",
            description="Update Camera2dBundle to use required components"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Camera3dBundle::default()",
            replacement="Camera3d",
            description="Update Camera3dBundle to use required components"
        ))
        
        # 4. Update UI node bundles
        transformations.append(self.create_transformation(
            pattern="NodeBundle { style: Style { .. }, .. }",
            replacement="Node::default()",
            description="Update NodeBundle to use required components system"
        ))
        
        # 5. Update ButtonBundle
        transformations.append(self.create_transformation(
            pattern="ButtonBundle::default()",
            replacement="Button",
            description="Update ButtonBundle to use required components"
        ))
        
        # 6. Update TextBundle
        transformations.append(self.create_transformation(
            pattern="TextBundle::from_section($_text, $_style)",
            replacement="Text::new($_text)",
            description="Update TextBundle to use new Text component"
        ))
        
        # 7. Update observer system
        transformations.append(self.create_transformation(
            pattern="app.add_observer($_)",
            replacement="app.observe($_)",
            description="Update observer registration to use new API"
        ))
        
        # 8. Update component hooks
        transformations.append(self.create_transformation(
            pattern="#[derive(Component)]",
            replacement="#[derive(Component)]",
            description="Update Component derive for hooks support"
        ))
        
        # 9. Update asset loading with new Handle system
        transformations.append(self.create_transformation(
            pattern="asset_server.load::<$_>($_)",
            replacement="asset_server.load($_)",
            description="Update asset loading with improved type inference"
        ))
        
        # 10. Update Transform hierarchy operations
        transformations.append(self.create_transformation(
            pattern="GlobalTransform::from($_)",
            replacement="Transform::from($_)",
            description="Update transform usage with new hierarchy system"
        ))
        
        # 11. Update animation system
        transformations.append(self.create_transformation(
            pattern="AnimationPlayer::default()",
            replacement="AnimationPlayer::new()",
            description="Update AnimationPlayer initialization"
        ))
        
        # 12. Update input handling
        transformations.append(self.create_transformation(
            pattern="Input<KeyCode>",
            replacement="ButtonInput<KeyCode>",
            description="Update input system to use ButtonInput"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Input<MouseButton>",
            replacement="ButtonInput<MouseButton>",
            description="Update mouse input to use ButtonInput"
        ))
        
        # 13. Update event handling with new observer system
        transformations.append(self.create_transformation(
            pattern="EventWriter<$_>",
            replacement="EventWriter<$_>",
            description="Update event writer usage"
        ))
        
        # 14. Update mesh and material handling
        transformations.append(self.create_transformation(
            pattern="PbrBundle { mesh: $_mesh, material: $_material, .. }",
            replacement="($_mesh, $_material)",
            description="Update PbrBundle to use required components"
        ))
        
        # 15. Update light bundles
        transformations.append(self.create_transformation(
            pattern="PointLightBundle::default()",
            replacement="PointLight::default()",
            description="Update PointLightBundle to use required components"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DirectionalLightBundle::default()",
            replacement="DirectionalLight::default()",
            description="Update DirectionalLightBundle to use required components"
        ))
        
        # 16. Update scene spawning
        transformations.append(self.create_transformation(
            pattern="SceneBundle { scene: $_scene, .. }",
            replacement="SceneRoot($_scene)",
            description="Update scene spawning to use SceneRoot"
        ))
        
        # 17. Update audio bundles
        transformations.append(self.create_transformation(
            pattern="AudioBundle { source: $_source, .. }",
            replacement="AudioPlayer($_source)",
            description="Update audio system to use AudioPlayer"
        ))
        
        # 18. Update visibility system
        transformations.append(self.create_transformation(
            pattern="VisibilityBundle::default()",
            replacement="Visibility::default()",
            description="Update visibility to use required components"
        ))
        
        # 19. Update gizmo system
        transformations.append(self.create_transformation(
            pattern="Gizmos",
            replacement="Gizmos",
            description="Update gizmo system usage"
        ))
        
        # 20. Update state management
        transformations.append(self.create_transformation(
            pattern="app.add_state::<$_>()",
            replacement="app.init_state::<$_>()",
            description="Update state initialization"
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
            self.logger.info("Executing pre-migration steps for 0.16 -> 0.17")
            
            # Check for common 0.16 patterns that need special handling
            rust_files = self.file_manager.find_rust_files()
            
            # Look for files that use bundle patterns
            bundle_files = []
            bundle_patterns = ["Bundle", "SpriteBundle", "Camera2dBundle", "Camera3dBundle", "NodeBundle"]
            
            for file_path in rust_files:
                content = self.file_manager.read_file_content(file_path)
                if content:
                    for pattern in bundle_patterns:
                        if pattern in content:
                            bundle_files.append(file_path)
                            break
            
            if bundle_files:
                self.logger.info(f"Found {len(bundle_files)} files using bundle patterns")
                
                # Create backup of files that will be heavily modified
                if not self.backup_files(bundle_files):
                    self.logger.warning("Some files could not be backed up")
            
            # Check for observer system usage
            observer_files = self.find_files_with_pattern("add_observer")
            if observer_files:
                self.logger.info(f"Found {len(observer_files)} files using observer system")
            
            # Check for input system usage
            input_files = self.find_files_with_pattern("Input<")
            if input_files:
                self.logger.info(f"Found {len(input_files)} files using old input system")
            
            # Check for animation system usage
            animation_files = self.find_files_with_pattern("AnimationPlayer")
            if animation_files:
                self.logger.info(f"Found {len(animation_files)} files using animation system")
            
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
            self.logger.info("Executing post-migration steps for 0.16 -> 0.17")
            
            # Update Cargo.toml dependencies
            if not self._update_cargo_dependencies():
                self.logger.warning("Failed to update Cargo.toml dependencies")
            
            # Check for any remaining 0.16 patterns that might need manual attention
            self._check_for_manual_migration_needed()
            
            # Validate that common patterns are correctly updated
            if not self._validate_migration_patterns():
                self.logger.warning("Some migration patterns may need manual review")
            
            # Check for required component usage
            self._validate_required_components()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def _update_cargo_dependencies(self) -> bool:
        """Update Cargo.toml to use Bevy 0.17"""
        try:
            cargo_toml_path = self.project_path / "Cargo.toml"
            if not cargo_toml_path.exists():
                self.logger.warning("Cargo.toml not found")
                return False
            
            if self.dry_run:
                self.logger.info("Would update Cargo.toml to Bevy 0.17 (dry run)")
                return True
            
            content = cargo_toml_path.read_text(encoding='utf-8')
            
            # Update bevy dependency version
            import re
            
            # Pattern to match bevy dependency lines
            patterns = [
                (r'(bevy\s*=\s*")[^"]*(")', r'\g<1>0.17\g<2>'),
                (r'(bevy\s*=\s*\{\s*version\s*=\s*")[^"]*(")', r'\g<1>0.17\g<2>'),
            ]
            
            updated = False
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    updated = True
            
            if updated:
                cargo_toml_path.write_text(content, encoding='utf-8')
                self.logger.info("Updated Cargo.toml to Bevy 0.17")
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
            # Patterns that might need manual attention in 0.17
            manual_patterns = [
                ("Bundle", "Bundle usage may need conversion to required components"),
                ("Observer", "Observer system has new API patterns"),
                ("ComponentHooks", "Component hooks may need manual implementation"),
                ("AssetEvent", "Asset events have changed in 0.17"),
                ("UiImage", "UI image handling has been updated"),
                ("Interaction", "UI interaction system has changes"),
                ("AnimationClip", "Animation clips have new features"),
                ("Gltf", "GLTF loading has improvements that may need updates"),
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
                "Camera2dBundle",
                "Camera3dBundle",
                "SpriteBundle {",
                "NodeBundle {",
                "ButtonBundle",
                "Input<KeyCode>",
                "Input<MouseButton>",
                "add_observer(",
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
                "Camera2d",
                "Camera3d",
                "ButtonInput<",
                "observe(",
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
                self.logger.info("No new 0.17 patterns found - this may be normal if project doesn't use affected systems")
            
            return validation_passed
            
        except Exception as e:
            self.logger.error(f"Migration validation failed: {e}", exc_info=True)
            return False
    
    def _validate_required_components(self) -> None:
        """Validate that required components are being used correctly"""
        try:
            rust_files = self.file_manager.find_rust_files()
            
            # Look for potential required component issues
            component_patterns = [
                ("Transform", "Transform is now a required component for many bundles"),
                ("Visibility", "Visibility is now a required component"),
                ("GlobalTransform", "GlobalTransform is automatically added as required component"),
            ]
            
            for pattern, message in component_patterns:
                files_with_pattern = []
                for file_path in rust_files:
                    content = self.file_manager.read_file_content(file_path)
                    if content and f"commands.spawn(({pattern}" in content:
                        files_with_pattern.append(file_path)
                
                if files_with_pattern:
                    self.logger.info(f"Found manual {pattern} usage - {message}")
                    self.logger.info(f"Files: {[str(f.relative_to(self.project_path)) for f in files_with_pattern[:2]]}")
                    
        except Exception as e:
            self.logger.error(f"Required components validation failed: {e}", exc_info=True)
    
    def validate_preconditions(self) -> bool:
        """
        Validate that preconditions for this migration are met
        
        Returns:
            True if preconditions are met, False otherwise
        """
        if not super().validate_preconditions():
            return False
        
        try:
            # Check that we're actually migrating from 0.16
            cargo_toml_path = self.project_path / "Cargo.toml"
            if cargo_toml_path.exists():
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                # Look for Bevy 0.16 dependency
                import re
                if re.search(r'bevy\s*=\s*["\']0\.16', content):
                    self.logger.info("Confirmed Bevy 0.16 dependency in Cargo.toml")
                elif re.search(r'bevy\s*=.*version\s*=\s*["\']0\.16', content):
                    self.logger.info("Confirmed Bevy 0.16 dependency in Cargo.toml")
                else:
                    self.logger.warning("Could not confirm Bevy 0.16 dependency in Cargo.toml")
            
            # Check for common 0.16 patterns
            rust_files = self.file_manager.find_rust_files()
            found_0_16_patterns = False
            
            patterns_to_check = ["Bundle", "add_plugins", "add_systems"]
            
            for file_path in rust_files[:10]:  # Check first 10 files
                content = self.file_manager.read_file_content(file_path)
                if content:
                    for pattern in patterns_to_check:
                        if pattern in content:
                            found_0_16_patterns = True
                            break
                    if found_0_16_patterns:
                        break
            
            if found_0_16_patterns:
                self.logger.info("Found 0.16 patterns in source code")
            else:
                self.logger.warning("No obvious 0.16 patterns found - migration may not be needed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False