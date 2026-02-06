import re
import sys
from typing import List

from bevymigrate.core.ast_processor import ASTTransformation
from bevymigrate.migrations.base_migration import BaseMigration


class Migration_0_18_to_0_19_Part1(BaseMigration):
    @property
    def from_version(self) -> str:
        return "0.18"

    @property
    def to_version(self) -> str:
        return "0.19-part1"

    @property
    def description(self) -> str:
        return "Bevy 0.18 → 0.19 Part 1: Messages API, observer renames, reflect reorg, and core renames"

    def get_transformations(self) -> List[ASTTransformation]:
        transformations = []

        # Event methods and types
        event_renames = {
            "EventWriter": "MessageWriter",
            "EventReader": "MessageReader",
            "Events": "Messages",
            "BufferedEvent": "Message",
            "BufferedEventReader": "MessageReader",
            "BufferedEventWriter": "MessageWriter",
            "BufferedEventCursor": "MessageCursor",
        }
        for old, new in event_renames.items():
            transformations.append(self.create_transformation(
                pattern=old,
                replacement=new,
                description=f"{old} renamed to {new}"
            ))

        # World/Commands methods
        method_renames = {
            "send_event": "write_message",
            "send_event_default": "write_message_default",
            "send_event_batch": "write_message_batch",
            "trigger_targets": "trigger",
        }
        for old, new in method_renames.items():
            transformations.append(self.create_transformation(
                pattern=f"$OBJ.{old}($($$ARGS))",
                replacement=f"$OBJ.{new}($($$ARGS))",
                description=f"{old} renamed to {new}"
            ))

        # Events::send renames
        transformations.append(self.create_transformation(
            pattern="Events::send",
            replacement="Messages::write",
            description="Events::send renamed to Messages::write"
        ))

        # Trigger to On
        transformations.append(self.create_transformation(
            pattern="Trigger<$E>",
            replacement="On<$E>",
            description="Trigger renamed to On"
        ))

        transformations.append(self.create_transformation(
            pattern="Trigger<$E, $F>",
            replacement="On<$E, $F>",
            description="Trigger with filter renamed to On"
        ))

        # Lifecycle renames
        lifecycle = {"OnAdd": "Add", "OnInsert": "Insert", "OnReplace": "Replace", "OnRemove": "Remove", "OnDespawn": "Despawn"}
        for old, new in lifecycle.items():
            transformations.append(self.create_transformation(
                pattern=old,
                replacement=new,
                description=f"{old} renamed to {new}"
            ))

        transformations.append(self.create_transformation(
            pattern="$TRIGGER.target()",
            replacement="$TRIGGER.entity",
            description="trigger.target() renamed to event.entity"
        ))

        # EntityEvent conversion (Atomic)
        entity_event_rule = """
id: entity-event-combined
language: rust
rule:
  kind: struct_item
"""
        def entity_event_callback(vars, file_path, match):
            v = vars.get("_matched_text", "")
            start = match['range']['byteOffset']['start']
            
            try:
                # We need to read the file content as it was before this transformation
                # but with newline='' to match offsets.
                with open(file_path, 'r', encoding='utf-8', newline='') as f:
                    full_content = f.read()
                
                # Look back from 'start' for #[derive(Event)]
                # 100 chars should be plenty for attributes and whitespace
                lookback_area = full_content[max(0, start-100):start]
                if "#[derive(Event)]" in lookback_area or "derive(Event)" in lookback_area:
                    # Perform the transformation on the struct body
                    v = re.sub(r"struct\s+(\w+)\s*;", r"struct \1 { entity: Entity }", v) if ";" in v and "{" not in v else (
                        re.sub(r"(struct\s+\w+\s*\{)", r"\1\n    entity: Entity,", v) if "entity: Entity" not in v else v
                    )
            except Exception:
                pass
            return v

        transformations.append(self.create_transformation(
            pattern="",
            replacement="",
            description="Event struct -> EntityEvent (body)",
            rule_yaml=entity_event_rule,
            callback=entity_event_callback
        ))

        # Rule for the attribute
        transformations.append(self.create_transformation(
            pattern="#[derive(Event)]",
            replacement="#[derive(EntityEvent)]",
            description="Event derive -> EntityEvent derive"
        ))

        transformations.append(self.create_transformation(
            pattern="bevy_camera::primitives::HalfSpace",
            replacement="bevy_math::primitives::HalfSpace",
            description="HalfSpace moved to bevy_math::primitives"
        ))

        # Frustum structural change
        frustum_rule = """
id: frustum-literal
language: rust
rule:
  kind: struct_expression
  pattern: "Frustum { $$$ }"
"""
        transformations.append(self.create_transformation(
            pattern="",
            replacement="",
            description="Frustum struct literal -> tuple wrapping ViewFrustum",
            rule_yaml=frustum_rule,
            callback=lambda vars, file_path, match: (
                full := vars.get("_matched_text", ""),
                re.sub(r"Frustum\s*\{(.*)\}", r"Frustum(ViewFrustum {\1})", full, flags=re.DOTALL)
            )[-1] if "Frustum" in vars.get("_matched_text", "") else vars.get("_matched_text", "")
        ))

        transformations.append(self.create_transformation(
            pattern="ShaderStorageBuffer",
            replacement="ShaderBuffer",
            description="ShaderStorageBuffer renamed to ShaderBuffer"
        ))

        transformations.append(self.create_transformation(
            pattern="GpuShaderStorageBuffer",
            replacement="GpuShaderBuffer",
            description="GpuShaderStorageBuffer renamed to GpuShaderBuffer"
        ))

        # TextFont fields updated
        transformations.append(self.create_transformation(
            pattern="TextFont { $$$ }",
            replacement="",
            description="TextFont fields updated for FontSource and FontSize",
            callback=lambda vars, file_path, match: (
                full := vars.get("_matched_text", ""),
                full := re.sub(r"(font:\s*)(asset_server\.load\([^)]+\)|[^\s,}]+)(,?)", r"\1\2.into()\3", full),
                full := re.sub(r"(font_size:\s*)([\d.]+)(,?)", r"\1FontSize::Px(\2)\3", full),
                full
            )[-1] if "font" in vars.get("_matched_text", "") or "font_size" in vars.get("_matched_text", "") else vars.get("_matched_text", "")
        ))

        transformations.append(self.create_transformation(
            pattern="entities_allocator()",
            replacement="entity_allocator()",
            description="entities_allocator renamed to entity_allocator"
        ))

        transformations.append(self.create_transformation(
            pattern="entities_allocator_mut()",
            replacement="entity_allocator_mut()",
            description="entities_allocator_mut renamed to entity_allocator_mut"
        ))

        # Reflect Reorganization
        reflect_modules = {
            "Struct": "structs", "DynamicStruct": "structs",
            "Tuple": "tuple", "DynamicTuple": "tuple",
            "TupleStruct": "tuple_struct", "DynamicTupleStruct": "tuple_struct",
            "List": "list", "DynamicList": "list",
            "Array": "array", "DynamicArray": "array",
            "Map": "map", "DynamicMap": "map",
            "Set": "set", "DynamicSet": "set",
            "Enum": "enums", "DynamicEnum": "enums"
        }

        # Simple renames for individual imports
        for item, mod in reflect_modules.items():
            transformations.append(self.create_transformation(
                pattern=f"bevy_reflect::{item}",
                replacement=f"bevy_reflect::{mod}::{item}",
                description=f"{item} path change to bevy_reflect::{mod}"
            ))

        # Braced imports callback
        transformations.append(self.create_transformation(
            pattern="use bevy_reflect::{ $$$ITEMS }",
            replacement="",
            description="Streamline braced reflect imports",
            callback=lambda vars, file_path, match: (
                full := vars.get("_matched_text", ""),
                (items_match := re.search(r"\{([^}]+)\}", full)) and (
                    items := [i.strip() for i in items_match.group(1).split(',')],
                    new_imports := {},
                    [new_imports.setdefault(reflect_modules.get(i, "root"), []).append(i) for i in items if i],
                    lines := [],
                    [lines.append(f"use bevy_reflect::{mod}::{{{', '.join(its)}}};") if mod != "root" else lines.append(f"use bevy_reflect::{{{', '.join(its)}}};") for mod, its in new_imports.items()],
                    "\n".join(lines).strip()
                ) or ""
            ) if "bevy_reflect" in vars.get("_matched_text", "") else vars.get("_matched_text", "")
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
