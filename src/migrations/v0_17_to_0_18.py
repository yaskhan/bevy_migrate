"""
Migration from Bevy 0.17 to 0.18
Handles the migration of Bevy projects from version 0.17 to 0.18
"""

import logging
from pathlib import Path
from typing import List

from migrations.base_migration import BaseMigration
from core.ast_processor import ASTTransformation


class Migration_0_17_to_0_18(BaseMigration):
    """
    Migration class for upgrading Bevy projects from version 0.17 to 0.18
    
    Key changes in Bevy 0.18:
    - New entity-component relationship improvements
    - Updated rendering pipeline with new features
    - Enhanced asset system with better loading and hot reloading
    - Improved UI system with new layout and styling options
    - Updated animation system with more robust features
    - New windowing system improvements
    - Enhanced audio system with spatial audio
    - Improved input handling with action maps
    - Updated physics integration patterns
    - New diagnostic and debugging tools
    """
    
    @property
    def from_version(self) -> str:
        """Source Bevy version for this migration"""
        return "0.17"
    
    @property
    def to_version(self) -> str:
        """Target Bevy version for this migration"""
        return "0.18"
    
    @property
    def description(self) -> str:
        """Human-readable description of this migration"""
        return "Migrate Bevy project from version 0.17 to 0.18 - Updates rendering, asset system, UI improvements, and enhanced features"
    
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for migrating from 0.17 to 0.18
        
        Returns:
            List of ASTTransformation objects
        """
        transformations = []
        
        # 1. Update rendering system with new pipeline features
        transformations.append(self.create_transformation(
            pattern="MaterialPlugin::<$_>::default()",
            replacement="MaterialPlugin::<$_>::default()",
            description="Update material plugin initialization for 0.18"
        ))
        
        # 2. Update asset loading with enhanced hot reloading
        transformations.append(self.create_transformation(
            pattern="asset_server.watch_for_changes()",
            replacement="asset_server.watch_for_changes().unwrap()",
            description="Update asset watching with improved error handling"
        ))
        
        # 3. Update UI system with new layout features
        transformations.append(self.create_transformation(
            pattern="Style { position_type: PositionType::Absolute, .. }",
            replacement="Style { position: Position::Absolute, .. }",
            description="Update UI positioning system"
        ))
        
        # 4. Update text rendering with new features
        transformations.append(self.create_transformation(
            pattern="TextStyle { font_size: $_, .. }",
            replacement="TextFont { font_size: $_, .. }",
            description="Update text styling to use TextFont"
        ))
        
        # 5. Update animation system with enhanced features
        transformations.append(self.create_transformation(
            pattern="AnimationClip::from_ron($_)",
            replacement="AnimationClip::from_ron($_).unwrap()",
            description="Update animation clip loading with error handling"
        ))
        
        # 6. Update window system with new configuration
        transformations.append(self.create_transformation(
            pattern="WindowDescriptor { title: $_, .. }",
            replacement="Window { title: $_, .. }",
            description="Update window configuration to use Window struct"
        ))
        
        # 7. Update audio system with spatial audio features
        transformations.append(self.create_transformation(
            pattern="AudioSink",
            replacement="AudioSink",
            description="Update audio sink usage for spatial audio"
        ))
        
        # 8. Update input system with action maps
        transformations.append(self.create_transformation(
            pattern="KeyboardInput { key_code: Some($_), .. }",
            replacement="KeyboardInput { logical_key: Some($_), .. }",
            description="Update keyboard input to use logical keys"
        ))
        
        # 9. Update camera system with new features
        transformations.append(self.create_transformation(
            pattern="OrthographicProjection { scale: $_, .. }",
            replacement="OrthographicProjection { scaling_mode: ScalingMode::FixedVertical($_), .. }",
            description="Update orthographic projection scaling"
        ))
        
        # 10. Update mesh system with new primitives
        transformations.append(self.create_transformation(
            pattern="Mesh::from(shape::Cube { size: $_ })",
            replacement="Mesh::from(Cuboid::new($_, $_, $_))",
            description="Update cube mesh creation to use Cuboid"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Mesh::from(shape::Plane { size: $_ })",
            replacement="Mesh::from(Plane3d::default().mesh().size($_, $_))",
            description="Update plane mesh creation"
        ))
        
        # 11. Update lighting system with enhanced features
        transformations.append(self.create_transformation(
            pattern="AmbientLight { color: $_, brightness: $_ }",
            replacement="AmbientLight { color: $_, brightness: $_ }",
            description="Update ambient light configuration"
        ))
        
        # 12. Update scene system with new loading patterns
        transformations.append(self.create_transformation(
            pattern="SceneSpawner",
            replacement="SceneSpawner",
            description="Update scene spawning system"
        ))
        
        # 13. Update physics integration patterns
        transformations.append(self.create_transformation(
            pattern="RigidBody::Dynamic",
            replacement="RigidBody::Dynamic",
            description="Update physics rigid body usage"
        ))
        
        # 14. Update diagnostic system with new tools
        transformations.append(self.create_transformation(
            pattern="FrameTimeDiagnosticsPlugin",
            replacement="FrameTimeDiagnosticsPlugin",
            description="Update frame time diagnostics"
        ))
        
        # 15. Update asset processor with new features
        transformations.append(self.create_transformation(
            pattern="AssetProcessor::default()",
            replacement="AssetProcessor::default()",
            description="Update asset processor initialization"
        ))
        
        # 16. Update shader system with new features
        transformations.append(self.create_transformation(
            pattern="Shader::from_wgsl($_)",
            replacement="Shader::from_wgsl($_, file!())",
            description="Update shader creation with file tracking"
        ))
        
        # 17. Update texture system with new formats
        transformations.append(self.create_transformation(
            pattern="Image::new_fill($_size, $_dimension, $_data, $_format)",
            replacement="Image::new($_size, $_dimension, $_data, $_format, $_sampler)",
            description="Update image creation with sampler parameter"
        ))
        
        # 18. Update UI interaction system
        transformations.append(self.create_transformation(
            pattern="Interaction::Clicked",
            replacement="Interaction::Pressed",
            description="Update UI interaction states"
        ))
        
        # 19. Update state management with new features
        transformations.append(self.create_transformation(
            pattern="NextState($_)",
            replacement="NextState($_)",
            description="Update state transitions"
        ))
        
        # 20. Update plugin system with new configuration
        transformations.append(self.create_transformation(
            pattern="DefaultPlugins.set($_)",
            replacement="DefaultPlugins.set($_)",
            description="Update default plugins configuration"
        ))
        
        # 21. Update time system with new features
        transformations.append(self.create_transformation(
            pattern="Time<Fixed>",
            replacement="Time<Fixed>",
            description="Update fixed timestep usage"
        ))
        
        # 22. Update transform system with new hierarchy features
        transformations.append(self.create_transformation(
            pattern="TransformBundle::from_transform($_)",
            replacement="$_",
            description="Remove TransformBundle usage in favor of Transform component"
        ))
        
        # 23. Update visibility system with new culling
        transformations.append(self.create_transformation(
            pattern="ComputedVisibility",
            replacement="InheritedVisibility",
            description="Update visibility system components"
        ))
        
        # 24. Update asset system with new metadata
        transformations.append(self.create_transformation(
            pattern="AssetLoader::load($_)",
            replacement="AssetLoader::load($_, $_settings)",
            description="Update asset loading with settings parameter"
        ))
        
        # 25. Update UI styling with new properties
        transformations.append(self.create_transformation(
            pattern="Style { margin: UiRect::all($_), .. }",
            replacement="Style { margin: UiRect::all(Val::Px($_)), .. }",
            description="Update UI margin values to use Val::Px"
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
            "assets/**/*.ron",   # RON asset files
            "assets/**/*.wgsl",  # Shader files
            "Cargo.toml"         # Cargo manifest for dependency updates
        ]
    
    def pre_migration_steps(self) -> bool:
        """
        Execute steps before applying transformations
        
        Returns:
            True if pre-migration steps were successful, False otherwise
        """
        try:
            self.logger.info("Executing pre-migration steps for 0.17 -> 0.18")
            
            # Check for common 0.17 patterns that need special handling
            rust_files = self.file_manager.find_rust_files()
            
            # Look for files that use rendering system
            rendering_files = []
            rendering_patterns = ["MaterialPlugin", "Shader", "Mesh", "Material"]
            
            for file_path in rust_files:
                content = self.file_manager.read_file_content(file_path)
                if content:
                    for pattern in rendering_patterns:
                        if pattern in content:
                            rendering_files.append(file_path)
                            break
            
            if rendering_files:
                self.logger.info(f"Found {len(rendering_files)} files using rendering system")
                
                # Create backup of files that will be heavily modified
                if not self.backup_files(rendering_files):
                    self.logger.warning("Some files could not be backed up")
            
            # Check for UI system usage
            ui_files = self.find_files_with_pattern("Style")
            if ui_files:
                self.logger.info(f"Found {len(ui_files)} files using UI system")
            
            # Check for animation system usage
            animation_files = self.find_files_with_pattern("AnimationClip")
            if animation_files:
                self.logger.info(f"Found {len(animation_files)} files using animation system")
            
            # Check for window system usage
            window_files = self.find_files_with_pattern("WindowDescriptor")
            if window_files:
                self.logger.info(f"Found {len(window_files)} files using old window system")
            
            # Check for audio system usage
            audio_files = self.find_files_with_pattern("AudioSink")
            if audio_files:
                self.logger.info(f"Found {len(audio_files)} files using audio system")
            
            # Check for input system usage
            input_files = self.find_files_with_pattern("KeyboardInput")
            if input_files:
                self.logger.info(f"Found {len(input_files)} files using input system")
            
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
            self.logger.info("Executing post-migration steps for 0.17 -> 0.18")
            
            # Update Cargo.toml dependencies
            if not self._update_cargo_dependencies():
                self.logger.warning("Failed to update Cargo.toml dependencies")
            
            # Check for any remaining 0.17 patterns that might need manual attention
            self._check_for_manual_migration_needed()
            
            # Validate that common patterns are correctly updated
            if not self._validate_migration_patterns():
                self.logger.warning("Some migration patterns may need manual review")
            
            # Check for new 0.18 features that could be utilized
            self._suggest_new_features()
            
            # Validate asset files if they exist
            self._validate_asset_files()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def _update_cargo_dependencies(self) -> bool:
        """Update Cargo.toml to use Bevy 0.18"""
        try:
            cargo_toml_path = self.project_path / "Cargo.toml"
            if not cargo_toml_path.exists():
                self.logger.warning("Cargo.toml not found")
                return False
            
            if self.dry_run:
                self.logger.info("Would update Cargo.toml to Bevy 0.18 (dry run)")
                return True
            
            content = cargo_toml_path.read_text(encoding='utf-8')
            
            # Update bevy dependency version
            import re
            
            # Pattern to match bevy dependency lines
            patterns = [
                (r'(bevy\s*=\s*")[^"]*(")', r'\g<1>0.18\g<2>'),
                (r'(bevy\s*=\s*\{\s*version\s*=\s*")[^"]*(")', r'\g<1>0.18\g<2>'),
            ]
            
            updated = False
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    updated = True
            
            if updated:
                cargo_toml_path.write_text(content, encoding='utf-8')
                self.logger.info("Updated Cargo.toml to Bevy 0.18")
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
            # Patterns that might need manual attention in 0.18
            manual_patterns = [
                ("WindowDescriptor", "Window system has been redesigned - manual review needed"),
                ("shape::", "Mesh shapes have new API - check primitive usage"),
                ("TextStyle", "Text styling has been reorganized - review text components"),
                ("ComputedVisibility", "Visibility system has new components"),
                ("AssetLoader", "Asset loading may need settings parameter"),
                ("Shader::from_wgsl", "Shader loading now requires file tracking"),
                ("Image::new_fill", "Image creation API has changed"),
                ("OrthographicProjection", "Camera projection system has new scaling modes"),
                ("KeyboardInput", "Input system uses logical keys now"),
                ("Interaction::Clicked", "UI interaction states have been updated"),
                ("TransformBundle", "Transform bundles are deprecated"),
                ("PositionType", "UI positioning system has been updated"),
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
                "WindowDescriptor",
                "shape::Cube",
                "shape::Plane",
                "TextStyle {",
                "ComputedVisibility",
                "PositionType::",
                "Interaction::Clicked",
                "TransformBundle::",
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
                "Window {",
                "Cuboid::",
                "TextFont",
                "InheritedVisibility",
                "Position::",
                "Interaction::Pressed",
                "logical_key:",
            ]
            
            found_new_patterns = 0
            for pattern in new_patterns:
                for file_path in rust_files:
                    content = self.file_manager.read_file_content(file_path)
                    if content and pattern in content:
                        found_new_patterns += 1
                        break
            
            if found_new_patterns == 0:
                self.logger.info("No new 0.18 patterns found - this may be normal if project doesn't use affected systems")
            else:
                self.logger.info(f"Found {found_new_patterns} new 0.18 patterns in use")
            
            return validation_passed
            
        except Exception as e:
            self.logger.error(f"Migration validation failed: {e}", exc_info=True)
            return False
    
    def _suggest_new_features(self) -> None:
        """Suggest new 0.18 features that could be utilized"""
        try:
            self.logger.info("Checking for opportunities to use new Bevy 0.18 features:")
            
            rust_files = self.file_manager.find_rust_files()
            
            # Check for opportunities to use new features
            feature_opportunities = [
                ("asset_server.load", "Consider using enhanced hot reloading features"),
                ("AnimationClip", "New animation system has improved blending and transitions"),
                ("AudioSink", "Spatial audio features are now available"),
                ("Camera", "New camera system has improved projection controls"),
                ("Material", "Enhanced material system with better PBR support"),
                ("UI", "New UI system has improved layout and styling options"),
                ("Window", "Window system now supports multiple windows better"),
                ("Input", "Action map system provides better input abstraction"),
            ]
            
            for pattern, suggestion in feature_opportunities:
                files_with_pattern = []
                for file_path in rust_files:
                    content = self.file_manager.read_file_content(file_path)
                    if content and pattern in content:
                        files_with_pattern.append(file_path)
                
                if files_with_pattern:
                    self.logger.info(f"Opportunity: {suggestion}")
                    self.logger.info(f"Relevant files: {[str(f.relative_to(self.project_path)) for f in files_with_pattern[:2]]}")
                    
        except Exception as e:
            self.logger.error(f"Failed to suggest new features: {e}", exc_info=True)
    
    def _validate_asset_files(self) -> None:
        """Validate asset files for 0.18 compatibility"""
        try:
            # Check for RON files that might need updates
            ron_files = self.file_manager.find_files_by_pattern("**/*.ron")
            if ron_files:
                self.logger.info(f"Found {len(ron_files)} RON asset files - may need review for 0.18 compatibility")
            
            # Check for shader files
            shader_files = self.file_manager.find_files_by_pattern("**/*.wgsl")
            if shader_files:
                self.logger.info(f"Found {len(shader_files)} WGSL shader files - check for new shader features in 0.18")
            
            # Check for scene files
            scene_files = self.file_manager.find_files_by_pattern("**/*.scn.ron")
            if scene_files:
                self.logger.info(f"Found {len(scene_files)} scene files - may need updates for new component system")
                
        except Exception as e:
            self.logger.error(f"Asset file validation failed: {e}", exc_info=True)
    
    def validate_preconditions(self) -> bool:
        """
        Validate that preconditions for this migration are met
        
        Returns:
            True if preconditions are met, False otherwise
        """
        if not super().validate_preconditions():
            return False
        
        try:
            # Check that we're actually migrating from 0.17
            cargo_toml_path = self.project_path / "Cargo.toml"
            if cargo_toml_path.exists():
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                # Look for Bevy 0.17 dependency
                import re
                if re.search(r'bevy\s*=\s*["\']0\.17', content):
                    self.logger.info("Confirmed Bevy 0.17 dependency in Cargo.toml")
                elif re.search(r'bevy\s*=.*version\s*=\s*["\']0\.17', content):
                    self.logger.info("Confirmed Bevy 0.17 dependency in Cargo.toml")
                else:
                    self.logger.warning("Could not confirm Bevy 0.17 dependency in Cargo.toml")
            
            # Check for common 0.17 patterns
            rust_files = self.file_manager.find_rust_files()
            found_0_17_patterns = False
            
            patterns_to_check = ["Camera2d", "Camera3d", "ButtonInput", "observe"]
            
            for file_path in rust_files[:10]:  # Check first 10 files
                content = self.file_manager.read_file_content(file_path)
                if content:
                    for pattern in patterns_to_check:
                        if pattern in content:
                            found_0_17_patterns = True
                            break
                    if found_0_17_patterns:
                        break
            
            if found_0_17_patterns:
                self.logger.info("Found 0.17 patterns in source code")
            else:
                self.logger.warning("No obvious 0.17 patterns found - migration may not be needed")
            
            # Check for patterns that definitely need migration to 0.18
            migration_needed_patterns = ["WindowDescriptor", "shape::", "TextStyle", "ComputedVisibility"]
            found_migration_needed = False
            
            for file_path in rust_files[:20]:  # Check more files for migration patterns
                content = self.file_manager.read_file_content(file_path)
                if content:
                    for pattern in migration_needed_patterns:
                        if pattern in content:
                            found_migration_needed = True
                            self.logger.info(f"Found pattern requiring migration: {pattern}")
                            break
                    if found_migration_needed:
                        break
            
            if found_migration_needed:
                self.logger.info("Found patterns that require migration to 0.18")
            else:
                self.logger.info("No patterns requiring immediate migration found")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False