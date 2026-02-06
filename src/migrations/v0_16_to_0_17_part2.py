"""
Migration from Bevy 0.16 to 0.17 - Part 2
bevy_render Reorganization and System Set Renames

This is Part 2 of 3 for the Bevy 0.16 to 0.17 migration.
Run parts in order: Part 1 → Part 2 → Part 3
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Callable

from migrations.base_migration import BaseMigration, MigrationResult
from core.ast_processor import ASTTransformation


class Migration_0_16_to_0_17_Part2(BaseMigration):
    """
    Migration Part 2: bevy_render Reorganization & System Set Renames

    Key changes in this part:
    - Rendering types moved to new crates (bevy_camera, bevy_shader, bevy_light, etc.)
    - System sets renamed with *Systems suffix
    - Anti-aliasing and post-processing moved
    - UI rendering separated
    """

    @property
    def from_version(self) -> str:
        return "0.17-part1"

    @property
    def to_version(self) -> str:
        return "0.17-part2"

    @property
    def description(self) -> str:
        return "Bevy 0.16 → 0.17 Part 2: bevy_render reorganization, System Set renames (~50 transformations)"

    def get_transformations(self) -> List[ASTTransformation]:
        transformations = []

        # ===== BEVY_RENDER REORGANIZATION (25 transformations) =====

        # Camera types moved to bevy_camera
        transformations.append(self.create_transformation(
            pattern="use bevy::render::camera",
            replacement="use bevy::camera",
            description="Camera types moved to bevy_camera"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy_render::camera",
            replacement="use bevy_camera",
            description="Camera types moved to bevy_camera crate"
        ))

        # Visibility types moved to bevy_camera::visibility
        transformations.append(self.create_transformation(
            pattern="use bevy::render::view::visibility",
            replacement="use bevy::camera::visibility",
            description="Visibility types moved to bevy_camera::visibility"
        ))

        # Shader types moved to bevy_shader
        transformations.append(self.create_transformation(
            pattern="use bevy::render::render_resource::Shader",
            replacement="use bevy::shader::Shader",
            description="Shader types moved to bevy_shader"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy_render::render_resource::Shader",
            replacement="use bevy_shader::Shader",
            description="Shader moved to bevy_shader crate"
        ))

        # Light types moved to bevy_light
        transformations.append(self.create_transformation(
            pattern="use bevy::pbr::PointLight",
            replacement="use bevy::light::PointLight",
            description="Light types moved to bevy_light"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy::pbr::DirectionalLight",
            replacement="use bevy::light::DirectionalLight",
            description="DirectionalLight moved to bevy_light"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy::pbr::SpotLight",
            replacement="use bevy::light::SpotLight",
            description="SpotLight moved to bevy_light"
        ))

        # Mesh types moved to bevy_mesh
        transformations.append(self.create_transformation(
            pattern="use bevy::render::mesh",
            replacement="use bevy::mesh",
            description="Mesh types moved to bevy_mesh"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy_render::mesh",
            replacement="use bevy_mesh",
            description="Mesh moved to bevy_mesh crate"
        ))

        # Image types moved to bevy_image
        transformations.append(self.create_transformation(
            pattern="use bevy::render::texture::Image",
            replacement="use bevy::image::Image",
            description="Image types moved to bevy_image"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy_render::texture::Image",
            replacement="use bevy_image::Image",
            description="Image moved to bevy_image crate"
        ))

        # UI rendering moved to bevy_ui_render
        transformations.append(self.create_transformation(
            pattern="use bevy::ui::render",
            replacement="use bevy::ui_render",
            description="UI rendering moved to bevy_ui_render"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy_ui::render",
            replacement="use bevy_ui_render",
            description="UI rendering moved to bevy_ui_render crate"
        ))

        # Sprite rendering moved to bevy_sprite_render
        transformations.append(self.create_transformation(
            pattern="use bevy::sprite::Material2d",
            replacement="use bevy::sprite_render::Material2d",
            description="Sprite rendering moved to bevy_sprite_render"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy_sprite::Material2d",
            replacement="use bevy_sprite_render::Material2d",
            description="Material2d moved to bevy_sprite_render"
        ))

        # Anti-aliasing moved to bevy_anti_alias
        transformations.append(self.create_transformation(
            pattern="use bevy::core_pipeline::fxaa",
            replacement="use bevy::anti_alias::fxaa",
            description="FXAA moved to bevy_anti_alias"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy::core_pipeline::smaa",
            replacement="use bevy::anti_alias::smaa",
            description="SMAA moved to bevy_anti_alias"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy::core_pipeline::experimental::taa",
            replacement="use bevy::anti_alias::taa",
            description="TAA no longer experimental, moved to bevy_anti_alias"
        ))

        # Post-processing moved to bevy_post_process
        transformations.append(self.create_transformation(
            pattern="use bevy::core_pipeline::bloom",
            replacement="use bevy::post_process::bloom",
            description="Bloom moved to bevy_post_process"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy::core_pipeline::tonemapping",
            replacement="use bevy::post_process::tonemapping",
            description="Tonemapping moved to bevy_post_process"
        ))

        # Text2d moved to bevy_sprite
        transformations.append(self.create_transformation(
            pattern="use bevy::text::Text2d",
            replacement="use bevy::sprite::Text2d",
            description="Text2d moved to bevy_sprite"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy_text::Text2d",
            replacement="use bevy_sprite::Text2d",
            description="Text2d moved to bevy_sprite crate"
        ))

        # Platform types moved
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::SyncCell",
            replacement="use bevy::platform::cell::SyncCell",
            description="SyncCell moved to bevy_platform"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy::utils::SyncUnsafeCell",
            replacement="use bevy::platform::cell::SyncUnsafeCell",
            description="SyncUnsafeCell moved to bevy_platform"
        ))

        # ===== SYSTEM SET RENAMES (20 transformations) =====

        transformations.append(self.create_transformation(
            pattern="AccessibilitySystem",
            replacement="AccessibilitySystems",
            description="AccessibilitySystem → AccessibilitySystems"
        ))

        transformations.append(self.create_transformation(
            pattern="GizmoRenderSystem",
            replacement="GizmoRenderSystems",
            description="GizmoRenderSystem → GizmoRenderSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="PickSet",
            replacement="PickingSystems",
            description="PickSet → PickingSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="RunFixedMainLoopSystem",
            replacement="RunFixedMainLoopSystems",
            description="RunFixedMainLoopSystem → RunFixedMainLoopSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="TransformSystem",
            replacement="TransformSystems",
            description="TransformSystem → TransformSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="RemoteSet",
            replacement="RemoteSystems",
            description="RemoteSet → RemoteSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="RenderSet",
            replacement="RenderSystems",
            description="RenderSet → RenderSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="SpriteSystem",
            replacement="SpriteSystems",
            description="SpriteSystem → SpriteSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="StateTransitionSteps",
            replacement="StateTransitionSystems",
            description="StateTransitionSteps → StateTransitionSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="RenderUiSystem",
            replacement="RenderUiSystems",
            description="RenderUiSystem → RenderUiSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="UiSystem",
            replacement="UiSystems",
            description="UiSystem → UiSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="Animation::",
            replacement="AnimationSystems::",
            description="Animation → AnimationSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="TrackAssets",
            replacement="AssetTrackingSystems",
            description="TrackAssets → AssetTrackingSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="UpdateGizmoMeshes",
            replacement="GizmoMeshSystems",
            description="UpdateGizmoMeshes → GizmoMeshSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="InputSystem",
            replacement="InputSystems",
            description="InputSystem → InputSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="InputFocusSet",
            replacement="InputFocusSystems",
            description="InputFocusSet → InputFocusSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="ExtractMaterialsSet",
            replacement="MaterialExtractionSystems",
            description="ExtractMaterialsSet → MaterialExtractionSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="ExtractMeshesSet",
            replacement="MeshExtractionSystems",
            description="ExtractMeshesSet → MeshExtractionSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="RumbleSystem",
            replacement="RumbleSystems",
            description="RumbleSystem → RumbleSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="CameraUpdateSystem",
            replacement="CameraUpdateSystems",
            description="CameraUpdateSystem → CameraUpdateSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="Update2dText",
            replacement="Text2dUpdateSystems",
            description="Update2dText → Text2dUpdateSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="TimeSystem",
            replacement="TimeSystems",
            description="TimeSystem → TimeSystems"
        ))

        transformations.append(self.create_transformation(
            pattern="EventUpdates",
            replacement="EventUpdateSystems",
            description="EventUpdates → EventUpdateSystems"
        ))

        # ===== RENDERING CHANGES (5 transformations) =====

        transformations.append(self.create_transformation(
            pattern="Pointer<Pressed>",
            replacement="Pointer<Press>",
            description="Pointer<Pressed> → Pointer<Press>"
        ))

        transformations.append(self.create_transformation(
            pattern="Pointer<Released>",
            replacement="Pointer<Release>",
            description="Pointer<Released> → Pointer<Release>"
        ))

        transformations.append(self.create_transformation(
            pattern="YAxisOrientation",
            replacement="// YAxisOrientation removed - automatic now",
            description="YAxisOrientation removed, chosen automatically"
        ))

        # Complex transformation for Camera.hdr split into Hdr component
        def camera_hdr_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            # This is a complex transformation that requires manual intervention
            # since it involves splitting a field into a separate component
            original_match = vars.get("_matched_text", "Camera { hdr: true, ..default() }")
            # Return a comment indicating the manual change needed
            return f"/* TODO: Split hdr field - use Hdr component separately: (Hdr, /* {original_match.replace('hdr: true, ', '').replace('hdr: true', '')} */)"

        transformations.append(self.create_transformation(
            pattern="Camera { hdr: true",
            replacement="",  # Ignored when callback is present
            description="Camera.hdr split into Hdr component",
            callback=camera_hdr_callback
        ))

        transformations.append(self.create_transformation(
            pattern="ComputedNodeTarget",
            replacement="ComputedUiTargetCamera",
            description="ComputedNodeTarget → ComputedUiTargetCamera"
        ))

        return transformations
    
    def get_affected_patterns(self) -> List[str]:
        return [
            "**/*.rs",
            "src/**/*.rs",
            "examples/**/*.rs",
            "benches/**/*.rs",
            "tests/**/*.rs",
        ]
    
    def pre_migration_steps(self) -> bool:
        try:
            self.logger.info("=" * 60)
            self.logger.info("BEVY 0.16 → 0.17 MIGRATION - PART 2 OF 3")
            self.logger.info("=" * 60)
            self.logger.info("This part covers:")
            self.logger.info("  - bevy_render reorganization (new crates)")
            self.logger.info("  - System set renames (*Systems suffix)")
            self.logger.info("  - Anti-aliasing and post-processing moves")
            self.logger.info("=" * 60)
            
            # Check for bevy_render imports
            render_files = self.find_files_with_pattern("use bevy::render::")
            if render_files:
                self.logger.info(f"Found {len(render_files)} files with bevy::render imports (will update)")
            
            # Check for system sets
            system_set_files = self.find_files_with_pattern("PickSet")
            if system_set_files:
                self.logger.info(f"Found {len(system_set_files)} files using old system set names")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        try:
            self.logger.info("=" * 60)
            self.logger.info("Part 2 migration complete!")
            self.logger.info("=" * 60)
            self.logger.info("IMPORTANT: This is Part 2 of 3")
            self.logger.info("Next steps:")
            self.logger.info("1. Review import path updates")
            self.logger.info("2. Check system set renames")
            self.logger.info("3. Run Part 3: Entity representation & specialized APIs")
            self.logger.info("=" * 60)
            self.logger.info("Manual migration required for:")
            self.logger.info("  - Camera.hdr → Hdr component (spawn separately)")
            self.logger.info("  - Feature flags (bevy_ui_render, bevy_sprite_render)")
            self.logger.info("  - wgpu 25 shader changes (@group indices)")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def validate_preconditions(self) -> bool:
        if not super().validate_preconditions():
            return False
        
        try:
            # Check that Part 1 was completed
            cargo_toml_path = self.file_manager.find_cargo_toml()
            if cargo_toml_path:
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                # Should still be on 0.16 (Cargo.toml updated in Part 3)
                if not re.search(r'bevy\s*=\s*["\']0\.16', content):
                    self.logger.warning("Expected Bevy 0.16 - ensure Part 1 was run first")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False
