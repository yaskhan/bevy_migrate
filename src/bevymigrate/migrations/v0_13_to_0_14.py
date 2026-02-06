"""
Migration from Bevy 0.13 to 0.14
Handles the migration of Bevy projects from version 0.13 to 0.14
"""

import logging
import re
from pathlib import Path
from typing import List

from bevymigrate.migrations.base_migration import BaseMigration, MigrationResult
from bevymigrate.core.ast_processor import ASTTransformation


class Migration_0_13_to_0_14(BaseMigration):
    """
    Migration class for upgrading Bevy projects from version 0.13 to 0.14
    
    Key changes in Bevy 0.14:
    - Complete Color overhaul with Srgba/LinearRgba
    - Animation graph system
    - SubApp separation from App
    - ECS observers and state system moves
    - Dir2/Dir3 renames for directions
    - Massive rendering changes (binned/sorted phases, matrix naming)
    - winit 0.30 and wgpu 0.20 updates
    - Many breaking API changes across all systems
    """
    
    @property
    def from_version(self) -> str:
        """Source Bevy version for this migration"""
        return "0.13"
    
    @property
    def to_version(self) -> str:
        """Target Bevy version for this migration"""
        return "0.14"
    
    @property
    def description(self) -> str:
        """Human-readable description of this migration"""
        return "Migrate Bevy project from version 0.13 to 0.14 - Major color, rendering, ECS, and API overhaul"
    
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for migrating from 0.13 to 0.14
        
        Returns:
            List of ASTTransformation objects
        """
        transformations = []
        
        # ===== ANIMATION CHANGES =====
        
        # 1. NoOpTypeIdHash to NoOpHash
        transformations.append(self.create_transformation(
            pattern="NoOpTypeIdHash",
            replacement="NoOpHash",
            description="Rename NoOpTypeIdHash to NoOpHash"
        ))
        
        transformations.append(self.create_transformation(
            pattern="NoOpTypeIdHasher",
            replacement="NoOpHasher",
            description="Rename NoOpTypeIdHasher to NoOpHasher"
        ))
        
        # ===== APP CHANGES =====
        
        # 2. App::world property to method
        transformations.append(self.create_transformation(
            pattern="$APP.world.id()",
            replacement="$APP.world().id()",
            description="Change App::world property to world() method"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$APP.world.spawn($BUNDLE)",
            replacement="$APP.world_mut().spawn($BUNDLE)",
            description="Change App::world to world_mut() for mutations"
        ))
        
        # 3. AppExit to enum
        transformations.append(self.create_transformation(
            pattern="writer.send(AppExit)",
            replacement="writer.send(AppExit::Success)",
            description="Update AppExit to AppExit::Success"
        ))
        
        # 4. State initialization import
        transformations.append(self.create_transformation(
            pattern="use bevy::app::App",
            replacement="use bevy::app::App;\nuse bevy::state::app::AppExtStates as _",
            description="Add AppExtStates import for init_state"
        ))
        
        # ===== ASSETS CHANGES =====
        
        # 5. UpdateAssets schedule to PreUpdate
        transformations.append(self.create_transformation(
            pattern=".add_systems(UpdateAssets, $SYSTEM)",
            replacement=".add_systems(PreUpdate, $SYSTEM)",
            description="Replace UpdateAssets schedule with PreUpdate"
        ))
        
        # 6. AssetEvents schedule to First set
        transformations.append(self.create_transformation(
            pattern=".add_systems(AssetEvents, $SYSTEM)",
            replacement=".add_systems(First, $SYSTEM.in_set(AssetEvents))",
            description="Replace AssetEvents schedule with First set"
        ))
        
        # 7. Handle::into() to Handle::id()
        transformations.append(self.create_transformation(
            pattern="let $VAR: AssetId<$TYPE> = $HANDLE.into()",
            replacement="let $VAR = $HANDLE.id()",
            description="Replace Handle::into() with Handle::id()"
        ))
        
        # 8. LoadState::Failed with error
        transformations.append(self.create_transformation(
            pattern="LoadState::Failed =>",
            replacement="LoadState::Failed(error) =>",
            description="Add error parameter to LoadState::Failed"
        ))
        
        # 9. AssetMetaCheck resource to plugin field
        transformations.append(self.create_transformation(
            pattern=".insert_resource(AssetMetaCheck::$VARIANT)",
            replacement=".add_plugins(DefaultPlugins.set(AssetPlugin { meta_check: AssetMetaCheck::$VARIANT, ..default() }))",
            description="Move AssetMetaCheck from resource to AssetPlugin field"
        ))
        
        # 10. LoadContext builder pattern
        transformations.append(self.create_transformation(
            pattern="load_context.load_direct($PATH)",
            replacement="load_context.loader().direct().untyped().load($PATH)",
            description="Update load_direct to builder pattern"
        ))
        
        transformations.append(self.create_transformation(
            pattern="load_context.load_untyped($PATH)",
            replacement="load_context.loader().untyped().load($PATH)",
            description="Update load_untyped to builder pattern"
        ))
        
        transformations.append(self.create_transformation(
            pattern="load_context.load_with_settings($PATH, $SETTINGS)",
            replacement="load_context.loader().with_settings($SETTINGS).load($PATH)",
            description="Update load_with_settings to builder pattern"
        ))
        
        # ===== COLOR CHANGES (MAJOR) =====
        
        # 11. Color::Rgba to Color::Srgba
        transformations.append(self.create_transformation(
            pattern="Color::Rgba { $FIELDS }",
            replacement="Color::Srgba(Srgba { $FIELDS })",
            description="Update Color::Rgba to Color::Srgba"
        ))
        
        # 12. Color::rgb to Color::srgb
        transformations.append(self.create_transformation(
            pattern="Color::rgb($R, $G, $B)",
            replacement="Color::srgb($R, $G, $B)",
            description="Rename Color::rgb to Color::srgb"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Color::rgba($R, $G, $B, $A)",
            replacement="Color::srgba($R, $G, $B, $A)",
            description="Rename Color::rgba to Color::srgba"
        ))
        
        # 13. Color::rgb_u8 to Color::srgb_u8
        transformations.append(self.create_transformation(
            pattern="Color::rgb_u8($R, $G, $B)",
            replacement="Color::srgb_u8($R, $G, $B)",
            description="Rename Color::rgb_u8 to Color::srgb_u8"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Color::rgba_u8($R, $G, $B, $A)",
            replacement="Color::srgba_u8($R, $G, $B, $A)",
            description="Rename Color::rgba_u8 to Color::srgba_u8"
        ))
        
        # 14. Color::linear_rgb and linear_rgba
        transformations.append(self.create_transformation(
            pattern="Color::rgb_linear($R, $G, $B)",
            replacement="Color::linear_rgb($R, $G, $B)",
            description="Rename Color::rgb_linear to Color::linear_rgb"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Color::rgba_linear($R, $G, $B, $A)",
            replacement="Color::linear_rgba($R, $G, $B, $A)",
            description="Rename Color::rgba_linear to Color::linear_rgba"
        ))
        
        # 15. Color alpha methods
        transformations.append(self.create_transformation(
            pattern="$COLOR.set_a($ALPHA)",
            replacement="$COLOR.set_alpha($ALPHA)",
            description="Rename Color::set_a to set_alpha"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$COLOR.with_a($ALPHA)",
            replacement="$COLOR.with_alpha($ALPHA)",
            description="Rename Color::with_a to with_alpha"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$COLOR.a()",
            replacement="$COLOR.alpha()",
            description="Rename Color::a() to alpha()"
        ))
        
        # 16. ColorAttachment with LinearRgba
        transformations.append(self.create_transformation(
            pattern="ColorAttachment::new(Some($COLOR))",
            replacement="ColorAttachment::new(Some($COLOR.into()))",
            description="Convert Color to LinearRgba in ColorAttachment"
        ))
        
        # ===== ECS CHANGES =====
        
        # 17. Event derive auto-implements Component
        transformations.append(self.create_transformation(
            pattern="#[derive(Event, Component)]",
            replacement="#[derive(Event)]",
            description="Remove Component from Event derive (auto-implemented)"
        ))
        
        # 18. Command and CommandQueue imports
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::system::Command",
            replacement="use bevy::ecs::world::Command",
            description="Move Command import to bevy::ecs::world"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::system::CommandQueue",
            replacement="use bevy::ecs::world::CommandQueue",
            description="Move CommandQueue import to bevy::ecs::world"
        ))
        
        # 19. Component::Storage to STORAGE_TYPE constant
        transformations.append(self.create_transformation(
            pattern="type Storage = TableStorage",
            replacement="const STORAGE_TYPE: StorageType = StorageType::Table",
            description="Replace Component::Storage with STORAGE_TYPE constant"
        ))
        
        transformations.append(self.create_transformation(
            pattern="type Storage = SparseStorage",
            replacement="const STORAGE_TYPE: StorageType = StorageType::SparseSet",
            description="Replace SparseStorage with StorageType::SparseSet"
        ))
        
        # 20. Event registration
        transformations.append(self.create_transformation(
            pattern="world.insert_resource(Events::<$EVENT>::default())",
            replacement="EventRegistry::register_event::<$EVENT>(&mut world)",
            description="Use EventRegistry for event registration"
        ))
        
        # 21. SystemId to entity conversion
        transformations.append(self.create_transformation(
            pattern="Entity::from($SYSTEM_ID)",
            replacement="$SYSTEM_ID.entity()",
            description="Use SystemId::entity() instead of Entity::from"
        ))
        
        # 22. NextState enum variants
        transformations.append(self.create_transformation(
            pattern="NextState(Some($STATE))",
            replacement="NextState::Pending($STATE)",
            description="Update NextState(Some(s)) to NextState::Pending(s)"
        ))
        
        transformations.append(self.create_transformation(
            pattern="NextState(None)",
            replacement="NextState::Unchanged",
            description="Update NextState(None) to NextState::Unchanged"
        ))
        
        # 23. State imports moved
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::schedule::NextState",
            replacement="use bevy::state::state::NextState",
            description="Move NextState import to bevy::state::state"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::schedule::OnEnter",
            replacement="use bevy::state::state::OnEnter",
            description="Move OnEnter import to bevy::state::state"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::schedule::OnExit",
            replacement="use bevy::state::state::OnExit",
            description="Move OnExit import to bevy::state::state"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::schedule::State",
            replacement="use bevy::state::state::State",
            description="Move State import to bevy::state::state"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::schedule::States",
            replacement="use bevy::state::state::States",
            description="Move States import to bevy::state::state"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::schedule::common_conditions::in_state",
            replacement="use bevy::state::condition::in_state",
            description="Move in_state import to bevy::state::condition"
        ))
        
        # 24. StateTransitionEvent fields
        transformations.append(self.create_transformation(
            pattern="$EVENT.before",
            replacement="$EVENT.exited",
            description="Rename StateTransitionEvent::before to exited"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$EVENT.after",
            replacement="$EVENT.entered",
            description="Rename StateTransitionEvent::after to entered"
        ))
        
        # 25. Label and intern module moves
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::label",
            replacement="use bevy::ecs::label",
            description="Move label module to bevy::ecs"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::intern",
            replacement="use bevy::ecs::intern",
            description="Move intern module to bevy::ecs"
        ))
        
        # ===== GIZMOS CHANGES =====
        
        # 26. Gizmo segments to resolution
        transformations.append(self.create_transformation(
            pattern="$GIZMO.segments($COUNT)",
            replacement="$GIZMO.resolution($COUNT)",
            description="Rename gizmo segments() to resolution()"
        ))
        
        # 27. Gizmo primitives take references
        transformations.append(self.create_transformation(
            pattern="gizmos.primitive_2d($PRIM, $POS, $ROT, $COLOR)",
            replacement="gizmos.primitive_2d(&$PRIM, $POS, $ROT, $COLOR)",
            description="Pass primitive as reference to primitive_2d"
        ))
        
        transformations.append(self.create_transformation(
            pattern="gizmos.primitive_3d($PRIM, $POS, $ROT, $COLOR)",
            replacement="gizmos.primitive_3d(&$PRIM, $POS, $ROT, $COLOR)",
            description="Pass primitive as reference to primitive_3d"
        ))
        
        # 28. insert_gizmo_group to insert_gizmo_config
        transformations.append(self.create_transformation(
            pattern="$APP.insert_gizmo_group($CONFIG)",
            replacement="$APP.insert_gizmo_config($CONFIG)",
            description="Rename insert_gizmo_group to insert_gizmo_config"
        ))
        
        # ===== INPUT CHANGES =====
        
        # 29. Touchpad to gesture renames
        transformations.append(self.create_transformation(
            pattern="use bevy::input::touchpad",
            replacement="use bevy::input::gestures",
            description="Rename touchpad module to gestures"
        ))
        
        transformations.append(self.create_transformation(
            pattern="TouchpadMagnify",
            replacement="PinchGesture",
            description="Rename TouchpadMagnify to PinchGesture"
        ))
        
        transformations.append(self.create_transformation(
            pattern="TouchpadRotate",
            replacement="RotationGesture",
            description="Rename TouchpadRotate to RotationGesture"
        ))
        
        # ===== MATH CHANGES =====
        
        # 30. Direction2d/3d to Dir2/3
        transformations.append(self.create_transformation(
            pattern="use bevy::math::primitives::Direction2d",
            replacement="use bevy::math::Dir2",
            description="Move Direction2d to bevy::math::Dir2"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::math::primitives::Direction3d",
            replacement="use bevy::math::Dir3",
            description="Move Direction3d to bevy::math::Dir3"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Direction2d",
            replacement="Dir2",
            description="Rename Direction2d to Dir2"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Direction3d",
            replacement="Dir3",
            description="Rename Direction3d to Dir3"
        ))
        
        # 31. Plane3d split
        transformations.append(self.create_transformation(
            pattern="Plane3d::new($NORMAL)",
            replacement="InfinitePlane3d::new($NORMAL)",
            description="Use InfinitePlane3d for infinite planes"
        ))
        
        # 32. Transform rotation with Dir3
        transformations.append(self.create_transformation(
            pattern="$TRANSFORM.rotate_axis(Vec3::$AXIS, $ANGLE)",
            replacement="$TRANSFORM.rotate_axis(Dir3::$AXIS, $ANGLE)",
            description="Use Dir3 for Transform::rotate_axis"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$TRANSFORM.rotate_local_axis(Vec3::$AXIS, $ANGLE)",
            replacement="$TRANSFORM.rotate_local_axis(Dir3::$AXIS, $ANGLE)",
            description="Use Dir3 for Transform::rotate_local_axis"
        ))
        
        # 33. FloatOrd move
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::FloatOrd",
            replacement="use bevy::math::FloatOrd",
            description="Move FloatOrd to bevy::math"
        ))
        
        # ===== REFLECTION CHANGES =====
        
        # 34. UntypedReflectDeserializer rename
        transformations.append(self.create_transformation(
            pattern="UntypedReflectDeserializer",
            replacement="ReflectDeserializer",
            description="Rename UntypedReflectDeserializer to ReflectDeserializer"
        ))
        
        # 35. DynamicScene::serialize_ron to serialize
        transformations.append(self.create_transformation(
            pattern="$SCENE.serialize_ron($REGISTRY)",
            replacement="$SCENE.serialize(&$REGISTRY.read())",
            description="Rename serialize_ron to serialize with TypeRegistry"
        ))
        
        # ===== RENDERING CHANGES =====
        
        # 36. Camera3dBundle::dither to deband_dither
        transformations.append(self.create_transformation(
            pattern="Camera3dBundle { dither: $VALUE, $REST }",
            replacement="Camera3dBundle { deband_dither: $VALUE, $REST }",
            description="Rename Camera3dBundle::dither to deband_dither"
        ))
        
        # 37. AlphaMode import move
        transformations.append(self.create_transformation(
            pattern="use bevy::pbr::AlphaMode",
            replacement="use bevy::render::alpha::AlphaMode",
            description="Move AlphaMode to bevy::render::alpha"
        ))
        
        # 38. GpuArrayBufferIndex::index type change
        transformations.append(self.create_transformation(
            pattern="$VAR.index.get()",
            replacement="$VAR.index",
            description="GpuArrayBufferIndex::index is now u32"
        ))
        
        # 39. Mesh::merge takes reference
        transformations.append(self.create_transformation(
            pattern="$MESH.merge($OTHER_MESH)",
            replacement="$MESH.merge(&$OTHER_MESH)",
            description="Mesh::merge now takes &Mesh reference"
        ))
        
        # 40. TextureAtlasBuilder::finish to build
        transformations.append(self.create_transformation(
            pattern="$BUILDER.finish()",
            replacement="$BUILDER.build()",
            description="Rename TextureAtlasBuilder::finish to build"
        ))
        
        # 41. SpriteSheetBundle deprecation
        transformations.append(self.create_transformation(
            pattern="SpriteSheetBundle { texture: $TEX, atlas: $ATLAS, $REST }",
            replacement="(SpriteBundle { texture: $TEX, $REST }, $ATLAS)",
            description="Replace SpriteSheetBundle with SpriteBundle + TextureAtlas"
        ))
        
        # 42. AtlasImageBundle deprecation
        transformations.append(self.create_transformation(
            pattern="AtlasImageBundle { image: $IMG, atlas: $ATLAS, $REST }",
            replacement="(ImageBundle { image: $IMG, $REST }, $ATLAS)",
            description="Replace AtlasImageBundle with ImageBundle + TextureAtlas"
        ))
        
        # 43. BufferVec to RawBufferVec
        transformations.append(self.create_transformation(
            pattern="BufferVec<$TYPE>",
            replacement="RawBufferVec<$TYPE>",
            description="Rename BufferVec to RawBufferVec for Pod types"
        ))
        
        # 44. Matrix naming - projection_matrix to clip_from_view
        transformations.append(self.create_transformation(
            pattern="$VAR.projection_matrix",
            replacement="$VAR.clip_from_view",
            description="Rename projection_matrix to clip_from_view"
        ))
        
        transformations.append(self.create_transformation(
            pattern="get_projection_matrix()",
            replacement="get_clip_from_view()",
            description="Rename get_projection_matrix to get_clip_from_view"
        ))
        
        # 45. Matrix naming - transform to world_from_local
        transformations.append(self.create_transformation(
            pattern="MeshUniform { transform: $TRANSFORM, $REST }",
            replacement="MeshUniform { world_from_local: $TRANSFORM, $REST }",
            description="Rename MeshUniform::transform to world_from_local"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$UNIFORM.previous_transform",
            replacement="$UNIFORM.previous_world_from_local",
            description="Rename previous_transform to previous_world_from_local"
        ))
        
        # 46. Node2d::MainPass split
        transformations.append(self.create_transformation(
            pattern="Node2d::MainPass",
            replacement="Node2d::StartMainPass",
            description="Replace Node2d::MainPass with StartMainPass (check context)"
        ))
        
        # ===== TASKS CHANGES =====
        
        # 47. Parallel iteration with index
        transformations.append(self.create_transformation(
            pattern="par_chunk_map($POOL, $SIZE, |$CHUNK|",
            replacement="par_chunk_map($POOL, $SIZE, |_index, $CHUNK|",
            description="Add index parameter to par_chunk_map closure"
        ))
        
        transformations.append(self.create_transformation(
            pattern="par_splat_map($POOL, |$ITEM|",
            replacement="par_splat_map($POOL, |_index, $ITEM|",
            description="Add index parameter to par_splat_map closure"
        ))
        
        transformations.append(self.create_transformation(
            pattern="par_chunk_map_mut($POOL, $SIZE, |$CHUNK|",
            replacement="par_chunk_map_mut($POOL, $SIZE, |_index, $CHUNK|",
            description="Add index parameter to par_chunk_map_mut closure"
        ))
        
        transformations.append(self.create_transformation(
            pattern="par_splat_map_mut($POOL, |$ITEM|",
            replacement="par_splat_map_mut($POOL, |_index, $ITEM|",
            description="Add index parameter to par_splat_map_mut closure"
        ))
        
        # ===== UI CHANGES =====
        
        # 48. Rect::inset to inflate
        transformations.append(self.create_transformation(
            pattern="$RECT.inset($VALUE)",
            replacement="$RECT.inflate($VALUE)",
            description="Rename Rect::inset to inflate"
        ))
        
        transformations.append(self.create_transformation(
            pattern="IRect::inset($VALUE)",
            replacement="IRect::inflate($VALUE)",
            description="Rename IRect::inset to inflate"
        ))
        
        transformations.append(self.create_transformation(
            pattern="URect::inset($VALUE)",
            replacement="URect::inflate($VALUE)",
            description="Rename URect::inset to inflate"
        ))
        
        # ===== WINDOWING CHANGES =====
        
        # 49. need_new_surfaces to need_surface_configuration
        transformations.append(self.create_transformation(
            pattern="need_new_surfaces()",
            replacement="need_surface_configuration()",
            description="Rename need_new_surfaces to need_surface_configuration"
        ))
        
        # 50. ApplicationLifecycle to AppLifecycle
        transformations.append(self.create_transformation(
            pattern="ApplicationLifecycle",
            replacement="AppLifecycle",
            description="Rename ApplicationLifecycle to AppLifecycle"
        ))
        
        # 51. UpdateMode changes
        transformations.append(self.create_transformation(
            pattern="UpdateMode::Reactive",
            replacement="UpdateMode::reactive()",
            description="UpdateMode::Reactive is now a method"
        ))
        
        transformations.append(self.create_transformation(
            pattern="UpdateMode::ReactiveLowPower",
            replacement="UpdateMode::reactive_low_power()",
            description="UpdateMode::ReactiveLowPower is now a method"
        ))
        
        # ===== OTHER CHANGES =====
        
        # 52. Node2D typo fix
        transformations.append(self.create_transformation(
            pattern="Node2D::ConstrastAdaptiveSharpening",
            replacement="Node2D::ContrastAdaptiveSharpening",
            description="Fix Node2D::ConstrastAdaptiveSharpening typo"
        ))
        
        # 53. Access::grow removal (automatic now)
        transformations.append(self.create_transformation(
            pattern="$ACCESS.grow($SIZE);",
            replacement="// Access now grows automatically",
            description="Remove Access::grow (now automatic)"
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
            "**/*.wgsl",         # Shader files (for WGSL changes)
            "Cargo.toml"         # Cargo manifest for dependency updates
        ]
    
    def pre_migration_steps(self) -> bool:
        """
        Execute steps before applying transformations
        
        Returns:
            True if pre-migration steps were successful, False otherwise
        """
        try:
            self.logger.info("Executing pre-migration steps for 0.13 -> 0.14")
            
            rust_files = self.file_manager.find_rust_files()
            
            # Check for Color usage (major change)
            color_files = self.find_files_with_pattern("Color::")
            if color_files:
                self.logger.warning(f"Found {len(color_files)} files using Color - MAJOR API changes in 0.14!")
                self.logger.warning("Color::Rgba -> Color::Srgba, Color::rgb -> Color::srgb, etc.")
            
            # Check for Direction2d/3d usage
            direction_files = self.find_files_with_pattern("Direction")
            if direction_files:
                self.logger.info(f"Found {len(direction_files)} files using Direction types (will rename to Dir2/Dir3)")
            
            # Check for state usage
            state_files = self.find_files_with_pattern("bevy::ecs::schedule::State")
            if state_files:
                self.logger.info(f"Found {len(state_files)} files with state imports (moved to bevy::state)")
            
            # Check for App::world property usage
            app_world_files = []
            for file_path in rust_files:
                content = self.file_manager.read_file_content(file_path)
                if content and re.search(r'\.world\.', content):
                    app_world_files.append(file_path)
            
            if app_world_files:
                self.logger.info(f"Found {len(app_world_files)} files using App::world property (now methods)")
            
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
            self.logger.info("Executing post-migration steps for 0.13 -> 0.14")
            
            # Update Cargo.toml dependencies
            if not self._update_cargo_dependencies():
                self.logger.warning("Failed to update Cargo.toml dependencies")
            
            # Check for patterns that need manual review
            self._check_for_manual_migration_needed()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def _update_cargo_dependencies(self) -> bool:
        """Update Cargo.toml to use Bevy 0.14"""
        try:
            cargo_toml_path = self.project_path / "Cargo.toml"
            if not cargo_toml_path.exists():
                self.logger.warning("Cargo.toml not found")
                return False
            
            if self.dry_run:
                self.logger.info("Would update Cargo.toml to Bevy 0.14 (dry run)")
                return True
            
            content = cargo_toml_path.read_text(encoding='utf-8')
            
            # Update bevy dependency version
            patterns = [
                (r'(bevy\s*=\s*")[^"]*(")', r'\g<1>0.14\g<2>'),
                (r'(bevy\s*=\s*\{\s*version\s*=\s*")[^"]*(")', r'\g<1>0.14\g<2>'),
            ]
            
            updated = False
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    updated = True
            
            if updated:
                cargo_toml_path.write_text(content, encoding='utf-8')
                self.logger.info("Updated Cargo.toml to Bevy 0.14")
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
            manual_patterns = [
                ("AnimationPlayer::play(", "AnimationPlayer now requires AnimationGraph - manual setup needed"),
                ("Color::r()", "Color channel getters removed - convert to specific color space first"),
                ("Color::set_r(", "Color channel setters removed - convert to specific color space first"),
                ("Color * f32", "Color arithmetic removed - use LinearRgba explicitly"),
                ("RenderPhase<", "RenderPhase moved to resources - use ViewSortedRenderPhases/ViewBinnedRenderPhases"),
                ("PhaseItem", "PhaseItem split into BinnedPhaseItem and SortedPhaseItem"),
                ("WorldCell", "WorldCell removed - use SystemState or UnsafeWorldCell"),
                ("ReceivedCharacter", "ReceivedCharacter deprecated - use KeyboardInput with Key::Character"),
                ("DynamicPlugin", "Dynamic plugins deprecated - compile into main binary"),
                ("close_on_esc", "close_on_esc system removed - implement custom or use OS keybinds"),
                ("SpriteSheetBundle", "SpriteSheetBundle deprecated - use SpriteBundle + TextureAtlas"),
                ("AtlasImageBundle", "AtlasImageBundle deprecated - use ImageBundle + TextureAtlas"),
                ("Color::BLUE", "Color constants moved to bevy::color::palettes::css"),
                ("App::run()", "App::run() now returns AppExit - consider returning from main"),
                ("SubApp::new(", "SubApp construction changed - use SubApp::new() and set_extract()"),
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
    
    def validate_preconditions(self) -> bool:
        """
        Validate that preconditions for this migration are met
        
        Returns:
            True if preconditions are met, False otherwise
        """
        if not super().validate_preconditions():
            return False
        
        try:
            # Check that we're actually migrating from 0.13
            cargo_toml_path = self.project_path / "Cargo.toml"
            if cargo_toml_path.exists():
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                # Look for Bevy 0.13 dependency
                if re.search(r'bevy\s*=\s*["\']0\.13', content):
                    self.logger.info("Confirmed Bevy 0.13 dependency in Cargo.toml")
                elif re.search(r'bevy\s*=.*version\s*=\s*["\']0\.13', content):
                    self.logger.info("Confirmed Bevy 0.13 dependency in Cargo.toml")
                else:
                    self.logger.warning("Could not confirm Bevy 0.13 dependency in Cargo.toml")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False
