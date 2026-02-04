"""
Migration from Bevy 0.14 to 0.15 - Part 1: Core API Changes
Handles core API changes, renames, and structural updates
Part 2 handles required components migration
"""

import logging
import re
from pathlib import Path
from typing import List

from migrations.base_migration import BaseMigration, MigrationResult
from core.ast_processor import ASTTransformation


class Migration_0_14_to_0_15_Part1(BaseMigration):
    """
    Migration class for upgrading Bevy projects from version 0.14 to 0.15 (Part 1)
    
    This is Part 1 of a two-part migration focusing on core API changes.
    Part 2 handles required components migration.
    
    Key changes in Part 1:
    - ECS API changes (observers, commands, queries)
    - Reflection API overhaul (PartialReflect, opaque types)
    - Rendering API changes (retained render world, MainEntity/RenderEntity)
    - Animation curve-based system
    - Text rework preparation
    - Many method renames and signature changes
    """
    
    @property
    def from_version(self) -> str:
        """Source Bevy version for this migration"""
        return "0.14"
    
    @property
    def to_version(self) -> str:
        """Target Bevy version for this migration"""
        return "0.15-part1"
    
    @property
    def description(self) -> str:
        """Human-readable description of this migration"""
        return "Migrate Bevy project from version 0.14 to 0.15 (Part 1: Core API Changes)"
    
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for Part 1
        
        Returns:
            List of ASTTransformation objects
        """
        transformations = []
        
        # ===== ANIMATION CHANGES =====
        
        # 1. is_playing_animation to animation_is_playing
        transformations.append(self.create_transformation(
            pattern="$PLAYER.is_playing_animation($ARGS)",
            replacement="$PLAYER.animation_is_playing($ARGS)",
            description="Rename is_playing_animation to animation_is_playing"
        ))
        
        # 2. Handle<AnimationGraph> to AnimationGraphHandle
        transformations.append(self.create_transformation(
            pattern="Handle<AnimationGraph>",
            replacement="AnimationGraphHandle",
            description="Replace Handle<AnimationGraph> component with AnimationGraphHandle"
        ))
        
        # ===== APP CHANGES =====
        
        # 3. run_fixed_main_schedule to RunFixedMainLoopSystem
        transformations.append(self.create_transformation(
            pattern="$SYSTEM.before(run_fixed_main_schedule)",
            replacement="$SYSTEM.in_set(RunFixedMainLoopSystem::BeforeFixedMainLoop)",
            description="Replace run_fixed_main_schedule with RunFixedMainLoopSystem"
        ))
        
        # 4. EventLoopProxy type change
        transformations.append(self.create_transformation(
            pattern="NonSend<EventLoopProxy<$TYPE>>",
            replacement="Res<EventLoopProxy<$TYPE>>",
            description="EventLoopProxy is now Send (use Res instead of NonSend)"
        ))
        
        # 5. Remove second generic from add_before/add_after
        transformations.append(self.create_transformation(
            pattern="$PLUGINS.add_before::<$PLUGIN, $_>($ARG)",
            replacement="$PLUGINS.add_before::<$PLUGIN>($ARG)",
            description="Remove second generic from add_before"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$PLUGINS.add_after::<$PLUGIN, $_>($ARG)",
            replacement="$PLUGINS.add_after::<$PLUGIN>($ARG)",
            description="Remove second generic from add_after"
        ))
        
        # ===== ASSETS CHANGES =====
        
        # 6. AssetPath::from to from_static for performance
        transformations.append(self.create_transformation(
            pattern='AssetPath::from("$PATH")',
            replacement='AssetPath::from_static("$PATH")',
            description="Use AssetPath::from_static for string literals"
        ))
        
        # 7. LoadContext loader API changes
        transformations.append(self.create_transformation(
            pattern="$CTX.loader().untyped()",
            replacement="$CTX.loader().with_unknown_type()",
            description="Rename untyped to with_unknown_type"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$CTX.loader().direct()",
            replacement="$CTX.loader().immediate()",
            description="Rename direct to immediate"
        ))
        
        # ===== COLOR CHANGES =====
        
        # 8. Color::linear to to_linear
        transformations.append(self.create_transformation(
            pattern="$COLOR.linear()",
            replacement="$COLOR.to_linear()",
            description="Rename Color::linear to to_linear"
        ))
        
        # ===== CORE CHANGES =====
        
        # 9. DebugName to NameOrEntity
        transformations.append(self.create_transformation(
            pattern="use bevy::core::name::DebugName",
            replacement="use bevy::core::name::NameOrEntity",
            description="Rename DebugName to NameOrEntity"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DebugName",
            replacement="NameOrEntity",
            description="Rename DebugName type to NameOrEntity"
        ))
        
        # ===== ECS CHANGES (MAJOR) =====
        
        # 10. World::flush_commands to flush
        transformations.append(self.create_transformation(
            pattern="$WORLD.flush_commands()",
            replacement="$WORLD.flush()",
            description="Rename World::flush_commands to flush"
        ))
        
        # 11. World::get_entity returns Result
        transformations.append(self.create_transformation(
            pattern="$WORLD.get_entity($ENTITY).ok()",
            replacement="$WORLD.get_entity($ENTITY).ok()",
            description="World::get_entity now returns Result (add .ok() if needed)"
        ))
        
        # 12. World::inspect_entity returns Iterator
        transformations.append(self.create_transformation(
            pattern="$WORLD.inspect_entity($ENTITY)",
            replacement="$WORLD.inspect_entity($ENTITY).collect::<Vec<_>>()",
            description="World::inspect_entity returns Iterator (collect if Vec needed)"
        ))
        
        # 13. ManualEventReader to EventCursor
        transformations.append(self.create_transformation(
            pattern="ManualEventReader",
            replacement="EventCursor",
            description="Rename ManualEventReader to EventCursor"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$EVENTS.get_reader()",
            replacement="$EVENTS.get_cursor()",
            description="Rename Events::get_reader to get_cursor"
        ))
        
        # 14. Events::oldest_id to oldest_event_count
        transformations.append(self.create_transformation(
            pattern="$EVENTS.oldest_id()",
            replacement="$EVENTS.oldest_event_count()",
            description="Rename Events::oldest_id to oldest_event_count"
        ))
        
        # 15. Commands::add to queue
        transformations.append(self.create_transformation(
            pattern="$COMMANDS.add($CMD)",
            replacement="$COMMANDS.queue($CMD)",
            description="Rename Commands::add to queue"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$COMMANDS.push($CMD)",
            replacement="$COMMANDS.queue($CMD)",
            description="Rename Commands::push to queue"
        ))
        
        # 16. Observer methods rename
        transformations.append(self.create_transformation(
            pattern="$APP.observe($OBSERVER)",
            replacement="$APP.add_observer($OBSERVER)",
            description="Rename App::observe to add_observer"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$WORLD.observe($OBSERVER)",
            replacement="$WORLD.add_observer($OBSERVER)",
            description="Rename World::observe to add_observer"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$COMMANDS.observe($OBSERVER)",
            replacement="$COMMANDS.add_observer($OBSERVER)",
            description="Rename Commands::observe to add_observer"
        ))
        
        # 17. register_one_shot_system to register_system
        transformations.append(self.create_transformation(
            pattern="$COMMANDS.register_one_shot_system($SYSTEM)",
            replacement="$COMMANDS.register_system($SYSTEM)",
            description="Rename register_one_shot_system to register_system"
        ))
        
        # 18. init_component to register_component
        transformations.append(self.create_transformation(
            pattern="$WORLD.init_component::<$TYPE>()",
            replacement="$WORLD.register_component::<$TYPE>()",
            description="Rename World::init_component to register_component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$WORLD.init_bundle::<$TYPE>()",
            replacement="$WORLD.register_bundle::<$TYPE>()",
            description="Rename World::init_bundle to register_bundle"
        ))
        
        # 19. push_children to add_children
        transformations.append(self.create_transformation(
            pattern="$ENTITY.push_children($CHILDREN)",
            replacement="$ENTITY.add_children($CHILDREN)",
            description="Rename EntityCommands::push_children to add_children"
        ))
        
        # 20. Run condition simplifications
        transformations.append(self.create_transformation(
            pattern="run_once()",
            replacement="run_once",
            description="Simplify run_once() to run_once"
        ))
        
        transformations.append(self.create_transformation(
            pattern="on_event::<$TYPE>()",
            replacement="on_event::<$TYPE>",
            description="Simplify on_event::<T>() to on_event::<T>"
        ))
        
        transformations.append(self.create_transformation(
            pattern="resource_removed::<$TYPE>()",
            replacement="resource_removed::<$TYPE>",
            description="Simplify resource_removed::<T>() to resource_removed::<T>"
        ))
        
        transformations.append(self.create_transformation(
            pattern="any_component_removed::<$TYPE>()",
            replacement="any_component_removed::<$TYPE>",
            description="Simplify any_component_removed::<T>() to any_component_removed::<T>"
        ))
        
        # 21. and_then/or_else to and/or
        transformations.append(self.create_transformation(
            pattern="$CONDITION.and_then($OTHER)",
            replacement="$CONDITION.and($OTHER)",
            description="Rename and_then to and for run conditions"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$CONDITION.or_else($OTHER)",
            replacement="$CONDITION.or($OTHER)",
            description="Rename or_else to or for run conditions"
        ))
        
        # 22. World::resource_ref returns Ref instead of Res
        transformations.append(self.create_transformation(
            pattern="let $VAR: Res<$TYPE> = $WORLD.resource_ref()",
            replacement="let $VAR: Ref<$TYPE> = $WORLD.resource_ref()",
            description="World::resource_ref now returns Ref<T> instead of Res<T>"
        ))
        
        # ===== GIZMOS CHANGES =====
        
        # 23. Gizmo Isometry usage
        transformations.append(self.create_transformation(
            pattern="gizmos.circle_2d($POS, $RADIUS, $COLOR)",
            replacement="gizmos.circle_2d(Isometry2d::from_translation($POS), $RADIUS, $COLOR)",
            description="Use Isometry2d for gizmo position"
        ))
        
        # ===== INPUT CHANGES =====
        
        # 24. Gamepad resource to Query
        transformations.append(self.create_transformation(
            pattern="gamepads: Res<Gamepads>",
            replacement="gamepads: Query<&Gamepad>",
            description="Gamepads is now a Query<&Gamepad> instead of resource"
        ))
        
        # ===== MATH CHANGES =====
        
        # 25. Rot2::angle_between to angle_to
        transformations.append(self.create_transformation(
            pattern="$ROT.angle_between($OTHER)",
            replacement="$ROT.angle_to($OTHER)",
            description="Rename Rot2::angle_between to angle_to"
        ))
        
        # 26. Ray2d/3d::new with Dir2/Dir3
        transformations.append(self.create_transformation(
            pattern="Ray2d::new($ORIGIN, $DIRECTION)",
            replacement="Ray2d::new($ORIGIN, Dir2::new($DIRECTION).unwrap())",
            description="Ray2d::new now requires Dir2 instead of Vec2"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Ray3d::new($ORIGIN, $DIRECTION)",
            replacement="Ray3d::new($ORIGIN, Dir3::new($DIRECTION).unwrap())",
            description="Ray3d::new now requires Dir3 instead of Vec3"
        ))
        
        # ===== REFLECTION CHANGES (MAJOR) =====
        
        # 27. ReflectKind::Value to Opaque
        transformations.append(self.create_transformation(
            pattern="ReflectKind::Value",
            replacement="ReflectKind::Opaque",
            description="Rename ReflectKind::Value to Opaque"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ReflectRef::Value",
            replacement="ReflectRef::Opaque",
            description="Rename ReflectRef::Value to Opaque"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ReflectMut::Value",
            replacement="ReflectMut::Opaque",
            description="Rename ReflectMut::Value to Opaque"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ReflectOwned::Value",
            replacement="ReflectOwned::Opaque",
            description="Rename ReflectOwned::Value to Opaque"
        ))
        
        # 28. reflect_value attribute to reflect(opaque)
        transformations.append(self.create_transformation(
            pattern="#[reflect_value($TRAITS)]",
            replacement="#[reflect(opaque)]\n#[reflect($TRAITS)]",
            description="Replace reflect_value with reflect(opaque)"
        ))
        
        # 29. impl_reflect_value to impl_reflect_opaque
        transformations.append(self.create_transformation(
            pattern="impl_reflect_value!",
            replacement="impl_reflect_opaque!",
            description="Rename impl_reflect_value! to impl_reflect_opaque!"
        ))
        
        # 30. ShortName import move
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::ShortName",
            replacement="use bevy::reflect::ShortName",
            description="Move ShortName to bevy::reflect"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy_utils::ShortName",
            replacement="use bevy_reflect::ShortName",
            description="Move ShortName to bevy_reflect"
        ))
        
        # 31. DynamicArray::from_vec to from_iter
        transformations.append(self.create_transformation(
            pattern="DynamicArray::from_vec($VEC)",
            replacement="DynamicArray::from_iter($VEC)",
            description="Rename DynamicArray::from_vec to from_iter"
        ))
        
        # ===== RENDERING CHANGES =====
        
        # 32. Rendering component renames
        transformations.append(self.create_transformation(
            pattern="AutoExposureSettings",
            replacement="AutoExposure",
            description="Rename AutoExposureSettings to AutoExposure"
        ))
        
        transformations.append(self.create_transformation(
            pattern="BloomSettings",
            replacement="Bloom",
            description="Rename BloomSettings to Bloom"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DepthOfFieldSettings",
            replacement="DepthOfField",
            description="Rename DepthOfFieldSettings to DepthOfField"
        ))
        
        transformations.append(self.create_transformation(
            pattern="FogSettings",
            replacement="DistanceFog",
            description="Rename FogSettings to DistanceFog"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SmaaSettings",
            replacement="Smaa",
            description="Rename SmaaSettings to Smaa"
        ))
        
        transformations.append(self.create_transformation(
            pattern="TemporalAntiAliasSettings",
            replacement="TemporalAntiAliasing",
            description="Rename TemporalAntiAliasSettings to TemporalAntiAliasing"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ScreenSpaceAmbientOcclusionSettings",
            replacement="ScreenSpaceAmbientOcclusion",
            description="Rename ScreenSpaceAmbientOcclusionSettings to ScreenSpaceAmbientOcclusion"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ScreenSpaceReflectionsSettings",
            replacement="ScreenSpaceReflections",
            description="Rename ScreenSpaceReflectionsSettings to ScreenSpaceReflections"
        ))
        
        transformations.append(self.create_transformation(
            pattern="VolumetricFogSettings",
            replacement="VolumetricFog",
            description="Rename VolumetricFogSettings to VolumetricFog"
        ))
        
        # 33. GpuMesh to RenderMesh
        transformations.append(self.create_transformation(
            pattern="GpuMesh",
            replacement="RenderMesh",
            description="Rename GpuMesh to RenderMesh"
        ))
        
        # 34. OrthographicProjection::default split
        transformations.append(self.create_transformation(
            pattern="OrthographicProjection { $FIELDS, ..default() }",
            replacement="OrthographicProjection { $FIELDS, ..OrthographicProjection::default_3d() }",
            description="Use OrthographicProjection::default_3d() or default_2d()"
        ))
        
        # ===== SCENES CHANGES =====
        
        # 35. DynamicSceneBuilder method renames
        transformations.append(self.create_transformation(
            pattern="$BUILDER.allow_all()",
            replacement="$BUILDER.allow_all_components()",
            description="Rename allow_all to allow_all_components"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$BUILDER.deny_all()",
            replacement="$BUILDER.deny_all_components()",
            description="Rename deny_all to deny_all_components"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$BUILDER.with_filter($FILTER)",
            replacement="$BUILDER.with_component_filter($FILTER)",
            description="Rename with_filter to with_component_filter"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$BUILDER.allow($TYPE)",
            replacement="$BUILDER.allow_component($TYPE)",
            description="Rename allow to allow_component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$BUILDER.deny($TYPE)",
            replacement="$BUILDER.deny_component($TYPE)",
            description="Rename deny to deny_component"
        ))
        
        # ===== TEXT CHANGES =====
        
        # 36. TextStyle to TextFont + TextColor
        transformations.append(self.create_transformation(
            pattern="TextStyle",
            replacement="TextFont",
            description="Rename TextStyle to TextFont (color moved to TextColor)"
        ))
        
        # 37. Text2dBounds to TextBounds
        transformations.append(self.create_transformation(
            pattern="Text2dBounds",
            replacement="TextBounds",
            description="Rename Text2dBounds to TextBounds"
        ))
        
        # ===== TIME CHANGES =====
        
        # 38. Stopwatch::paused to is_paused
        transformations.append(self.create_transformation(
            pattern="$STOPWATCH.paused()",
            replacement="$STOPWATCH.is_paused()",
            description="Rename Stopwatch::paused to is_paused"
        ))
        
        # 39. Time::elapsed_seconds to elapsed_secs
        transformations.append(self.create_transformation(
            pattern="$TIME.elapsed_seconds()",
            replacement="$TIME.elapsed_secs()",
            description="Rename Time::elapsed_seconds to elapsed_secs"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$TIME.elapsed_seconds_f64()",
            replacement="$TIME.elapsed_secs_f64()",
            description="Rename Time::elapsed_seconds_f64 to elapsed_secs_f64"
        ))
        
        # ===== UI CHANGES =====
        
        # 40. Node to ComputedNode for computed properties
        transformations.append(self.create_transformation(
            pattern="Query<&Node>",
            replacement="Query<&ComputedNode>",
            description="Use ComputedNode for computed node properties"
        ))
        
        # 41. Style to Node for layout properties  
        transformations.append(self.create_transformation(
            pattern="Style {",
            replacement="Node {",
            description="Rename Style to Node for layout properties"
        ))
        
        # 42. BreakLineOn to LineBreak
        transformations.append(self.create_transformation(
            pattern="BreakLineOn",
            replacement="LineBreak",
            description="Rename BreakLineOn to LineBreak"
        ))
        
        # 43. UiImage to ImageNode
        transformations.append(self.create_transformation(
            pattern="UiImage",
            replacement="ImageNode",
            description="Rename UiImage to ImageNode"
        ))
        
        # 44. ZIndex split
        transformations.append(self.create_transformation(
            pattern="ZIndex::Local($VALUE)",
            replacement="ZIndex($VALUE)",
            description="Replace ZIndex::Local with ZIndex component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ZIndex::Global($VALUE)",
            replacement="GlobalZIndex($VALUE)",
            description="Replace ZIndex::Global with GlobalZIndex component"
        ))
        
        # ===== UTILS CHANGES =====
        
        # 45. EntityHash imports move
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::EntityHash",
            replacement="use bevy::ecs::entity::EntityHash",
            description="Move EntityHash to bevy::ecs::entity"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::EntityHashMap",
            replacement="use bevy::ecs::entity::EntityHashMap",
            description="Move EntityHashMap to bevy::ecs::entity"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::EntityHashSet",
            replacement="use bevy::ecs::entity::EntityHashSet",
            description="Move EntityHashSet to bevy::ecs::entity"
        ))
        
        # 46. get_short_name to ShortName wrapper
        transformations.append(self.create_transformation(
            pattern="get_short_name($NAME)",
            replacement="ShortName($NAME).to_string()",
            description="Replace get_short_name with ShortName wrapper"
        ))
        
        # ===== WINDOWING CHANGES =====
        
        # 47. ANDROID_APP move
        transformations.append(self.create_transformation(
            pattern="use bevy::winit::ANDROID_APP",
            replacement="use bevy::window::ANDROID_APP",
            description="Move ANDROID_APP to bevy::window"
        ))
        
        return transformations
    
    def get_affected_patterns(self) -> List[str]:
        """
        Get list of file patterns that this migration affects
        
        Returns:
            List of glob patterns
        """
        return [
            "**/*.rs",
            "src/**/*.rs",
            "examples/**/*.rs",
            "benches/**/*.rs",
            "tests/**/*.rs",
            "Cargo.toml"
        ]
    
    def pre_migration_steps(self) -> bool:
        """Execute steps before applying transformations"""
        try:
            self.logger.info("Executing pre-migration steps for 0.14 -> 0.15 Part 1")
            
            rust_files = self.file_manager.find_rust_files()
            
            # Warn about two-part migration
            self.logger.warning("=" * 60)
            self.logger.warning("IMPORTANT: This is Part 1 of a two-part migration!")
            self.logger.warning("After running Part 1, you MUST run Part 2 for complete migration.")
            self.logger.warning("Part 1: Core API changes (this migration)")
            self.logger.warning("Part 2: Required components migration")
            self.logger.warning("=" * 60)
            
            # Check for patterns that will change
            ecs_files = self.find_files_with_pattern("World::")
            if ecs_files:
                self.logger.info(f"Found {len(ecs_files)} files using World API (many methods renamed)")
            
            reflection_files = self.find_files_with_pattern("ReflectKind::")
            if reflection_files:
                self.logger.info(f"Found {len(reflection_files)} files using Reflection (Value -> Opaque)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        """Execute steps after applying transformations"""
        try:
            self.logger.info("Executing post-migration steps for 0.14 -> 0.15 Part 1")
            
            # Note: We don't update Cargo.toml yet - that happens in Part 2
            self.logger.info("Cargo.toml will be updated in Part 2")
            
            # Check for manual migration patterns
            self._check_for_manual_migration_needed()
            
            # Remind about Part 2
            self.logger.warning("=" * 60)
            self.logger.warning("Part 1 migration complete!")
            self.logger.warning("NEXT STEP: Run Part 2 migration for required components")
            self.logger.warning("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def _check_for_manual_migration_needed(self) -> None:
        """Check for patterns that might need manual migration"""
        try:
            manual_patterns = [
                ("dyn Reflect", "Most dyn Reflect should be dyn PartialReflect - review manually"),
                ("TextBundle", "Text bundles removed - Part 2 will migrate, but review hierarchy changes"),
                ("Gamepad", "Gamepad is now entity-based - significant refactoring may be needed"),
                ("Extract<Query<(Entity,", "Retained render world - use RenderEntity, not Entity"),
                ("get_or_spawn", "get_or_spawn deprecated - use entity() or spawn()"),
                ("SceneInstanceReady", "SceneInstanceReady now uses observers - manual migration needed"),
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
        """Validate that preconditions for this migration are met"""
        if not super().validate_preconditions():
            return False
        
        try:
            cargo_toml_path = self.project_path / "Cargo.toml"
            if cargo_toml_path.exists():
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                if re.search(r'bevy\s*=\s*["\']0\.14', content):
                    self.logger.info("Confirmed Bevy 0.14 dependency in Cargo.toml")
                elif re.search(r'bevy\s*=.*version\s*=\s*["\']0\.14', content):
                    self.logger.info("Confirmed Bevy 0.14 dependency in Cargo.toml")
                else:
                    self.logger.warning("Could not confirm Bevy 0.14 dependency in Cargo.toml")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False
