"""
Migration from Bevy 0.17 to 0.18
Comprehensive migration covering 80+ breaking changes
"""

import logging
import re
from pathlib import Path
from typing import Dict, List

from bevymigrate.migrations.base_migration import BaseMigration, MigrationResult
from bevymigrate.core.ast_processor import ASTTransformation




class Migration_0_17_to_0_18(BaseMigration):
    """
    Migration class for Bevy 0.17 → 0.18
    
    Key changes:
    - RenderTarget split into component
    - Entity row → index terminology
    - Mesh try_* methods for RENDER_WORLD-only meshes
    - BorderRadius component → Node field
    - LineHeight component (was TextFont field)
    - AnimationTarget split into two components
    - AmbientLight split into component + resource
    - Feature renames and many API refinements
    """
    
    @property
    def from_version(self) -> str:
        return "0.17"
    
    @property
    def to_version(self) -> str:
        return "0.18"
    
    @property
    def description(self) -> str:
        return "Bevy 0.17 → 0.18: RenderTarget component, Entity API, Mesh try_* methods, BorderRadius, and 80+ changes"
    
    def get_transformations(self) -> List[ASTTransformation]:
        transformations = []

        def animation_target_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            full = vars.get("_matched_text", "")
            # Extract fields from AnimationTarget { id: ..., player: ... }
            # Matches both possible orders and handle nested AnimationTargetId
            id_m = re.search(r"id:\s*(AnimationTargetId\([^)]+\)|[^,\s{}]+)", full)
            player_m = re.search(r"player:\s*([^,\s{}]+)", full)
            
            if id_m and player_m:
                id_val = id_m.group(1).strip()
                player_val = player_m.group(1).strip()
                
                if not id_val.startswith("AnimationTargetId"):
                    id_val = f"AnimationTargetId({id_val})"
                
                return f"({id_val}, AnimatedBy({player_val}))"
            return full

        def image_render_target_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            full = vars.get("_matched_text", "")
            # Remove FloatOrd wrapper specifically for scale_factor field
            # This is safer than a global string replacement
            return re.sub(r"(scale_factor:\s*)FloatOrd\(([^)]+)\)", r"\1\2", full)

        def render_target_callback(vars: Dict[str, str], file_path: Path, match: Dict[str, Any]) -> str:
            full = vars.get("_matched_text", "")
            # Extract content between Camera { and }
            inner_m = re.search(r"Camera\s*\{\s*(.*)\s*\}", full, re.DOTALL)
            if not inner_m:
                return full
            inner = inner_m.group(1).strip()
            
            # Split by comma balancing () and {}
            items = []
            curr = ""
            d = 0
            for c in inner:
                if c in '({': d += 1
                elif c in ')}': d -= 1
                if c == ',' and d == 0:
                    items.append(curr.strip())
                    curr = ""
                else:
                    curr += c
            if curr.strip():
                items.append(curr.strip())
            
            target_val = None
            remaining_items = []
            for item in items:
                if item.startswith("target:"):
                    target_val = item[len("target:"):].strip()
                else:
                    remaining_items.append(item)
            
            if not target_val:
                return full
            
            # Filter out ..default() from remaining items to check if anything else exists
            subst_items = []
            for it in remaining_items:
                clean_it = it.strip()
                if clean_it and clean_it != "..default()":
                    subst_items.append(clean_it)
            
            if not subst_items:
                return target_val
            else:
                rest_str = ", ".join(remaining_items)
                return f"(Camera {{ {rest_str} }}, {target_val})"
        
        # ===== ENTITY API CHANGES (15 transformations) =====
        
        # Entity row → index terminology
        transformations.append(self.create_transformation(
            pattern="EntityRow",
            replacement="EntityIndex",
            description="EntityRow renamed to EntityIndex"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$ENTITY.row()",
            replacement="$ENTITY.index()",
            description="Entity::row() → index()"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Entity::from_row",
            replacement="Entity::from_index",
            description="Entity::from_row → from_index"
        ))
        
        transformations.append(self.create_transformation(
            pattern="EntityDoesNotExistError",
            replacement="EntityNotSpawnedError",
            description="EntityDoesNotExistError → EntityNotSpawnedError"
        ))
        
        transformations.append(self.create_transformation(
            pattern="BundleSpawner::spawn_non_existent",
            replacement="BundleSpawner::construct",
            description="spawn_non_existent → construct"
        ))
        
        transformations.append(self.create_transformation(
            pattern="QueryEntityError::EntityDoesNotExist",
            replacement="QueryEntityError::NotSpawned",
            description="EntityDoesNotExist → NotSpawned"
        ))
        
        # ===== UI CHANGES (10 transformations) =====
        
        # clear_* → detach_*
        transformations.append(self.create_transformation(
            pattern="$ENTITY.clear_children()",
            replacement="$ENTITY.detach_all_children()",
            description="clear_children → detach_all_children"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$ENTITY.remove_children",
            replacement="$ENTITY.detach_children",
            description="remove_children → detach_children"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$ENTITY.remove_child",
            replacement="$ENTITY.detach_child",
            description="remove_child → detach_child"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$ENTITY.clear_related",
            replacement="$ENTITY.detach_all_related",
            description="clear_related → detach_all_related"
        ))
        
        # ===== ANIMATION CHANGES (3 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="AnimationEventTrigger { animation_player:",
            replacement="AnimationEventTrigger { target:",
            description="animation_player field → target"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$ENTITY.animation_player",
            replacement="$ENTITY.target",
            description="AnimationEventTrigger.animation_player → target"
        ))
        
        transformations.append(self.create_transformation(
            pattern="AnimationTarget { $$$ }",
            replacement="",
            description="AnimationTarget split into AnimationTargetId and AnimatedBy",
            callback=animation_target_callback
        ))
        
        # ===== FEATURE RENAMES (5 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern='features = ["animation"]',
            replacement='features = ["gltf_animation"]',
            description="animation feature → gltf_animation"
        ))
        
        transformations.append(self.create_transformation(
            pattern='features = ["bevy_sprite_picking_backend"]',
            replacement='features = ["sprite_picking"]',
            description="bevy_sprite_picking_backend → sprite_picking"
        ))
        
        transformations.append(self.create_transformation(
            pattern='features = ["bevy_ui_picking_backend"]',
            replacement='features = ["ui_picking"]',
            description="bevy_ui_picking_backend → ui_picking"
        ))
        
        transformations.append(self.create_transformation(
            pattern='features = ["bevy_mesh_picking_backend"]',
            replacement='features = ["mesh_picking"]',
            description="bevy_mesh_picking_backend → mesh_picking"
        ))
        
        transformations.append(self.create_transformation(
            pattern='features = ["documentation"]',
            replacement='features = ["reflect_documentation"]',
            description="documentation → reflect_documentation"
        ))
        
        # ===== REFLECTION CHANGES (2 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="#[reflect[$_]]",
            replacement="#[reflect($_)]",
            description="#[reflect[...]] → #[reflect(...)]"
        ))
        
        transformations.append(self.create_transformation(
            pattern="#[reflect{$_}]",
            replacement="#[reflect($_)]",
            description="#[reflect{...}] → #[reflect(...)]"
        ))
        
        # ===== ASSET CHANGES (3 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="sender.send(AssetSourceEvent::",
            replacement="sender.send_blocking(AssetSourceEvent::",
            description="async_channel::Sender uses send_blocking"
        ))
        
        transformations.append(self.create_transformation(
            pattern="LoadContext::asset_path()",
            replacement="LoadContext::path()",
            description="asset_path() removed, use path()"
        ))
        
        # ===== SYSTEM CHANGES (3 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="SimpleExecutor",
            replacement="SingleThreadedExecutor",
            description="SimpleExecutor removed, use SingleThreadedExecutor"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$STATE.set($VALUE)",
            replacement="$STATE.set_if_neq($VALUE) // or .set() to always trigger",
            description="NextState::set now always triggers transitions"
        ))
        
        # ===== MISC CHANGES (10 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="TickCells",
            replacement="ComponentTickCells",
            description="TickCells → ComponentTickCells"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ThinSlicePtr::get(",
            replacement="ThinSlicePtr::get_unchecked(",
            description="get() → get_unchecked()"
        ))
        
        transformations.append(self.create_transformation(
            pattern="dangling_with_align($ALIGN)",
            replacement="NonNull::without_provenance($ALIGN)",
            description="dangling_with_align removed"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Gizmos::cuboid",
            replacement="Gizmos::cube",
            description="cuboid → cube"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Internal",
            replacement="// Internal component removed",
            description="Internal component removed"
        ))
        
        transformations.append(self.create_transformation(
            pattern="HashMap::get_many_mut",
            replacement="HashMap::get_disjoint_mut",
            description="get_many_mut → get_disjoint_mut"
        ))
        
        transformations.append(self.create_transformation(
            pattern="HashMap::get_many_unchecked_mut",
            replacement="HashMap::get_disjoint_unchecked_mut",
            description="get_many_unchecked_mut → get_disjoint_unchecked_mut"
        ))
        
        transformations.append(self.create_transformation(
            pattern="HashMap::get_many_key_value_mut",
            replacement="HashMap::get_disjoint_key_value_mut",
            description="get_many_key_value_mut → get_disjoint_key_value_mut"
        ))
        
        transformations.append(self.create_transformation(
            pattern="TrackedRenderPass::set_index_buffer($BUFFER, $OFFSET, $FORMAT)",
            replacement="TrackedRenderPass::set_index_buffer($BUFFER, $FORMAT)",
            description="set_index_buffer no longer takes offset"
        ))
        
        # ===== RENDERING CHANGES (10 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="MaterialDrawFunction",
            replacement="MainPassOpaqueDrawFunction",
            description="MaterialDrawFunction → MainPassOpaqueDrawFunction"
        ))
        
        transformations.append(self.create_transformation(
            pattern="PrepassDrawFunction",
            replacement="PrepassOpaqueDrawFunction",
            description="PrepassDrawFunction → PrepassOpaqueDrawFunction"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DeferredDrawFunction",
            replacement="DeferredOpaqueDrawFunction",
            description="DeferredDrawFunction → DeferredOpaqueDrawFunction"
        ))
        
        transformations.append(self.create_transformation(
            pattern="RenderGraphApp",
            replacement="RenderGraphExt",
            description="RenderGraphApp → RenderGraphExt"
        ))
        
        transformations.append(self.create_transformation(
            pattern="FULLSCREEN_SHADER_HANDLE",
            replacement="FullscreenShader",
            description="FULLSCREEN_SHADER_HANDLE → FullscreenShader resource"
        ))
        
        # Camera RenderTarget now component
        transformations.append(self.create_transformation(
            pattern="Camera { $$$ }",
            replacement="",
            description="RenderTarget moved from Camera field to component",
            callback=render_target_callback
        ))
        
        transformations.append(self.create_transformation(
            pattern="ExtractedUiNode { $$$PRE, stack_index: $VAL, $$$POST }",
            replacement="ExtractedUiNode { $$$PRE, z_order: $VAL, $$$POST }",
            description="stack_index → z_order (now f32)"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ImageRenderTarget { $$$ }",
            replacement="",
            description="scale_factor is now f32, no FloatOrd wrapper",
            callback=image_render_target_callback
        ))
        
        # Atmosphere changes
        transformations.append(self.create_transformation(
            pattern="Atmosphere::default()",
            replacement="Atmosphere::earthlike(scattering_mediums.add(ScatteringMedium::default()))",
            description="Atmosphere no longer implements Default"
        ))
        
        transformations.append(self.create_transformation(
            pattern="MaterialPlugin { $$$PRE, prepass_enabled: $VAL, $$$POST }",
            replacement="MaterialPlugin { $$$PRE, /* prepass_enabled: $VAL moved to Material::enable_prepass() */ $$$POST }",
            description="MaterialPlugin fields moved to Material methods"
        ))
        
        # ===== COMPONENT/RESOURCE CHANGES (5 transformations) =====
        
        # AmbientLight resource → GlobalAmbientLight (YAML rule with context)
        ambient_light_rule = """
id: ambient-light-resource
language: rust
rule:
  any:
    - pattern: $OBJ.insert_resource(AmbientLight { $$$ARGS })
    - pattern: $OBJ.insert_resource(AmbientLight::default())
fix: $OBJ.insert_resource(GlobalAmbientLight { $$$ARGS })
"""
        transformations.append(self.create_transformation(
            pattern="",
            replacement="",
            description="AmbientLight resource → GlobalAmbientLight",
            rule_yaml=ambient_light_rule
        ))

        transformations.append(self.create_transformation(
            pattern=".init_resource::<AmbientLight>()",
            replacement=".init_resource::<GlobalAmbientLight>()",
            description="init_resource::<AmbientLight> → GlobalAmbientLight"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ResMut<AmbientLight>",
            replacement="ResMut<GlobalAmbientLight>",
            description="AmbientLight resource → GlobalAmbientLight"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Res<AmbientLight>",
            replacement="Res<GlobalAmbientLight>",
            description="AmbientLight resource → GlobalAmbientLight"
        ))
        
        transformations.append(self.create_transformation(
            pattern="FontAtlasSets",
            replacement="FontAtlasSet",
            description="FontAtlasSets → FontAtlasSet resource"
        ))
        
        transformations.append(self.create_transformation(
            pattern="NoAutoAabb",
            replacement="NoAutoAabb // New component to disable auto Aabb",
            description="NoAutoAabb component (new in 0.18)"
        ))
        
        # ===== QUERY/ECS CHANGES (5 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="fn requires_exact_size<D: QueryData>",
            replacement="fn requires_exact_size<D: ArchetypeQueryData>",
            description="QueryData → ArchetypeQueryData for ExactSizeIterator"
        ))
        
        transformations.append(self.create_transformation(
            pattern="get_components(",
            replacement="get_components( // Now returns Result",
            description="get_components returns Result instead of Option"
        ))
        
        transformations.append(self.create_transformation(
            pattern="get_components_mut_unchecked(",
            replacement="get_components_mut_unchecked( // Now returns Result",
            description="get_components_mut_unchecked returns Result"
        ))
        
        transformations.append(self.create_transformation(
            pattern="#[derive(Resource)]",
            replacement="#[derive(Resource)] // Must use 'static lifetime",
            description="Resource derive requires 'static lifetime"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Reader for",
            replacement="Reader for // Must implement seekable() method",
            description="Reader trait requires seekable() implementation"
        ))
        
        # ===== WINIT/INPUT CHANGES (3 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="EventLoopProxyWrapper<WakeUp>",
            replacement="EventLoopProxyWrapper // No longer generic",
            description="WinitPlugin no longer generic over Message type"
        ))
        
        transformations.append(self.create_transformation(
            pattern="event_loop_proxy.send_event(WakeUp)",
            replacement="event_loop_proxy.send_event(WinitUserEvent::WakeUp)",
            description="WakeUp → WinitUserEvent::WakeUp"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DragEnter",
            replacement="DragEnter // Now also fires on drag starts",
            description="DragEnter behavior changed"
        ))
        
        # GltfPlugin changes using callback (Simple pattern that ast-grep likes)
        transformations.append(self.create_transformation(
            pattern="GltfPlugin { $$$ }",
            replacement="",
            description="GltfPlugin use_model_forward_direction → convert_coordinates",
            callback=lambda vars, _: (
                full := vars.get("_matched_text", "").strip(),
                val := m.group(1).strip().lower() if (m := re.search(r"use_model_forward_direction:\s*(true|false|[^,}]+)", full)) else "true",
                repl := f"convert_coordinates: {('Some(' if 'GltfLoaderSettings' in full else '')}GltfConvertCoordinates {{ rotate_scene_entity: {val}, ..default() }}{(')' if 'GltfLoaderSettings' in full else '')}",
                re.sub(r"use_model_forward_direction:\s*(true|false|[^,}]+)", repl, full)
            )[-1] if vars.get("_matched_text") and "use_model_forward_direction" in vars.get("_matched_text") else vars.get("_matched_text", "")
        ))
        
        # Also for loader settings
        transformations.append(self.create_transformation(
            pattern="GltfLoaderSettings { $$$ }",
            replacement="",
            description="GltfLoaderSettings use_model_forward_direction → convert_coordinates",
            callback=lambda vars, _: (
                full := vars.get("_matched_text", "").strip(),
                val := m.group(1).strip().lower() if (m := re.search(r"use_model_forward_direction:\s*(true|false|[^,}]+)", full)) else "true",
                repl := f"convert_coordinates: {('Some(' if 'GltfLoaderSettings' in full else '')}GltfConvertCoordinates {{ rotate_scene_entity: {val}, ..default() }}{(')' if 'GltfLoaderSettings' in full else '')}",
                re.sub(r"use_model_forward_direction:\s*(true|false|[^,}]+)", repl, full)
            )[-1] if vars.get("_matched_text") and "use_model_forward_direction" in vars.get("_matched_text") else vars.get("_matched_text", "")
        ))
        
        # ===== SCHEDULE/GRAPH CHANGES (3 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="ScheduleGraph::topsort_graph",
            replacement="DiGraph::toposort",
            description="topsort_graph moved to DiGraph"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DiGraph::try_into",
            replacement="DiGraph::try_convert",
            description="try_into → try_convert (avoid TryInto trait overlap)"
        ))
        
        transformations.append(self.create_transformation(
            pattern="UnGraph::try_into",
            replacement="UnGraph::try_convert",
            description="try_into → try_convert"
        ))
        
        # ===== BIND GROUP CHANGES (2 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="render_device.create_bind_group_layout(",
            replacement="BindGroupLayoutDescriptor::new( // Now use descriptor",
            description="BindGroupLayout → BindGroupLayoutDescriptor"
        ))
        
        transformations.append(self.create_transformation(
            pattern="fn label() -> Option<&'static str>",
            replacement="fn label() -> &'static str // No longer optional",
            description="BindGroupLayout labels no longer optional"
        ))
        
        # ===== IMAGE/TEXTURE CHANGES (3 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="Image::reinterpret_size(",
            replacement="Image::reinterpret_size( // Now returns Result",
            description="reinterpret_size returns Result"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Image::reinterpret_stacked_2d_as_array(",
            replacement="Image::reinterpret_stacked_2d_as_array( // Now returns Result",
            description="reinterpret_stacked_2d_as_array returns Result"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ImageLoaderSettings",
            replacement="ImageLoaderSettings // New array_layout field",
            description="ImageLoaderSettings supports array textures"
        ))
        
        # ===== TILEMAP CHANGES (1 transformation) =====
        
        transformations.append(self.create_transformation(
            pattern="TilemapChunk",
            replacement="TilemapChunk // Origin now bottom-left",
            description="TilemapChunk origin changed to bottom-left"
        ))
        
        # ===== BEVY MANIFEST (1 transformation) =====
        
        transformations.append(self.create_transformation(
            pattern="let manifest = BevyManifest::shared();",
            replacement="let result = BevyManifest::shared(|manifest| { /* use manifest */ });",
            description="BevyManifest::shared is now scope-like API"
        ))
        
        # ===== COLUMN CHANGES (1 transformation) =====
        
        transformations.append(self.create_transformation(
            pattern="ThinColumn",
            replacement="Column // ThinColumn merged into Column",
            description="ThinColumn merged into Column"
        ))
        
        # ===== BORDERRADIUS/LINEHEIGHT CHANGES (2 transformations) =====
        
        # BorderRadius is now Node field, not component
        transformations.append(self.create_transformation(
            pattern="commands.spawn((Node::default(), BorderRadius::",
            replacement="commands.spawn(Node { border_radius: BorderRadius::",
            description="BorderRadius is now Node field, not component"
        ))
        
        # LineHeight is now separate component
        transformations.append(self.create_transformation(
            pattern="TextFont { line_height:",
            replacement="// LineHeight is now separate component",
            description="LineHeight removed from TextFont, now separate component"
        ))
        
        # ===== TEXT LAYOUT CHANGES (1 transformation) =====
        
        transformations.append(self.create_transformation(
            pattern="TextLayoutInfo { section_rects:",
            replacement="TextLayoutInfo { run_geometry:",
            description="section_rects → run_geometry"
        ))
        
        # ===== BUNDLE CHANGES (2 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="fn component_ids(components: &mut ComponentsRegistrator, ids: &mut impl FnMut(ComponentId))",
            replacement="fn component_ids(components: &mut ComponentsRegistrator) -> impl Iterator<Item = ComponentId>",
            description="Bundle::component_ids returns iterator"
        ))
        
        transformations.append(self.create_transformation(
            pattern="fn get_component_ids(components: &Components, ids: &mut impl FnMut(Option<ComponentId>))",
            replacement="fn get_component_ids(components: &Components) -> impl Iterator<Item = Option<ComponentId>>",
            description="Bundle::get_component_ids returns iterator"
        ))
        
        # ===== ASSET SOURCE CHANGES (2 transformations) =====
        
        transformations.append(self.create_transformation(
            pattern="AssetSource::build()",
            replacement="AssetSourceBuilder::new(move || /* reader */)",
            description="AssetSource::build → AssetSourceBuilder::new"
        ))
        
        transformations.append(self.create_transformation(
            pattern="AssetServer::new($SOURCES,",
            replacement="AssetServer::new(Arc::new($SOURCES),",
            description="AssetServer::new takes Arc<AssetSources>"
        ))
        
        # ===== PROCESS TRAIT CHANGES (1 transformation) =====
        
        transformations.append(self.create_transformation(
            pattern="context.asset_bytes()",
            replacement="context.asset_reader() // Read bytes manually",
            description="ProcessContext.asset_bytes → asset_reader"
        ))
        
        # ===== ASSET LOADER CHANGES (1 transformation) =====
        
        transformations.append(self.create_transformation(
            pattern="impl AssetLoader for",
            replacement="#[derive(TypePath)]\nimpl AssetLoader for // Requires TypePath",
            description="AssetLoader requires TypePath trait"
        ))
        
        # BorderRect changes using callback
        transformations.append(self.create_transformation(
            pattern="BorderRect { $$$ }",
            replacement="",
            description="BorderRect fields changed to Vec2 (min_inset, max_inset)",
            callback=lambda vars, _: (
                full := vars.get("_matched_text", ""),
                l := re.search(r"left:\s*([^,}]+)", full),
                r := re.search(r"right:\s*([^,}]+)", full),
                t := re.search(r"top:\s*([^,}]+)", full),
                b := re.search(r"bottom:\s*([^,}]+)", full),
                f"BorderRect {{ min_inset: Vec2::new({(l.group(1).strip() if l else '0.0')}, {(t.group(1).strip() if t else '0.0')}), max_inset: Vec2::new({(r.group(1).strip() if r else '0.0')}, {(b.group(1).strip() if b else '0.0')}) }}"
            )[-1]
        ))
        
        # AssetProcessor::new tuple return
        asset_proc_rule = """
id: asset-processor-new
language: rust
rule:
  kind: let_declaration
  pattern: "let $P = AssetProcessor::new($S)"
"""
        transformations.append(self.create_transformation(
            pattern="",
            replacement="",
            description="AssetProcessor::new now returns tuple",
            rule_yaml=asset_proc_rule,
            callback=lambda vars, _: (
                full := vars.get("_matched_text", ""),
                m := re.search(r"let\s+(\w+)\s*=\s*AssetProcessor::new\(([^)]+)\)", full),
                f"let ({m.group(1)}, _sources) = AssetProcessor::new({m.group(2)}, false)" if m else full
            )[-1]
        ))
        
        # ===== COMPONENT DESCRIPTOR CHANGES (1 transformation) =====
        
        transformations.append(self.create_transformation(
            pattern="ComponentDescriptor::new_with_layout($$$ARGS)",
            replacement="ComponentDescriptor::new_with_layout($$$ARGS /* Requires relationship_accessor param */)",
            description="ComponentDescriptor requires relationship_accessor"
        ))
        
        # ===== BEVY_GIZMOS SPLIT (1 transformation) =====
        
        transformations.append(self.create_transformation(
            pattern='features = ["bevy_gizmos"]',
            replacement='features = ["bevy_gizmos", "bevy_gizmos_render"]',
            description="bevy_gizmos rendering split to bevy_gizmos_render"
        ))
        
        # ===== STATE MANAGEMENT CHANGES (TODOMIGRATE) =====
        
        transformations.append(self.create_transformation(
            pattern="Res<State<$S>>",
            replacement="State<$S>",
            description="Res<State<S>> -> State<S>"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ResMut<NextState<$S>>",
            replacement="NextState<$S>",
            description="ResMut<NextState<S>> -> NextState<S>"
        ))

        # ===== EVENTS -> MESSAGES (Bevy Adventure) =====
        
        transformations.append(self.create_transformation(
            pattern=".add_event::<$T>()",
            replacement=".add_message::<$T>()",
            description="App::add_event -> App::add_message"
        ))
        
        transformations.append(self.create_transformation(
            pattern="EventWriter<$T>",
            replacement="MessageWriter<$T>",
            description="EventWriter -> MessageWriter"
        ))
        
        transformations.append(self.create_transformation(
            pattern="EventReader<$T>",
            replacement="MessageReader<$T>",
            description="EventReader -> MessageReader"
        ))

        # ===== INPUT API CHANGES =====
        
        # Only replacing inside Res/ResMut to be safe as per TODOMIGRATE
        transformations.append(self.create_transformation(
            pattern="Res<Input<$T>>",
            replacement="Res<ButtonInput<$T>>",
            description="Res<Input<T>> -> Res<ButtonInput<T>>"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ResMut<Input<$T>>",
            replacement="ResMut<ButtonInput<$T>>",
            description="ResMut<Input<T>> -> ResMut<ButtonInput<T>>"
        ))

        # ===== ENTITY COMMANDS =====
        
        transformations.append(self.create_transformation(
            pattern="$ENTITY.despawn_recursive()",
            replacement="$ENTITY.despawn()",
            description="despawn_recursive -> despawn"
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
            self.logger.info("BEVY 0.17 → 0.18 MIGRATION")
            self.logger.info("=" * 60)
            self.logger.info("Key changes:")
            self.logger.info("  - RenderTarget → Component")
            self.logger.info("  - Entity row → index")
            self.logger.info("  - Mesh try_* methods")
            self.logger.info("  - BorderRadius → Node field")
            self.logger.info("  - Feature renames")
            self.logger.info("=" * 60)
            
            # Check for Entity API usage
            entity_files = self.find_files_with_pattern("EntityRow")
            if entity_files:
                self.logger.info(f"Found {len(entity_files)} files using EntityRow (will rename)")
            
            # Check for UI changes
            ui_files = self.find_files_with_pattern("clear_children")
            if ui_files:
                self.logger.info(f"Found {len(ui_files)} files using clear_children (will rename)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        try:
            # Additional Cargo.toml tweaks for 0.18
            cargo_toml_path = self.file_manager.find_cargo_toml()
            
            if cargo_toml_path:
                content = cargo_toml_path.read_text(encoding='utf-8')
                original_content = content
                
                # Update feature names
                content = content.replace('"animation"', '"gltf_animation"')
                content = content.replace('"bevy_sprite_picking_backend"', '"sprite_picking"')
                content = content.replace('"bevy_ui_picking_backend"', '"ui_picking"')
                content = content.replace('"bevy_mesh_picking_backend"', '"mesh_picking"')
                content = content.replace('"documentation"', '"reflect_documentation"')
                
                if content != original_content:
                    cargo_toml_path.write_text(content, encoding='utf-8')
                    self.logger.info("Updated Cargo.toml feature names for Bevy 0.18")
            
            self.logger.info("=" * 60)
            self.logger.info("Migration to Bevy 0.18 complete!")
            self.logger.info("=" * 60)
            self.logger.info("Manual migration required for:")
            self.logger.info("  - RenderTarget: Move from Camera field to component")
            self.logger.info("  - BorderRadius: Move from component to Node field")
            self.logger.info("  - LineHeight: Now separate component")
            self.logger.info("  - AnimationTarget: Split into AnimationTargetId + AnimatedBy")
            self.logger.info("  - AmbientLight: Split into GlobalAmbientLight + AmbientLight")
            self.logger.info("  - Mesh methods: Use try_* variants for RENDER_WORLD meshes")
            self.logger.info("  - Entity::index(): Old method -> index_u32()")
            self.logger.info("  - Rapier Physics: Update raycast signatures (API changed)")
            self.logger.info("  - Query::get_single_mut(): Returns Result now, check unwrap/handling")
            self.logger.info("  - State SystemParam: Check for 'where S: FreelyMutableState' bounds")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def validate_preconditions(self) -> bool:
        if not super().validate_preconditions():
            return False
        
        try:
            cargo_toml_path = self.file_manager.find_cargo_toml()
            if cargo_toml_path:
                content = cargo_toml_path.read_text(encoding='utf-8')
                
                if not re.search(r'bevy\s*=\s*["\']0\.17', content):
                    self.logger.warning("Expected Bevy 0.17 in Cargo.toml")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False