"""
Migration from Bevy 0.12 to 0.13
Handles the migration of Bevy projects from version 0.12 to 0.13
"""

import logging
import re
from pathlib import Path
from typing import List

from bevymigrate.migrations.base_migration import BaseMigration, MigrationResult
from bevymigrate.core.ast_processor import ASTTransformation


class Migration_0_12_to_0_13(BaseMigration):
    """
    Migration class for upgrading Bevy projects from version 0.12 to 0.13
    
    Key changes in Bevy 0.13:
    - Split WorldQuery into QueryData and QueryFilter
    - Rename Input to ButtonInput
    - TextureAtlas rework
    - Event send methods now return EventId
    - Deprecated mesh shapes in bevy_render
    - Many rendering, UI, and windowing changes
    """
    
    @property
    def from_version(self) -> str:
        """Source Bevy version for this migration"""
        return "0.12"
    
    @property
    def to_version(self) -> str:
        """Target Bevy version for this migration"""
        return "0.13"
    
    @property
    def description(self) -> str:
        """Human-readable description of this migration"""
        return "Migrate Bevy project from version 0.12 to 0.13 - Major ECS, rendering, and API changes"
    
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for migrating from 0.12 to 0.13
        
        Returns:
            List of ASTTransformation objects
        """
        transformations = []
        
        # ===== ECS CHANGES =====
        
        # 1. Rename Input to ButtonInput
        transformations.append(self.create_transformation(
            pattern="Input<$TYPE>",
            replacement="ButtonInput<$TYPE>",
            description="Rename Input to ButtonInput"
        ))
        
        # 2. Replace Option<With<T>> with Has<T>
        transformations.append(self.create_transformation(
            pattern="Option<With<$TYPE>>",
            replacement="Has<$TYPE>",
            description="Replace Option<With<T>> with Has<T>"
        ))
        
        # 3. WorldQuery derive to QueryData
        transformations.append(self.create_transformation(
            pattern="#[derive(WorldQuery)]",
            replacement="#[derive(QueryData)]",
            description="Update WorldQuery derive to QueryData"
        ))
        
        # 4. world_query attribute to query_data
        transformations.append(self.create_transformation(
            pattern="#[world_query($ARGS)]",
            replacement="#[query_data($ARGS)]",
            description="Update world_query attribute to query_data"
        ))
        
        # 5. ReadOnlyWorldQuery to QueryFilter  
        transformations.append(self.create_transformation(
            pattern="ReadOnlyWorldQuery",
            replacement="QueryFilter",
            description="Rename ReadOnlyWorldQuery to QueryFilter"
        ))
        
        # 6. Rename add_state to init_state
        transformations.append(self.create_transformation(
            pattern="$APP.add_state($STATE)",
            replacement="$APP.init_state($STATE)",
            description="Rename App::add_state to init_state"
        ))
        
        # 7. Simplify run conditions - remove parentheses
        conditions = [
            'resource_exists', 'resource_added', 'resource_changed',
            'resource_exists_and_changed', 'state_exists', 'state_changed',
            'any_with_component'
        ]
        for condition in conditions:
            transformations.append(self.create_transformation(
                pattern=f"{condition}<$TYPE>()",
                replacement=f"{condition}<$TYPE>",
                description=f"Simplify {condition} run condition (remove parentheses)"
            ))
        
        # 8. TableRow and TableId method renames
        transformations.append(self.create_transformation(
            pattern="TableRow::new($EXPR)",
            replacement="TableRow::from_usize($EXPR)",
            description="Rename TableRow::new to from_usize"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$VAR.index()",
            replacement="$VAR.as_usize()",
            description="Rename index() to as_usize() for TableRow/TableId"
        ))
        
        transformations.append(self.create_transformation(
            pattern="TableId::new($EXPR)",
            replacement="TableId::from_usize($EXPR)",
            description="Rename TableId::new to from_usize"
        ))
        
        # ===== RENDERING CHANGES =====
        
        # 9. TextureAtlas to TextureAtlasLayout in Assets
        transformations.append(self.create_transformation(
            pattern="Assets<TextureAtlas>",
            replacement="Assets<TextureAtlasLayout>",
            description="Rename TextureAtlas asset to TextureAtlasLayout"
        ))
        
        # 10. TextureAtlasSprite to TextureAtlas component
        transformations.append(self.create_transformation(
            pattern="TextureAtlasSprite",
            replacement="TextureAtlas",
            description="Replace TextureAtlasSprite with TextureAtlas component"
        ))
        
        # 11. Deprecated shape types - common patterns
        transformations.append(self.create_transformation(
            pattern="shape::Cube",
            replacement="Cuboid",
            description="Replace deprecated shape::Cube with Cuboid"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::Box",
            replacement="Cuboid",
            description="Replace deprecated shape::Box with Cuboid"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::Quad",
            replacement="Rectangle",
            description="Replace deprecated shape::Quad with Rectangle"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::Plane",
            replacement="Plane3d",
            description="Replace deprecated shape::Plane with Plane3d"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::Circle",
            replacement="Circle",
            description="Replace deprecated shape::Circle with Circle"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::UVSphere",
            replacement="Sphere",
            description="Replace deprecated shape::UVSphere with Sphere"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::Icosphere",
            replacement="Sphere",
            description="Replace deprecated shape::Icosphere with Sphere"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::Capsule",
            replacement="Capsule3d",
            description="Replace deprecated shape::Capsule with Capsule3d"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::Cylinder",
            replacement="Cylinder",
            description="Replace deprecated shape::Cylinder with Cylinder"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::Torus",
            replacement="Torus",
            description="Replace deprecated shape::Torus with Torus"
        ))
        
        transformations.append(self.create_transformation(
            pattern="shape::RegularPolygon",
            replacement="RegularPolygon",
            description="Replace deprecated shape::RegularPolygon with RegularPolygon"
        ))
        
        # 12. Color conversion methods
        transformations.append(self.create_transformation(
            pattern="Color::from($EXPR)",
            replacement="Color::rgba_from_array($EXPR)",
            description="Update Color::from to rgba_from_array"
        ))
        
        # 13. Mesh::set_indices to insert_indices
        transformations.append(self.create_transformation(
            pattern="$MESH.set_indices($INDICES)",
            replacement="$MESH.insert_indices($INDICES)",
            description="Rename Mesh::set_indices to insert_indices"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$MESH.with_indices($INDICES)",
            replacement="$MESH.with_inserted_indices($INDICES)",
            description="Rename Mesh::with_indices to with_inserted_indices"
        ))
        
        # 14. RenderGraph labelization
        transformations.append(self.create_transformation(
            pattern="core_3d::graph::NAME",
            replacement="Core3d",
            description="Update 3D graph name to Core3d label"
        ))
        
        transformations.append(self.create_transformation(
            pattern="core_2d::graph::NAME",
            replacement="Core2d",
            description="Update 2D graph name to Core2d label"
        ))
        
        # ===== MATH CHANGES =====
        
        # 15. Direction renames
        transformations.append(self.create_transformation(
            pattern="Direction2d::from_normalized($EXPR)",
            replacement="Direction2d::new_unchecked($EXPR)",
            description="Rename Direction2d::from_normalized to new_unchecked"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Direction3d::from_normalized($EXPR)",
            replacement="Direction3d::new_unchecked($EXPR)",
            description="Rename Direction3d::from_normalized to new_unchecked"
        ))
        
        # 16. Ray to Ray3d
        transformations.append(self.create_transformation(
            pattern="Ray { $FIELDS }",
            replacement="Ray3d { $FIELDS }",
            description="Rename Ray struct to Ray3d"
        ))
        
        # 17. RayTest to RayCast
        transformations.append(self.create_transformation(
            pattern="RayTest2d",
            replacement="RayCast2d",
            description="Rename RayTest2d to RayCast2d"
        ))
        
        transformations.append(self.create_transformation(
            pattern="RayTest3d",
            replacement="RayCast3d",
            description="Rename RayTest3d to RayCast3d"
        ))
        
        # 18. Capsule to Capsule3d (standalone, not shape::)
        transformations.append(self.create_transformation(
            pattern="Capsule { $FIELDS }",
            replacement="Capsule3d { $FIELDS }",
            description="Rename Capsule to Capsule3d"
        ))
        
        # ===== TEXT & UI CHANGES =====
        
        # 19. TextAlignment to JustifyText
        transformations.append(self.create_transformation(
            pattern="TextAlignment",
            replacement="JustifyText",
            description="Rename TextAlignment to JustifyText"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$BUNDLE.with_text_alignment($ALIGN)",
            replacement="$BUNDLE.with_text_justify($ALIGN)",
            description="Rename with_text_alignment to with_text_justify"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$TEXT.with_alignment($ALIGN)",
            replacement="$TEXT.with_justify($ALIGN)",
            description="Rename Text::with_alignment to with_justify"
        ))
        
        # ===== TIME CHANGES =====
        
        # 20. Timer method renames
        transformations.append(self.create_transformation(
            pattern="$TIMER.percent()",
            replacement="$TIMER.fraction()",
            description="Rename Timer::percent to fraction"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$TIMER.percent_left()",
            replacement="$TIMER.fraction_remaining()",
            description="Rename Timer::percent_left to fraction_remaining"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$TIME.overstep_percentage()",
            replacement="$TIME.overstep_fraction()",
            description="Rename overstep_percentage to overstep_fraction"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$TIME.overstep_percentage_f64()",
            replacement="$TIME.overstep_fraction_f64()",
            description="Rename overstep_percentage_f64 to overstep_fraction_f64"
        ))
        
        # ===== HIERARCHY CHANGES =====
        
        # 21. AddChild to PushChild
        transformations.append(self.create_transformation(
            pattern="AddChild",
            replacement="PushChild",
            description="Rename AddChild to PushChild"
        ))
        
        transformations.append(self.create_transformation(
            pattern="AddChildInPlace",
            replacement="PushChildInPlace",
            description="Rename AddChildInPlace to PushChildInPlace"
        ))
        
        # ===== AUDIO CHANGES =====
        
        # 22. AudioPlugin::spatial_scale to default_spatial_scale
        transformations.append(self.create_transformation(
            pattern="AudioPlugin { spatial_scale: $SCALE, $REST }",
            replacement="AudioPlugin { default_spatial_scale: $SCALE, $REST }",
            description="Rename AudioPlugin::spatial_scale to default_spatial_scale"
        ))
        
        # ===== DIAGNOSTICS CHANGES =====
        
        # 23. DiagnosticId to DiagnosticPath
        transformations.append(self.create_transformation(
            pattern="DiagnosticId",
            replacement="DiagnosticPath",
            description="Rename DiagnosticId to DiagnosticPath"
        ))
        
        # ===== GIZMOS CHANGES =====
        
        # 24. Gizmo type renames
        transformations.append(self.create_transformation(
            pattern="gizmos::CircleBuilder",
            replacement="gizmos::circles::Circle2dBuilder",
            description="Update CircleBuilder path"
        ))
        
        transformations.append(self.create_transformation(
            pattern="gizmos::Circle2dBuilder",
            replacement="gizmos::circles::Circle2dBuilder",
            description="Update Circle2dBuilder path"
        ))
        
        transformations.append(self.create_transformation(
            pattern="gizmos::Arc2dBuilder",
            replacement="gizmos::arcs::Arc2dBuilder",
            description="Update Arc2dBuilder path"
        ))
        
        # ===== WINDOWING & INPUT CHANGES =====
        
        # 25. KeyCode renames - most common ones
        key_mappings = [
            ('KeyCode::W', 'KeyCode::KeyW'),
            ('KeyCode::A', 'KeyCode::KeyA'),
            ('KeyCode::S', 'KeyCode::KeyS'),
            ('KeyCode::D', 'KeyCode::KeyD'),
            ('KeyCode::Q', 'KeyCode::KeyQ'),
            ('KeyCode::E', 'KeyCode::KeyE'),
            ('KeyCode::Up', 'KeyCode::ArrowUp'),
            ('KeyCode::Down', 'KeyCode::ArrowDown'),
            ('KeyCode::Left', 'KeyCode::ArrowLeft'),
            ('KeyCode::Right', 'KeyCode::ArrowRight'),
            ('KeyCode::Key1', 'KeyCode::Digit1'),
            ('KeyCode::Key2', 'KeyCode::Digit2'),
            ('KeyCode::Key3', 'KeyCode::Digit3'),
            ('KeyCode::Key4', 'KeyCode::Digit4'),
            ('KeyCode::Key5', 'KeyCode::Digit5'),
            ('KeyCode::Key6', 'KeyCode::Digit6'),
            ('KeyCode::Key7', 'KeyCode::Digit7'),
            ('KeyCode::Key8', 'KeyCode::Digit8'),
            ('KeyCode::Key9', 'KeyCode::Digit9'),
            ('KeyCode::Key0', 'KeyCode::Digit0'),
        ]
        
        for old_key, new_key in key_mappings:
            transformations.append(self.create_transformation(
                pattern=old_key,
                replacement=new_key,
                description=f"Update KeyCode: {old_key} to {new_key}"
            ))
        
        # Make import transformations robust against nested imports.
        reflect_modules = {
            "ReflectComponent": "component",
            "ReflectResource": "resource",
            "ReflectAsset": "asset",
            "ReflectFromPtr": "from_ptr",
            "ReflectPath": "path",
            "ReflectMap": "map",
            "ReflectTuple": "tuple",
            "ReflectStruct": "struct",
            "ReflectEnum": "enum",
            "ReflectList": "list",
            "ReflectArray": "array",
            "ReflectAtomic": "atomic",
            "ReflectTupleStruct": "tuple_struct",
            "ReflectOpaque": "opaque",
            "Reflect": "reflect",
        }
        
        for item, mod in reflect_modules.items():
            transformations.append(self.create_transformation(
                pattern=f"bevy_reflect::{item}",
                replacement=f"bevy_reflect::{mod}::{item}",
                description=f"{item} path change to bevy_reflect::{mod}"
            ))
        
        # 26. WindowMoved entity to window
        transformations.append(self.create_transformation(
            pattern="$EVENT.entity",
            replacement="$EVENT.window",
            description="Rename WindowMoved::entity to window (context-sensitive)"
        ))
        
        # ===== UTILS & OTHER CHANGES =====
        
        # 27. EntityHash imports moved to bevy_ecs
        transformations.append(self.create_transformation(
            pattern="bevy::utils::EntityHash",
            replacement="bevy::ecs::entity::hash::EntityHash",
            description="Update EntityHash path to bevy_ecs"
        ))
        
        transformations.append(self.create_transformation(
            pattern="bevy::utils::EntityHasher",
            replacement="bevy::ecs::entity::hash::EntityHasher",
            description="Update EntityHasher import to bevy_ecs"
        ))
        
        transformations.append(self.create_transformation(
            pattern="bevy::utils::EntityHashMap",
            replacement="bevy::ecs::entity::hash::EntityHashMap",
            description="Update EntityHashMap import to bevy_ecs"
        ))
        
        transformations.append(self.create_transformation(
            pattern="bevy::utils::EntityHashSet",
            replacement="bevy::ecs::entity::hash::EntityHashSet",
            description="Update EntityHashSet import to bevy_ecs"
        ))
        
        # 28. TypeUuid to TypePath
        transformations.append(self.create_transformation(
            pattern="#[derive(TypeUuid)]",
            replacement="#[derive(TypePath)]",
            description="Replace TypeUuid derive with TypePath"
        ))
        
        # 29. Accessibility plugin rename
        transformations.append(self.create_transformation(
            pattern="bevy_winit::AccessibilityPlugin",
            replacement="bevy_winit::AccessKitPlugin",
            description="Rename AccessibilityPlugin to AccessKitPlugin"
        ))
        
        # 30. NonSendMarker moved to bevy_core
        transformations.append(self.create_transformation(
            pattern="bevy::render::view::NonSendMarker",
            replacement="bevy::core::NonSendMarker",
            description="Update NonSendMarker path to bevy_core"
        ))
        
        transformations.append(self.create_transformation(
            pattern="bevy::render::view::window::NonSendMarker",
            replacement="bevy::core::NonSendMarker",
            description="Update window::NonSendMarker path to bevy_core"
        ))
        
        # 31. futures_lite re-export
        transformations.append(self.create_transformation(
            pattern="use futures_lite::$PATH",
            replacement="use bevy::tasks::futures_lite::$PATH",
            description="Update futures_lite import to bevy::tasks"
        ))
        
        # 32. RunFixedUpdateLoop to RunFixedMainLoop
        transformations.append(self.create_transformation(
            pattern="RunFixedUpdateLoop",
            replacement="RunFixedMainLoop",
            description="Rename RunFixedUpdateLoop to RunFixedMainLoop"
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
            self.logger.info("Executing pre-migration steps for 0.12 -> 0.13")
            
            # Check for common 0.12 patterns
            rust_files = self.file_manager.find_rust_files()
            
            # Look for files using Input<T> (will become ButtonInput<T>)
            input_files = []
            for file_path in rust_files:
                content = self.file_manager.read_file_content(file_path)
                if content and re.search(r'\bInput<', content):
                    input_files.append(file_path)
            
            if input_files:
                self.logger.info(f"Found {len(input_files)} files using Input<T> (will be renamed to ButtonInput<T>)")
            
            # Look for WorldQuery usage
            world_query_files = []
            for file_path in rust_files:
                content = self.file_manager.read_file_content(file_path)
                if content and re.search(r'#\[derive\(WorldQuery\)\]', content):
                    world_query_files.append(file_path)
            
            if world_query_files:
                self.logger.info(f"Found {len(world_query_files)} files using WorldQuery derive (will be split into QueryData/QueryFilter)")
                # Backup these files as they need significant changes
                if not self.backup_files(world_query_files):
                    self.logger.warning("Some WorldQuery files could not be backed up")
            
            # Look for deprecated shape usage
            shape_files = self.find_files_with_pattern("shape::")
            if shape_files:
                self.logger.info(f"Found {len(shape_files)} files using deprecated shape types")
            
            # Look for TextureAtlas usage
            atlas_files = self.find_files_with_pattern("TextureAtlas")
            if atlas_files:
                self.logger.info(f"Found {len(atlas_files)} files using TextureAtlas (major rework in 0.13)")
                self.logger.warning("TextureAtlas has been significantly reworked - manual review recommended")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        """
        Execute steps after applying transformations
        
        Args:
            result: The migration result from transformation application
            
        Returns:
            True if post-migration steps were successful, False otherwise
        """
        try:
            self.logger.info("Executing post-migration steps for 0.12 -> 0.13")
            
            # Check for patterns that need manual review
            self._check_for_manual_migration_needed()
            
            # Validate migration
            if not self._validate_migration_patterns():
                self.logger.warning("Some migration patterns may need manual review")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    

    
    def _check_for_manual_migration_needed(self) -> None:
        """Check for patterns that might need manual migration"""
        try:
            # Patterns that need manual attention in 0.13
            manual_patterns = [
                ("TextureAtlasSprite", "TextureAtlasSprite removed - needs manual conversion to Sprite + TextureAtlas"),
                ("UiTextureAtlasImage", "UiTextureAtlasImage removed - use AtlasImageBundle instead"),
                ("Events::send", "Event send methods now return EventId - may need to handle return value"),
                ("EntityCommands<'w, 's, 'a>", "EntityCommands lifetimes simplified - update to EntityCommands<'a>"),
                ("Query::get_component", "Query::get_component deprecated - use Query::get with tuple destructuring"),
                ("ViewTarget::get_color_attachment", "ViewTarget methods signature changed - remove arguments"),
                ("Camera3d", "ClearColor moved from Camera3d to Camera component"),
                ("PreparedMaterial2d", "PreparedMaterial2d now has depth_bias field"),
                ("RenderPassDescriptor", "RenderPassDescriptor now uses StoreOp enum instead of boolean"),
                ("create_bind_group_layout", "create_bind_group_layout signature changed - provide parameters separately"),
                ("@group(1)", "Material and mesh bind groups swapped - materials now use @group(2)"),
                ("Exposure", "New Exposure component affects lighting - may need to adjust light intensities"),
                ("RenderAssetUsages", "Mesh and Image now require asset_usage field"),
                ("AspectRatio", "AspectRatio is now a struct, not f32"),
                ("ReceivedCharacter", "ReceivedCharacter.char is now SmolStr - use .chars().last()"),
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
                (r'\bInput<', "Input<T> should be ButtonInput<T>"),
                (r'#\[derive\(WorldQuery\)\]', "WorldQuery derive should be QueryData or QueryFilter"),
                (r'\.add_state\(', "add_state should be init_state"),
                (r'\bTextAlignment\b', "TextAlignment should be JustifyText"),
            ]
            
            for pattern, message in old_patterns:
                files_with_old_pattern = []
                for file_path in rust_files:
                    content = self.file_manager.read_file_content(file_path)
                    if content and re.search(pattern, content):
                        files_with_old_pattern.append(file_path)
                
                if files_with_old_pattern:
                    self.logger.warning(f"Old pattern still found: {message}")
                    self.logger.warning(f"Found in {len(files_with_old_pattern)} files")
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
            # Check that we're actually migrating from 0.12
            cargo_toml_path = self.project_path / "Cargo.toml"
            if cargo_toml_path.exists():
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                # Look for Bevy 0.12 dependency
                if re.search(r'bevy\s*=\s*["\']0\.12', content):
                    self.logger.info("Confirmed Bevy 0.12 dependency in Cargo.toml")
                elif re.search(r'bevy\s*=.*version\s*=\s*["\']0\.12', content):
                    self.logger.info("Confirmed Bevy 0.12 dependency in Cargo.toml")
                else:
                    self.logger.warning("Could not confirm Bevy 0.12 dependency in Cargo.toml")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False
