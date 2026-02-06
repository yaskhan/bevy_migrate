"""
Migration from Bevy 0.15 to 0.16
Handles comprehensive migration covering ECS error handling, entity relationships,
rendering updates, utils refactor, and 100+ other breaking changes
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any

from bevymigrate.migrations.base_migration import BaseMigration, MigrationResult
from bevymigrate.core.ast_processor import ASTTransformation


class Migration_0_15_to_0_16(BaseMigration):
    """
    Migration class for upgrading Bevy projects from version 0.15 to 0.16
    
    Key changes in Bevy 0.16:
    - ECS error handling: Query::single() returns Result, fallible systems
    - Entity relationships: Parent → ChildOf, built-in relationships
    - Rendering: wgpu 24, bindless mode, GPU culling by default
    - Audio: Volume enum (Linear/Decibels), mute support
    - Utils refactor: bevy_utils → bevy_platform
    - no_std support for main bevy crate
    - Rust 2024 edition upgrade
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
        return "Migrate Bevy project from version 0.15 to 0.16 - Comprehensive update with 100+ breaking changes"
    
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for migrating from 0.15 to 0.16
        
        Returns:
            List of ASTTransformation objects
        """
        transformations = []

        def audio_sink_param_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            name = vars.get("NAME", "").strip()
            if name.startswith("mut "):
                name = name[len("mut "):].strip()
            if not name:
                name = "sink"
            return f"mut {name}: Single<&mut AudioSink>"

        def set_parent_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            full = vars.get("_matched_text", "")
            if ".set_parent(" not in full:
                return full
            return re.sub(r"\.set_parent\(([^)]+)\)", r".insert(ChildOf(\1))", full)

        def require_attribute_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            type_snippet = vars.get("TYPE", "").strip()
            func_snippet = vars.get("FUNC", "").strip()
            full = vars.get("_matched_text", "")
            if not type_snippet or not func_snippet:
                return full
            if func_snippet.startswith("||"):
                expr = func_snippet[2:].strip()
                # If expr already contains the type constructor, use it directly
                # e.g. || A(10) -> #[require(A(10))]
                if expr.startswith(f"{type_snippet}(") or expr.startswith(f"{type_snippet} {{"):
                     return f"#[require({expr})]"
                return f"#[require({type_snippet}({expr}))]"
            if re.match(rf"^{re.escape(type_snippet)}\s*\(", func_snippet):
                return f"#[require({func_snippet})]"
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", func_snippet):
                return f"#[require({type_snippet} = {func_snippet}())]"
            return f"#[require({type_snippet} = {func_snippet})]"

        def child_of_deref_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            var_name = vars.get("VAR", "").strip()
            # Only match if the variable name is parent, child_of (case insensitive)
            if re.search(r'(?i)^(parent|child_of)$', var_name):
                return f"{var_name}.parent()"
            return vars.get("_matched_text", f"*{var_name}")
        
        # ===== ACCESSIBILITY =====
        
        # 1. Focus to InputFocus
        transformations.append(self.create_transformation(
            pattern="use bevy::a11y::Focus",
            replacement="use bevy::input_focus::InputFocus",
            description="Replace bevy::a11y::Focus with bevy::input_focus::InputFocus"
        ))
        
        transformations.append(self.create_transformation(
            pattern="bevy::a11y::Focus",
            replacement="bevy::input_focus::InputFocus",
            description="Replace Focus type with InputFocus"
        ))
        
        # ===== ANIMATION =====
        
        # 2. EaseFunction::Steps now takes JumpAt parameter
        ease_steps_rule = """
id: ease-steps
language: rust
rule:
  kind: call_expression
  pattern: "EaseFunction::Steps($N)"
fix: "EaseFunction::Steps($N, JumpAt::default())"
"""
        transformations.append(self.create_transformation(
            pattern="",
            replacement="",
            description="Add JumpAt parameter to EaseFunction::Steps",
            rule_yaml=ease_steps_rule
        ))
        
        # 3. CubicCurve::new_bezier renamed
        transformations.append(self.create_transformation(
            pattern="CubicCurve::new_bezier",
            replacement="CubicCurve::new_bezier_easing",
            description="Rename CubicCurve::new_bezier to new_bezier_easing"
        ))
        
        # ===== ASSETS =====
        
        # 4. Handle::weak_from_u128 deprecated
        transformations.append(self.create_transformation(
            pattern='Handle::weak_from_u128($UUID)',
            replacement='weak_handle!("$UUID")',
            description="Replace Handle::weak_from_u128 with weak_handle! macro"
        ))
        
        # ===== AUDIO =====
        
        # 5. AudioSinkPlayback::set_volume now takes &mut self
        transformations.append(self.create_transformation(
            pattern="$NAME: Single<&AudioSink>",
            replacement="",
            description="AudioSinkPlayback methods now require &mut self",
            callback=audio_sink_param_callback
        ))
        
        # 6. AudioSinkPlayback::toggle renamed
        transformations.append(self.create_transformation(
            pattern="$SINK.toggle()",
            replacement="$SINK.toggle_playback()",
            description="Rename AudioSinkPlayback::toggle to toggle_playback"
        ))
        
        # 7. Volume is now an enum
        transformations.append(self.create_transformation(
            pattern="Volume($VALUE)",
            replacement="Volume::Linear($VALUE)",
            description="Volume is now an enum with Linear and Decibels variants"
        ))
        
        # 8. Volume::ZERO renamed
        transformations.append(self.create_transformation(
            pattern="Volume::ZERO",
            replacement="Volume::SILENT",
            description="Rename Volume::ZERO to Volume::SILENT"
        ))
        
        # ===== DEV-TOOLS =====
        
        # 9. track_change_detection feature renamed
        # (This is a feature flag change, handled in Cargo.toml)
        
        # ===== ECS - ERROR HANDLING =====
        
        # 10. Query::single returns Result
        transformations.append(self.create_transformation(
            pattern="let $VAR = $QUERY.single()",
            replacement="let $VAR = $QUERY.single()?",
            description="Query::single now returns Result (use ? operator)"
        ))
        
        # 11. Query::single_mut returns Result
        transformations.append(self.create_transformation(
            pattern="let $VAR = $QUERY.single_mut()",
            replacement="let $VAR = $QUERY.single_mut()?",
            description="Query::single_mut now returns Result (use ? operator)"
        ))
        
        # 12. Query::get_single deprecated
        transformations.append(self.create_transformation(
            pattern="$QUERY.get_single()",
            replacement="$QUERY.single()",
            description="Query::get_single deprecated, use single() which returns Result"
        ))
        
        # 13. Query::many deprecated
        transformations.append(self.create_transformation(
            pattern="$QUERY.many($ENTITIES)",
            replacement="$QUERY.get_many($ENTITIES)?",
            description="Query::many deprecated, use get_many() which returns Result"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$QUERY.many_mut($ENTITIES)",
            replacement="$QUERY.get_many_mut($ENTITIES)?",
            description="Query::many_mut deprecated, use get_many_mut() which returns Result"
        ))
        
        # 14. World::try_despawn returns Result
        transformations.append(self.create_transformation(
            pattern="if $WORLD.try_despawn($ENTITY)",
            replacement="if $WORLD.try_despawn($ENTITY).is_ok()",
            description="World::try_despawn now returns Result instead of bool"
        ))
        
        # 15. World::inspect_entity returns Result
        transformations.append(self.create_transformation(
            pattern="$WORLD.inspect_entity($ENTITY)",
            replacement="$WORLD.inspect_entity($ENTITY)?",
            description="World::inspect_entity now returns Result"
        ))
        
        # ===== ECS - RELATIONSHIPS =====
        
        # 16. Parent renamed to ChildOf
        transformations.append(self.create_transformation(
            pattern="use bevy::hierarchy::Parent",
            replacement="use bevy::hierarchy::ChildOf",
            description="Parent component renamed to ChildOf"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Query<&Parent>",
            replacement="Query<&ChildOf>",
            description="Replace Parent with ChildOf in queries"
        ))
        
        # 17. ChildOf::get() deprecated
        transformations.append(self.create_transformation(
            pattern="$CHILD_OF.get()",
            replacement="$CHILD_OF.parent()",
            description="ChildOf::get() deprecated, use parent()"
        ))
        
        # 18. ChildOf Deref removed
        transformations.append(self.create_transformation(
            pattern="*$VAR",
            replacement="",
            description="ChildOf Deref removed, use parent() method",
            callback=child_of_deref_callback
        ))
        
        # 19. despawn_recursive is now default despawn
        transformations.append(self.create_transformation(
            pattern="$COMMANDS.entity($E).despawn_recursive()",
            replacement="$COMMANDS.entity($E).despawn()",
            description="despawn_recursive is now the default despawn behavior"
        ))
        
        # 20. despawn_descendants renamed
        transformations.append(self.create_transformation(
            pattern="$COMMANDS.entity($E).despawn_descendants()",
            replacement="$COMMANDS.entity($E).despawn_related::<Children>()",
            description="despawn_descendants renamed to despawn_related::<Children>"
        ))
        
        # 21. ChildBuilder renamed to ChildSpawnerCommands
        transformations.append(self.create_transformation(
            pattern="builder: &mut ChildBuilder",
            replacement="spawner: &mut ChildSpawnerCommands",
            description="ChildBuilder renamed to ChildSpawnerCommands"
        ))
        
        # 22. parent_entity renamed to target_entity
        transformations.append(self.create_transformation(
            pattern="$BUILDER.parent_entity()",
            replacement="$SPAWNER.target_entity()",
            description="parent_entity() renamed to target_entity()"
        ))
        
        # 23. set_parent replaced with insert(ChildOf)
        transformations.append(self.create_transformation(
            pattern="$TARGET.set_parent($PARENT)",
            replacement="",
            description="set_parent replaced with insert(ChildOf(parent))",
            callback=set_parent_callback
        ))
        
        # 24. replace_children pattern
        transformations.append(self.create_transformation(
            pattern="$COMMANDS.entity($PARENT).replace_children(&[$CHILDREN])",
            replacement="$COMMANDS.entity($PARENT).remove::<Children>().add_children(&[$CHILDREN])",
            description="replace_children now requires remove::<Children>() first"
        ))
        
        # ===== ECS - SYSTEM CONFIGURATION =====
        
        # 25. SystemConfigs renamed
        transformations.append(self.create_transformation(
            pattern="SystemConfigs",
            replacement="ScheduleConfigs<ScheduleSystem>",
            description="SystemConfigs renamed to ScheduleConfigs<ScheduleSystem>"
        ))
        
        # 26. IntoSystemConfigs renamed
        transformations.append(self.create_transformation(
            pattern="IntoSystemConfigs",
            replacement="IntoScheduleConfigs<ScheduleSystem, M>",
            description="IntoSystemConfigs renamed to IntoScheduleConfigs"
        ))
        
        # ===== ECS - EVENTS =====
        
        # 27. EventWriter::send renamed to write
        transformations.append(self.create_transformation(
            pattern="$WRITER.send($EVENT)",
            replacement="$WRITER.write($EVENT)",
            description="EventWriter::send renamed to write"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$WRITER.send_batch($EVENTS)",
            replacement="$WRITER.write_batch($EVENTS)",
            description="EventWriter::send_batch renamed to write_batch"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$WRITER.send_default()",
            replacement="$WRITER.write_default()",
            description="EventWriter::send_default renamed to write_default"
        ))
        
        # ===== ECS - COMPONENTS =====
        
        # 28. Required component syntax change
        transformations.append(self.create_transformation(
            pattern="#[require($TYPE($$$FUNC))]",
            replacement="",
            description="Required component syntax updated for 0.16",
            callback=require_attribute_callback
        ))
        
        # 29. Component::register_component_hooks deprecated
        transformations.append(self.create_transformation(
            pattern="fn register_component_hooks(hooks: &mut ComponentHooks)",
            replacement="fn on_add() -> Option<ComponentHook>",
            description="Component::register_component_hooks split into individual methods"
        ))
        
        # ===== ECS - OBSERVERS =====
        
        # 30. Trigger::entity renamed to target
        transformations.append(self.create_transformation(
            pattern="$TRIGGER.entity()",
            replacement="$TRIGGER.target()",
            description="Trigger::entity() renamed to target()"
        ))
        
        # ===== ECS - QUERIES =====
        
        # 31. Query::to_readonly renamed
        transformations.append(self.create_transformation(
            pattern="$QUERY.to_readonly()",
            replacement="$QUERY.as_readonly()",
            description="Query::to_readonly renamed to as_readonly"
        ))
        
        # 32. QueryIter::sort_by lifetime fix
        transformations.append(self.create_transformation(
            pattern="$QUERY.iter().sort_by::<&$C>(Ord::cmp)",
            replacement="$QUERY.iter().sort_by::<&$C>(|l, r| Ord::cmp(l, r))",
            description="QueryIter::sort_by now requires closure for lifetime fix"
        ))
        
        # ===== ECS - WORLD =====
        
        # 33. World::run_system_with_input renamed
        transformations.append(self.create_transformation(
            pattern="$WORLD.run_system_with_input($SYSTEM, $INPUT)",
            replacement="$WORLD.run_system_with($SYSTEM, $INPUT)",
            description="World::run_system_with_input renamed to run_system_with"
        ))
        
        # 34. apply_deferred is now a type
        transformations.append(self.create_transformation(
            pattern="apply_deferred()",
            replacement="ApplyDeferred",
            description="apply_deferred() is now ApplyDeferred type"
        ))
        
        # ===== ECS - MISC =====
        
        # 35. VisitEntities replaced with MapEntities
        transformations.append(self.create_transformation(
            pattern="#[derive(VisitEntities, VisitEntitiesMut)]",
            replacement="#[derive(MapEntities)]",
            description="VisitEntities replaced with MapEntities"
        ))
        
        transformations.append(self.create_transformation(
            pattern="#[visit_entities(ignore)]",
            replacement="// Field not marked with #[entities], so it's ignored by default",
            description="MapEntities uses opt-in #[entities] instead of opt-out"
        ))
        
        # 36. NonSendMarker no longer needs Option<NonSend<_>>
        transformations.append(self.create_transformation(
            pattern="use bevy::core::NonSendMarker",
            replacement="use bevy::ecs::system::NonSendMarker",
            description="NonSendMarker moved to bevy::ecs::system"
        ))
        
        transformations.append(self.create_transformation(
            pattern="_: Option<NonSend<NonSendMarker>>",
            replacement="_: NonSendMarker",
            description="NonSendMarker no longer needs Option<NonSend<_>>"
        ))
        
        # 37. CachedSystemId stores Entity
        transformations.append(self.create_transformation(
            pattern="CachedSystemId::<$S::System>::($ID)",
            replacement="CachedSystemId::<$S>::new($ID)",
            description="CachedSystemId construction changed"
        ))
        
        # ===== INPUT =====
        
        # 38. GamepadInfo removed
        transformations.append(self.create_transformation(
            pattern="GamepadInfo",
            replacement="Name",
            description="GamepadInfo replaced with Name component"
        ))
        
        # ===== MATH =====
        
        # 39. Rot2::angle_between deprecated
        transformations.append(self.create_transformation(
            pattern="$ROT.angle_between($OTHER)",
            replacement="$ROT.angle_to($OTHER)",
            description="Rot2::angle_between deprecated, use angle_to"
        ))
        
        # ===== PICKING =====
        
        # 40. Picking backend renames
        transformations.append(self.create_transformation(
            pattern="MeshPickingBackend",
            replacement="MeshPickingPlugin",
            description="MeshPickingBackend renamed to MeshPickingPlugin"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpritePickingBackend",
            replacement="SpritePickingPlugin",
            description="SpritePickingBackend renamed to SpritePickingPlugin"
        ))
        
        transformations.append(self.create_transformation(
            pattern="UiPickingBackendPlugin",
            replacement="UiPickingPlugin",
            description="UiPickingBackendPlugin renamed to UiPickingPlugin"
        ))
        
        # 41. PickingBehavior renamed to Pickable
        transformations.append(self.create_transformation(
            pattern="PickingBehavior",
            replacement="Pickable",
            description="PickingBehavior renamed to Pickable"
        ))
        
        # 42. RayCastSettings renamed
        transformations.append(self.create_transformation(
            pattern="RayCastSettings",
            replacement="MeshRayCastSettings",
            description="RayCastSettings renamed to MeshRayCastSettings"
        ))
        
        # 43. Pointer event renames
        transformations.append(self.create_transformation(
            pattern="Pointer<Down>",
            replacement="Pointer<Pressed>",
            description="Pointer<Down> renamed to Pointer<Pressed>"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Pointer<Up>",
            replacement="Pointer<Released>",
            description="Pointer<Up> renamed to Pointer<Released>"
        ))
        
        # 44. Focus to hover terminology
        transformations.append(self.create_transformation(
            pattern="PickSet::Focus",
            replacement="PickSet::Hover",
            description="PickSet::Focus renamed to Hover"
        ))
        
        transformations.append(self.create_transformation(
            pattern="PickSet::PostFocus",
            replacement="PickSet::PostHover",
            description="PickSet::PostFocus renamed to PostHover"
        ))
        
        # ===== REFLECTION =====
        
        # 45. ArgList::push methods renamed
        transformations.append(self.create_transformation(
            pattern="$ARGS.push_arg($ARG)",
            replacement="$ARGS.with_arg($ARG)",
            description="ArgList::push_arg renamed to with_arg"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$ARGS.push_ref($REF)",
            replacement="$ARGS.with_ref($REF)",
            description="ArgList::push_ref renamed to with_ref"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$ARGS.push_mut($MUT)",
            replacement="$ARGS.with_mut($MUT)",
            description="ArgList::push_mut renamed to with_mut"
        ))
        
        # 46. PartialReflect::clone_value deprecated
        transformations.append(self.create_transformation(
            pattern="$REFLECT.clone_value()",
            replacement="$REFLECT.to_dynamic()",
            description="PartialReflect::clone_value deprecated, use to_dynamic"
        ))
        
        # 47. Dynamic type clone methods renamed
        transformations.append(self.create_transformation(
            pattern="$ARRAY.clone_dynamic()",
            replacement="$ARRAY.to_dynamic_array()",
            description="Array::clone_dynamic renamed to to_dynamic_array"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$STRUCT.clone_dynamic()",
            replacement="$STRUCT.to_dynamic_struct()",
            description="Struct::clone_dynamic renamed to to_dynamic_struct"
        ))
        
        # ===== RENDERING =====
        
        # 48. Anti-aliasing imports moved
        transformations.append(self.create_transformation(
            pattern="use bevy::core_pipeline::fxaa",
            replacement="use bevy::anti_aliasing::fxaa",
            description="Anti-aliasing moved to bevy::anti_aliasing"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::core_pipeline::smaa",
            replacement="use bevy::anti_aliasing::smaa",
            description="SMAA moved to bevy::anti_aliasing"
        ))
        
        # 49. GpuImage::size is now Extent3d
        transformations.append(self.create_transformation(
            pattern="$GPU_IMAGE.size",
            replacement="$GPU_IMAGE.size_2d()",
            description="GpuImage::size is now Extent3d, use size_2d() for UVec2"
        ))
        
        # 50. Projections no longer components
        transformations.append(self.create_transformation(
            pattern="PerspectiveProjection::default()",
            replacement="Projection::Perspective(PerspectiveProjection::default())",
            description="PerspectiveProjection no longer a component, use Projection"
        ))
        
        transformations.append(self.create_transformation(
            pattern="OrthographicProjection::default()",
            replacement="Projection::Orthographic(OrthographicProjection::default())",
            description="OrthographicProjection no longer a component, use Projection"
        ))
        
        # 51. GpuCulling replaced with NoIndirectDrawing
        transformations.append(self.create_transformation(
            pattern="GpuCulling",
            replacement="NoIndirectDrawing",
            description="GpuCulling removed, use NoIndirectDrawing to opt-out"
        ))
        
        # 52. Anchor is now a struct
        transformations.append(self.create_transformation(
            pattern="Anchor::Custom($VEC)",
            replacement="Anchor($VEC)",
            description="Anchor::Custom removed, use Anchor(vec) constructor"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Anchor::BottomLeft",
            replacement="Anchor::BOTTOM_LEFT",
            description="Anchor::BottomLeft is now Anchor::BOTTOM_LEFT constant"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Anchor::Center",
            replacement="Anchor::CENTER",
            description="Anchor::Center is now Anchor::CENTER constant"
        ))
        
        # 53. TextureAtlas moved to bevy_image
        transformations.append(self.create_transformation(
            pattern="use bevy::sprite::TextureAtlas",
            replacement="use bevy::image::TextureAtlas",
            description="TextureAtlas moved from bevy_sprite to bevy_image"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::sprite::TextureAtlasLayout",
            replacement="use bevy::image::TextureAtlasLayout",
            description="TextureAtlasLayout moved to bevy_image"
        ))
        
        # 54. RenderTarget::Image signature change
        transformations.append(self.create_transformation(
            pattern="RenderTarget::Image($HANDLE)",
            replacement="RenderTarget::Image($HANDLE.into())",
            description="RenderTarget::Image now takes ImageRenderTarget"
        ))
        
        # ===== TEXT =====
        
        # 55. TextFont line_height field added
        # (This is a field addition, handled by ..default() in most cases)
        
        # ===== UI =====
        
        # 56. UiImage renamed to ImageNode
        transformations.append(self.create_transformation(
            pattern="UiImage::new($IMAGE)",
            replacement="ImageNode::new($IMAGE)",
            description="UiImage renamed to ImageNode"
        ))
        
        transformations.append(self.create_transformation(
            pattern="UiImage {",
            replacement="ImageNode {",
            description="UiImage struct renamed to ImageNode"
        ))
        
        # 57. UiImage::texture renamed to image
        transformations.append(self.create_transformation(
            pattern="texture: $IMAGE",
            replacement="image: $IMAGE",
            description="UiImage::texture field renamed to image"
        ))
        
        # 58. TextureAtlas into UiImage
        transformations.append(self.create_transformation(
            pattern="(UiImage::new($IMAGE), TextureAtlas { index: $INDEX, layout: $LAYOUT })",
            replacement="UiImage::from_atlas_image($IMAGE, TextureAtlas { index: $INDEX, layout: $LAYOUT })",
            description="TextureAtlas integrated into UiImage::from_atlas_image"
        ))
        
        # 59. UiBoxShadowSamples renamed
        transformations.append(self.create_transformation(
            pattern="UiBoxShadowSamples",
            replacement="BoxShadowSamples",
            description="UiBoxShadowSamples renamed to BoxShadowSamples"
        ))
        
        # 60. ValArithmeticError typo fix
        transformations.append(self.create_transformation(
            pattern="ValArithmeticError::NonEvaluateable",
            replacement="ValArithmeticError::NonEvaluable",
            description="Fix ValArithmeticError::NonEvaluateable typo"
        ))
        
        # 61. DefaultCameraView renamed
        transformations.append(self.create_transformation(
            pattern="DefaultCameraView",
            replacement="UiCameraView",
            description="DefaultCameraView renamed to UiCameraView"
        ))
        
        # 62. TargetCamera renamed
        transformations.append(self.create_transformation(
            pattern="TargetCamera",
            replacement="UiTargetCamera",
            description="TargetCamera renamed to UiTargetCamera"
        ))
        
        # ===== UTILS REFACTOR =====
        
        # 63. HashMap moved to bevy_platform
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::HashMap",
            replacement="use bevy::platform::collections::HashMap",
            description="HashMap moved to bevy::platform::collections"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy_utils::HashMap",
            replacement="use bevy_platform::collections::HashMap",
            description="HashMap moved to bevy_platform::collections"
        ))
        
        # 64. HashSet moved
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::HashSet",
            replacement="use bevy::platform::collections::HashSet",
            description="HashSet moved to bevy::platform::collections"
        ))
        
        # 65. EntityHash* moved to bevy_ecs
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::EntityHash",
            replacement="use bevy::ecs::entity::EntityHash",
            description="EntityHash moved to bevy::ecs::entity"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::EntityHashMap",
            replacement="use bevy::ecs::entity::EntityHashMap",
            description="EntityHashMap moved to bevy::ecs::entity"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::EntityHashSet",
            replacement="use bevy::ecs::entity::EntityHashSet",
            description="EntityHashSet moved to bevy::ecs::entity"
        ))
        
        # 66. Instant moved to bevy_platform
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::Instant",
            replacement="use bevy::platform::time::Instant",
            description="Instant moved to bevy::platform::time"
        ))
        
        # 67. Logging macros moved to bevy_log
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::info",
            replacement="use bevy::log::info",
            description="Logging macros moved to bevy::log"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::warn",
            replacement="use bevy::log::warn",
            description="warn macro moved to bevy::log"
        ))
        
        # 68. BoxedFuture moved to bevy_tasks
        transformations.append(self.create_transformation(
            pattern="use bevy::utils::BoxedFuture",
            replacement="use bevy::tasks::BoxedFuture",
            description="BoxedFuture moved to bevy::tasks"
        ))
        
        # ===== WINDOWING =====
        
        # 69. WindowMode::Fullscreen signature change
        transformations.append(self.create_transformation(
            pattern="WindowMode::Fullscreen($MONITOR)",
            replacement="WindowMode::Fullscreen($MONITOR, VideoModeSelection::Current)",
            description="WindowMode::Fullscreen now takes VideoModeSelection"
        ))
        
        # ===== BEVY_CORE REMOVAL =====
        
        # 70. FrameCount moved to bevy_diagnostic
        transformations.append(self.create_transformation(
            pattern="use bevy::core::FrameCount",
            replacement="use bevy::diagnostic::FrameCount",
            description="FrameCount moved to bevy::diagnostic"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy_core::FrameCount",
            replacement="use bevy_diagnostic::FrameCount",
            description="FrameCount moved to bevy_diagnostic"
        ))
        
        # 71. Name moved to bevy_ecs
        transformations.append(self.create_transformation(
            pattern="use bevy::core::Name",
            replacement="use bevy::ecs::name::Name",
            description="Name moved to bevy::ecs::name"
        ))
        
        transformations.append(self.create_transformation(
            pattern="use bevy_core::Name",
            replacement="use bevy_ecs::name::Name",
            description="Name moved to bevy_ecs::name"
        ))
        
        # 72. TaskPoolOptions moved to bevy_app
        transformations.append(self.create_transformation(
            pattern="use bevy::core::TaskPoolOptions",
            replacement="use bevy::app::TaskPoolOptions",
            description="TaskPoolOptions moved to bevy::app"
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
            self.logger.info("Executing pre-migration steps for 0.15 -> 0.16")
            
            rust_files = self.file_manager.find_rust_files()
            
            # Check for patterns that will change
            ecs_files = self.find_files_with_pattern("Query::single")
            if ecs_files:
                self.logger.info(f"Found {len(ecs_files)} files using Query::single (now returns Result)")
            
            parent_files = self.find_files_with_pattern("Parent")
            if parent_files:
                self.logger.info(f"Found {len(parent_files)} files using Parent (renamed to ChildOf)")
            
            utils_files = self.find_files_with_pattern("bevy::utils::")
            if utils_files:
                self.logger.info(f"Found {len(utils_files)} files using bevy::utils (refactored)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        """Execute steps after applying transformations"""
        try:
            self.logger.info("Executing post-migration steps for 0.15 -> 0.16")
            
            # Additional Cargo.toml tweaks for 0.16
            cargo_toml_path = self.file_manager.find_cargo_toml()
            if cargo_toml_path:
                content = cargo_toml_path.read_text(encoding='utf-8')
                original_content = content
                
                # Update edition to 2024 if still on 2021
                if 'edition = "2021"' in content:
                    content = content.replace('edition = "2021"', 'edition = "2024"')
                    self.logger.info("Updated Rust edition to 2024")
                
                # Update track_change_detection feature to track_location
                if 'track_change_detection' in content:
                    content = content.replace('track_change_detection', 'track_location')
                    self.logger.info("Updated track_change_detection feature to track_location")
                
                if content != original_content:
                    cargo_toml_path.write_text(content, encoding='utf-8')
                    self.logger.info("Updated Cargo.toml features and edition for Bevy 0.16")
            
            # Check for manual migration patterns
            self._check_for_manual_migration_needed()
            
            self.logger.info("=" * 60)
            self.logger.info("Migration to Bevy 0.16 complete!")
            self.logger.info("Next steps:")
            self.logger.info("1. Review error handling changes (Query::single now returns Result)")
            self.logger.info("2. Update entity relationships (Parent → ChildOf)")
            self.logger.info("3. Fix import paths (bevy_utils refactor)")
            self.logger.info("4. Run 'cargo check' to verify compilation")
            self.logger.info("5. Consider enabling Rust 2024 edition in Cargo.toml")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    

    
    def _check_for_manual_migration_needed(self) -> None:
        """Check for patterns that might need manual migration"""
        try:
            manual_patterns = [
                ("fn.*->.*Result", "Systems may need to return Result for error handling"),
                ("despawn_recursive", "despawn() is now recursive by default - review despawn logic"),
                ("ChildBuilder", "ChildBuilder renamed to ChildSpawnerCommands - update closures"),
                ("bevy_utils::", "bevy_utils refactored - many items moved to bevy_platform"),
                ("PerspectiveProjection", "Projections no longer components - use Projection enum"),
                ("TextureAtlas", "TextureAtlas moved to bevy_image - update imports"),
                ("no_std", "Consider enabling no_std features if targeting embedded platforms"),
                ("Volume\\(", "Volume is now an enum - use Volume::Linear or Volume::Decibels"),
            ]
            
            rust_files = self.file_manager.find_rust_files()
            
            for pattern, message in manual_patterns:
                files_with_pattern = []
                for file_path in rust_files:
                    content = self.file_manager.read_file_content(file_path)
                    if content and re.search(pattern, content):
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
            cargo_toml_path = self.file_manager.find_cargo_toml()
            if cargo_toml_path:
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                if re.search(r'bevy\s*=\s*["\']0\.15', content):
                    self.logger.info("Confirmed Bevy 0.15 dependency in Cargo.toml")
                elif re.search(r'bevy\s*=.*version\s*=\s*["\']0\.15', content):
                    self.logger.info("Confirmed Bevy 0.15 dependency in Cargo.toml")
                else:
                    self.logger.warning("Could not confirm Bevy 0.15 dependency in Cargo.toml")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False
