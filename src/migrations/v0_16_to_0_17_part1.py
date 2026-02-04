"""
Migration from Bevy 0.16 to 0.17 - Part 1
Event/Message Split, Observer API Changes, and Core ECS Updates

This is Part 1 of 3 for the Bevy 0.16 to 0.17 migration.
Run parts in order: Part 1 → Part 2 → Part 3
"""

import logging
import re
from pathlib import Path
from typing import List

from migrations.base_migration import BaseMigration, MigrationResult
from core.ast_processor import ASTTransformation


class Migration_0_16_to_0_17_Part1(BaseMigration):
    """
    Migration Part 1: Event/Message Split & Observer API
    
    Key changes in this part:
    - Event/Message terminology split (buffered events → messages)
    - Observer API changes (Trigger → On, lifecycle events renamed)
    - Core ECS changes (Query, System, Relationships)
    - Handle::Weak → Handle::Uuid
    """
    
    @property
    def from_version(self) -> str:
        return "0.16"
    
    @property
    def to_version(self) -> str:
        return "0.17-part1"
    
    @property
    def description(self) -> str:
        return "Bevy 0.16 → 0.17 Part 1: Event/Message split, Observer API, Core ECS (~50 transformations)"
    
    def get_transformations(self) -> List[ASTTransformation]:
        transformations = []
        
        # ===== EVENT/MESSAGE RENAME (10 transformations) =====
        
        # 1-3. EventWriter/Reader/Events → MessageWriter/Reader/Messages
        transformations.append(self.create_transformation(
            pattern="EventWriter<$T>",
            replacement="MessageWriter<$T>",
            description="EventWriter renamed to MessageWriter for buffered events"
        ))
        
        transformations.append(self.create_transformation(
            pattern="EventReader<$T>",
            replacement="MessageReader<$T>",
            description="EventReader renamed to MessageReader"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Events<$T>",
            replacement="Messages<$T>",
            description="Events renamed to Messages"
        ))
        
        # 4-5. World/Commands send_event → write_message
        transformations.append(self.create_transformation(
            pattern="$WORLD.send_event($EVENT)",
            replacement="$WORLD.write_message($EVENT)",
            description="World::send_event renamed to write_message"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$COMMANDS.send_event($EVENT)",
            replacement="$COMMANDS.write_message($EVENT)",
            description="Commands::send_event renamed to write_message"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$WORLD.send_event_default()",
            replacement="$WORLD.write_message_default()",
            description="send_event_default renamed to write_message_default"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$WORLD.send_event_batch($EVENTS)",
            replacement="$WORLD.write_message_batch($EVENTS)",
            description="send_event_batch renamed to write_message_batch"
        ))
        
        # 6. RemovedComponentEvents → RemovedComponentMessages
        transformations.append(self.create_transformation(
            pattern="RemovedComponentEvents",
            replacement="RemovedComponentMessages",
            description="RemovedComponentEvents renamed to RemovedComponentMessages"
        ))
        
        # 7. RemovedComponents::events → messages
        transformations.append(self.create_transformation(
            pattern="$REMOVED.events()",
            replacement="$REMOVED.messages()",
            description="RemovedComponents::events renamed to messages"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$REMOVED.reader_mut_with_events()",
            replacement="$REMOVED.reader_mut_with_messages()",
            description="reader_mut_with_events renamed to reader_mut_with_messages"
        ))
        
        # ===== OBSERVER API CHANGES (15 transformations) =====
        
        # 11. Trigger<E> → On<E> (parameter type)
        transformations.append(self.create_transformation(
            pattern="trigger: Trigger<$E>",
            replacement="on: On<$E>",
            description="Trigger parameter renamed to On"
        ))
        
        transformations.append(self.create_transformation(
            pattern="trigger: Trigger<$E, $F>",
            replacement="on: On<$E, $F>",
            description="Trigger with filter renamed to On"
        ))
        
        # 12-16. Lifecycle events renamed (OnAdd → Add, etc.)
        transformations.append(self.create_transformation(
            pattern="OnAdd",
            replacement="Add",
            description="OnAdd renamed to Add"
        ))
        
        transformations.append(self.create_transformation(
            pattern="OnInsert",
            replacement="Insert",
            description="OnInsert renamed to Insert"
        ))
        
        transformations.append(self.create_transformation(
            pattern="OnReplace",
            replacement="Replace",
            description="OnReplace renamed to Replace"
        ))
        
        transformations.append(self.create_transformation(
            pattern="OnRemove",
            replacement="Remove",
            description="OnRemove renamed to Remove"
        ))
        
        transformations.append(self.create_transformation(
            pattern="OnDespawn",
            replacement="Despawn",
            description="OnDespawn renamed to Despawn"
        ))
        
        # 17. trigger.target() → event.entity (for EntityEvent)
        transformations.append(self.create_transformation(
            pattern="$TRIGGER.target()",
            replacement="$TRIGGER.entity",
            description="Trigger::target() → event.entity for EntityEvent"
        ))
        
        # 18. trigger.components() → event.trigger().components
        transformations.append(self.create_transformation(
            pattern="$TRIGGER.components()",
            replacement="$TRIGGER.trigger().components",
            description="Access components via trigger() method"
        ))
        
        # 19. world.trigger_targets removed (manual migration needed)
        # This requires manual intervention to add entity field to event
        
        # 20-22. Event derive macros (manual migration - add comments)
        # These require manual changes to derive macros
        
        # 23. Animation events (manual migration)
        
        # 24-25. ObserverState unified (manual migration)
        
        # ===== ECS CORE CHANGES (10 transformations) =====
        
        # 26. Query::get_single deprecated → use single()
        transformations.append(self.create_transformation(
            pattern="$QUERY.get_single()",
            replacement="$QUERY.single()",
            description="Query::get_single deprecated, use single()"
        ))
        
        # 27. iter_entities deprecated
        transformations.append(self.create_transformation(
            pattern="$WORLD.iter_entities()",
            replacement="$WORLD.query::<EntityRef>().iter(&$WORLD)",
            description="iter_entities deprecated, use query::<EntityRef>()"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$WORLD.iter_entities_mut()",
            replacement="$WORLD.query::<EntityMut>().iter(&mut $WORLD)",
            description="iter_entities_mut deprecated, use query::<EntityMut>()"
        ))
        
        # 28. EntityRef now respects default query filters
        # (Manual migration - add Allows<Disabled> if needed)
        
        # 29. Option<Single<D>> behavior change
        # (Manual migration - use Query::single() manually)
        
        # 30. Condition → SystemCondition
        transformations.append(self.create_transformation(
            pattern="use bevy::ecs::schedule::Condition",
            replacement="use bevy::ecs::schedule::SystemCondition",
            description="Condition trait renamed to SystemCondition"
        ))
        
        transformations.append(self.create_transformation(
            pattern=": Condition",
            replacement=": SystemCondition",
            description="Condition trait renamed to SystemCondition"
        ))
        
        # 31. System::run returns Result
        # (Manual migration - add ? or unwrap())
        
        # 32. apply_deferred() → ApplyDeferred
        transformations.append(self.create_transformation(
            pattern="apply_deferred()",
            replacement="ApplyDeferred",
            description="apply_deferred() is now ApplyDeferred type"
        ))
        
        # 33-34. State scoped entities renamed
        transformations.append(self.create_transformation(
            pattern="StateScoped",
            replacement="DespawnOnExit",
            description="StateScoped renamed to DespawnOnExit"
        ))
        
        transformations.append(self.create_transformation(
            pattern="clear_state_scoped_entities",
            replacement="despawn_entities_on_exit_state",
            description="clear_state_scoped_entities renamed"
        ))
        
        transformations.append(self.create_transformation(
            pattern="add_state_scoped_event",
            replacement="add_event",
            description="add_state_scoped_event replaced with add_event + clear_events_on_exit"
        ))
        
        # 35. Internal component (observers/systems hidden)
        # (Manual migration - add Allows<Internal> if needed)
        
        # ===== RELATIONSHIP CHANGES (5 transformations) =====
        
        # 36. world.trigger_targets removed
        # (Manual migration - use world.trigger with EntityEvent)
        
        # 37-40. Relationship API changes
        # (Manual migration - implement set_risky, derive EntityEvent)
        
        # ===== MISC PART 1 (10 transformations) =====
        
        # 41-43. Handle::Weak → Handle::Uuid
        transformations.append(self.create_transformation(
            pattern="weak_handle!($UUID)",
            replacement="uuid_handle!($UUID)",
            description="weak_handle! macro renamed to uuid_handle!"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Handle::Weak",
            replacement="Handle::Uuid",
            description="Handle::Weak renamed to Handle::Uuid"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$HANDLE.clone_weak()",
            replacement="$HANDLE.clone()",
            description="Handle::clone_weak → clone (most cases)"
        ))
        
        # 44-45. SceneSpawner renames
        transformations.append(self.create_transformation(
            pattern="$SPAWNER.despawn($SCENE)",
            replacement="$SPAWNER.despawn_dynamic($SCENE)",
            description="SceneSpawner::despawn → despawn_dynamic"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$SPAWNER.despawn_sync($SCENE)",
            replacement="$SPAWNER.despawn_dynamic_sync($SCENE)",
            description="SceneSpawner::despawn_sync → despawn_dynamic_sync"
        ))
        
        transformations.append(self.create_transformation(
            pattern="$SPAWNER.update_spawned_scenes()",
            replacement="$SPAWNER.update_spawned_dynamic_scenes()",
            description="update_spawned_scenes → update_spawned_dynamic_scenes"
        ))
        
        # 46. Location no longer Component
        transformations.append(self.create_transformation(
            pattern="use bevy_picking::Location",
            replacement="use bevy_picking::PointerLocation",
            description="Location no longer Component, use PointerLocation"
        ))
        
        # 47. scale_value removed
        transformations.append(self.create_transformation(
            pattern="scale_value($FACTOR)",
            replacement="$FACTOR *",
            description="scale_value removed, multiply by scale factor directly"
        ))
        
        # 48-49. Assets::insert/get_or_insert_with returns Result
        # (Manual migration - add ? or unwrap())
        
        # 50. Wayland enabled by default
        # (No code change, just documentation)
        
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
            self.logger.info("BEVY 0.16 → 0.17 MIGRATION - PART 1 OF 3")
            self.logger.info("=" * 60)
            self.logger.info("This part covers:")
            self.logger.info("  - Event/Message terminology split")
            self.logger.info("  - Observer API changes (Trigger → On)")
            self.logger.info("  - Core ECS updates")
            self.logger.info("  - Handle::Weak → Handle::Uuid")
            self.logger.info("=" * 60)
            
            rust_files = self.file_manager.find_rust_files()
            
            # Check for Event/Message patterns
            event_files = self.find_files_with_pattern("EventWriter")
            if event_files:
                self.logger.info(f"Found {len(event_files)} files using EventWriter (will rename to MessageWriter)")
            
            # Check for Observer patterns
            observer_files = self.find_files_with_pattern("Trigger<")
            if observer_files:
                self.logger.info(f"Found {len(observer_files)} files using Trigger (will rename to On)")
            
            # Check for lifecycle events
            lifecycle_files = self.find_files_with_pattern("OnAdd")
            if lifecycle_files:
                self.logger.info(f"Found {len(lifecycle_files)} files using OnAdd/OnInsert/etc (will rename)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        try:
            self.logger.info("=" * 60)
            self.logger.info("Part 1 migration complete!")
            self.logger.info("=" * 60)
            self.logger.info("IMPORTANT: This is Part 1 of 3")
            self.logger.info("Next steps:")
            self.logger.info("1. Review Event/Message renames")
            self.logger.info("2. Update observer signatures (Trigger → On)")
            self.logger.info("3. Fix entity event derives (#[derive(EntityEvent)])")
            self.logger.info("4. Run Part 2: bevy_render reorganization")
            self.logger.info("=" * 60)
            self.logger.info("Manual migration required for:")
            self.logger.info("  - Entity events: add 'entity: Entity' field")
            self.logger.info("  - world.trigger_targets → world.trigger")
            self.logger.info("  - #[derive(Event)] → #[derive(EntityEvent)] for entity events")
            self.logger.info("  - System::run now returns Result (add ? or unwrap)")
            self.logger.info("  - Assets::insert/get_or_insert_with returns Result")
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
                
                if re.search(r'bevy\s*=\s*["\']0\.16', content):
                    self.logger.info("Confirmed Bevy 0.16 dependency")
                elif re.search(r'bevy\s*=.*version\s*=\s*["\']0\.16', content):
                    self.logger.info("Confirmed Bevy 0.16 dependency")
                else:
                    self.logger.warning("Could not confirm Bevy 0.16 dependency")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}", exc_info=True)
            return False
