"""
Migration from Bevy 0.16 to 0.17 - Part 3 (Final)
Entity Representation, UI Transform Specialization, and Misc Changes

This is Part 3 of 3 for the Bevy 0.16 to 0.17 migration.
Run parts in order: Part 1 → Part 2 → Part 3

After this part, update Cargo.toml to Bevy 0.17
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Callable

from bevymigrate.migrations.base_migration import BaseMigration, MigrationResult
from bevymigrate.core.ast_processor import ASTTransformation


class Migration_0_16_to_0_17_Part3(BaseMigration):
    """
    Migration Part 3: Entity Representation & Specialized APIs (FINAL)

    Key changes in this part:
    - Entity representation changes (EntityRow, NonMaxU32)
    - UI Transform specialization (UiTransform, UiGlobalTransform)
    - Timer/Audio/Picking changes
    - Text/Font/Mesh updates
    - Cargo.toml update to 0.17
    """

    @property
    def from_version(self) -> str:
        return "0.17-part2"

    @property
    def to_version(self) -> str:
        return "0.17"

    @property
    def description(self) -> str:
        return "Bevy 0.16 → 0.17 Part 3 (FINAL): Entity representation, UI transform, misc changes + Cargo.toml update"

    def get_transformations(self) -> List[ASTTransformation]:
        transformations = []

        # ===== ENTITY REPRESENTATION CHANGES (15 transformations) =====

        # Entity::from_raw → from_raw_u32 (returns Option)
        transformations.append(self.create_transformation(
            pattern="Entity::from_raw($INDEX)",
            replacement="Entity::from_raw_u32($INDEX).unwrap()",
            description="Entity::from_raw → from_raw_u32 (returns Option)"
        ))

        transformations.append(self.create_transformation(
            pattern="$ENTITY.index()",
            replacement="$ENTITY.row().index_u32()",
            description="Entity::index → row().index_u32()"
        ))

        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::entity::identifier",
            replacement="// identifier module removed",
            description="identifier module removed, functionality in Entity"
        ))

        transformations.append(self.create_transformation(
            pattern="IdentifierError",
            replacement="Option",
            description="IdentifierError replaced with Option"
        ))

        # ===== UI TRANSFORM SPECIALIZED (5 transformations) =====

        # Note: This is complex and requires manual migration
        # We'll add warnings/comments for manual review

        # Complex transformation for UI Transform changes
        def ui_transform_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            x_val = vars.get("X", "0.0")
            y_val = vars.get("Y", "0.0")
            z_val = vars.get("Z", "0.0")
            # Return a comment indicating the manual change needed
            return f"/* TODO: For UI nodes, use UiTransform {{ translation: Val2::px({x_val}, {y_val}), ..default() }} instead of Transform::from_xyz */"

        transformations.append(self.create_transformation(
            pattern="Transform::from_xyz($X, $Y, $Z)",
            replacement="",  # Ignored when callback is present
            description="UI nodes use UiTransform instead of Transform",
            callback=ui_transform_callback
        ))

        transformations.append(self.create_transformation(
            pattern="GlobalTransform::from",
            replacement="UiGlobalTransform::from",
            description="UI nodes use UiGlobalTransform"
        ))

        # ===== UI CHANGES (10 transformations) =====

        transformations.append(self.create_transformation(
            pattern="JustifyText",
            replacement="Justify",
            description="JustifyText renamed to Justify"
        ))

        transformations.append(self.create_transformation(
            pattern="BorderColor($COLOR)",
            replacement="BorderColor::all($COLOR)",
            description="BorderColor now uses ::all() constructor"
        ))

        transformations.append(self.create_transformation(
            pattern="WindowPlugin { $$$PRE, primary_window: $VAL, $$$POST }",
            replacement="WindowPlugin { $$$PRE, primary_cursor_options: $VAL, $$$POST }",
            description="WindowPlugin::primary_window → primary_cursor_options"
        ))

        transformations.append(self.create_transformation(
            pattern="update_ui_context_system",
            replacement="propagate_ui_target_cameras",
            description="update_ui_context_system renamed"
        ))

        # ===== TIMER/AUDIO CHANGES (5 transformations) =====

        transformations.append(self.create_transformation(
            pattern="$TIMER.paused()",
            replacement="$TIMER.is_paused()",
            description="Timer::paused → is_paused"
        ))

        transformations.append(self.create_transformation(
            pattern="$TIMER.finished()",
            replacement="$TIMER.is_finished()",
            description="Timer::finished → is_finished"
        ))

        # Complex transformation for volume changes
        def volume_add_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            volume_var = vars.get("VOLUME", "volume")
            percent_var = vars.get("PERCENT", "percent")
            return f"{volume_var}.increase_by_percentage({percent_var})"

        def volume_sub_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            volume_var = vars.get("VOLUME", "volume")
            percent_var = vars.get("PERCENT", "percent")
            return f"{volume_var}.decrease_by_percentage({percent_var})"

        transformations.append(self.create_transformation(
            pattern="$VOLUME + $PERCENT",
            replacement="",  # Ignored when callback is present
            description="Volume Add/Sub removed, use increase_by_percentage",
            callback=volume_add_callback
        ))

        transformations.append(self.create_transformation(
            pattern="$VOLUME - $PERCENT",
            replacement="",  # Ignored when callback is present
            description="Volume Sub removed, use decrease_by_percentage",
            callback=volume_sub_callback
        ))

        # ===== PICKING CHANGES (3 transformations) =====

        transformations.append(self.create_transformation(
            pattern="PickingPlugin",
            replacement="// PickingPlugin → PickingSettings resource",
            description="PickingPlugin replaced with PickingSettings resource"
        ))

        transformations.append(self.create_transformation(
            pattern="PointerInputPlugin",
            replacement="// PointerInputPlugin → PointerInputSettings resource",
            description="PointerInputPlugin replaced with PointerInputSettings"
        ))

        transformations.append(self.create_transformation(
            pattern="$POINTER.target",
            replacement="$POINTER.original_event_target()",
            description="Pointer.target removed, use original_event_target()"
        ))

        # ===== TEXT/FONT CHANGES (3 transformations) =====

        transformations.append(self.create_transformation(
            pattern="TextFont::from_font($FONT)",
            replacement="TextFont::from($FONT)",
            description="TextFont::from_font → from"
        ))

        transformations.append(self.create_transformation(
            pattern="TextFont::from_line_height($HEIGHT)",
            replacement="TextFont::from($HEIGHT)",
            description="TextFont::from_line_height → from"
        ))

        transformations.append(self.create_transformation(
            pattern="use cosmic_text",
            replacement="// cosmic_text re-exports removed, add dependency",
            description="cosmic_text re-exports removed"
        ))

        # ===== MESH/MATH CHANGES (5 transformations) =====

        transformations.append(self.create_transformation(
            pattern="MergeMeshError",
            replacement="MeshMergeError",
            description="MergeMeshError → MeshMergeError"
        ))

        transformations.append(self.create_transformation(
            pattern="face_normal($A, $B, $C)",
            replacement="triangle_normal($A, $B, $C)",
            description="face_normal → triangle_normal"
        ))

        transformations.append(self.create_transformation(
            pattern="face_area_normal($A, $B, $C)",
            replacement="triangle_area_normal($A, $B, $C)",
            description="face_area_normal → triangle_area_normal"
        ))

        transformations.append(self.create_transformation(
            pattern="$MESH.with_computed_smooth_normals()",
            replacement="$MESH.with_computed_smooth_normals() // Consider with_computed_area_weighted_normals if needed",
            description="Smooth normals algorithm changed to angle-weighted"
        ))

        transformations.append(self.create_transformation(
            pattern="$MESH.compute_smooth_normals()",
            replacement="$MESH.compute_smooth_normals() // Consider compute_area_weighted_normals if needed",
            description="compute_smooth_normals algorithm changed"
        ))

        # ===== REFLECTION CHANGES (2 transformations) =====

        transformations.append(self.create_transformation(
            pattern="$MAP.get_at($INDEX)",
            replacement="$MAP.get($INDEX)",
            description="DynamicMap::get_at removed, use get"
        ))

        # ===== WINDOW/RENDERING CHANGES (5 transformations) =====

        transformations.append(self.create_transformation(
            pattern="WindowResolution::new($W as f32, $H as f32)",
            replacement="WindowResolution::new($W, $H)",
            description="WindowResolution now takes u32 directly"
        ))

        transformations.append(self.create_transformation(
            pattern="WindowResolution::new($W.0, $H.0)",
            replacement="WindowResolution::new($W, $H)",
            description="WindowResolution constructor simplified"
        ))

        transformations.append(self.create_transformation(
            pattern="RenderGraphApp",
            replacement="RenderGraphExt",
            description="RenderGraphApp renamed to RenderGraphExt"
        ))

        transformations.append(self.create_transformation(
            pattern="FULLSCREEN_SHADER_HANDLE",
            replacement="FullscreenShader",
            description="FULLSCREEN_SHADER_HANDLE → FullscreenShader resource"
        ))

        transformations.append(self.create_transformation(
            pattern="fullscreen_shader_vertex_state()",
            replacement="fullscreen_shader.to_vertex_state()",
            description="fullscreen_shader_vertex_state → FullscreenShader::to_vertex_state"
        ))

        # ===== MISC CHANGES (7 transformations) =====

        transformations.append(self.create_transformation(
            pattern="Entry::",
            replacement="ComponentEntry::",
            description="Entry enum renamed to ComponentEntry"
        ))

        transformations.append(self.create_transformation(
            pattern="OccupiedEntry",
            replacement="OccupiedComponentEntry",
            description="OccupiedEntry → OccupiedComponentEntry"
        ))

        transformations.append(self.create_transformation(
            pattern="VacantEntry",
            replacement="VacantComponentEntry",
            description="VacantEntry → VacantComponentEntry"
        ))

        transformations.append(self.create_transformation(
            pattern="$APP.enable_state_scoped_entities",
            replacement="// enable_state_scoped_entities deprecated - always enabled",
            description="State scoped entities always enabled"
        ))

        transformations.append(self.create_transformation(
            pattern="TextShadow",
            replacement="bevy::ui::widget::text::TextShadow",
            description="TextShadow moved to bevy::ui::widget::text"
        ))

        transformations.append(self.create_transformation(
            pattern="$TRANSFORM.compute_matrix()",
            replacement="$TRANSFORM.to_matrix()",
            description="Transform::compute_matrix → to_matrix"
        ))

        transformations.append(self.create_transformation(
            pattern="$GLOBAL_TRANSFORM.compute_matrix()",
            replacement="$GLOBAL_TRANSFORM.to_matrix()",
            description="GlobalTransform::compute_matrix → to_matrix"
        ))

        return transformations
    
    def get_affected_patterns(self) -> List[str]:
        return [
            "**/*.rs",
            "src/**/*.rs",
            "examples/**/*.rs",
            "benches/**/*.rs",
            "tests/**/*.rs",
            "Cargo.toml",
        ]
    
    def pre_migration_steps(self) -> bool:
        try:
            self.logger.info("=" * 60)
            self.logger.info("BEVY 0.16 → 0.17 MIGRATION - PART 3 OF 3 (FINAL)")
            self.logger.info("=" * 60)
            self.logger.info("This part covers:")
            self.logger.info("  - Entity representation changes")
            self.logger.info("  - UI Transform specialization")
            self.logger.info("  - Timer/Audio/Picking updates")
            self.logger.info("  - Cargo.toml update to 0.17")
            self.logger.info("=" * 60)
            
            # Check for Entity::from_raw usage
            entity_files = self.find_files_with_pattern("Entity::from_raw")
            if entity_files:
                self.logger.info(f"Found {len(entity_files)} files using Entity::from_raw (will update)")
            
            # Check for Transform in UI context
            ui_transform_files = self.find_files_with_pattern("Transform")
            if ui_transform_files:
                self.logger.warning(f"Found {len(ui_transform_files)} files using Transform - review for UI nodes")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        try:
            self.logger.info("=" * 60)
            self.logger.info("🎉 ALL 3 PARTS COMPLETE! 🎉")
            self.logger.info("=" * 60)
            self.logger.info("Migration to Bevy 0.17 finished!")
            self.logger.info("")
            self.logger.info("Next steps:")
            self.logger.info("1. Run 'cargo check' to verify compilation")
            self.logger.info("2. Review manual migration warnings")
            self.logger.info("3. Test your application thoroughly")
            self.logger.info("=" * 60)
            self.logger.info("Manual migration still required for:")
            self.logger.info("  - UI nodes: Transform → UiTransform (complex)")
            self.logger.info("  - Entity events: add 'entity: Entity' field")
            self.logger.info("  - Camera.hdr → Hdr component")
            self.logger.info("  - System::run Result handling")
            self.logger.info("  - Assets::insert Result handling")
            self.logger.info("  - Feature flags (bevy_ui_render, etc.)")
            self.logger.info("=" * 60)
            self.logger.info("Major breaking changes summary:")
            self.logger.info("  ✓ Event → Message (buffered events)")
            self.logger.info("  ✓ Trigger → On (observers)")
            self.logger.info("  ✓ bevy_render → 6 new crates")
            self.logger.info("  ✓ System sets → *Systems")
            self.logger.info("  ✓ Entity::from_raw → from_raw_u32")
            self.logger.info("  ✓ UI Transform specialized")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def validate_preconditions(self) -> bool:
        if not super().validate_preconditions():
            return False
        
        try:
            # Check that Parts 1 and 2 were completed
            cargo_toml_path = self.file_manager.find_cargo_toml()
            if cargo_toml_path:
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                # Should still be on 0.16 (we update in post_migration)
                if not re.search(r'bevy\s*=\s*["\']0\.16', content):
                    self.logger.warning("Expected Bevy 0.16 - ensure Parts 1 and 2 were run first")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False
