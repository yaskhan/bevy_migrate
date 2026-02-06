import sys
from pathlib import Path
import unittest
import tempfile
import shutil

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from bevymigrate.migrations.v0_16_to_0_17_part1 import Migration_0_16_to_0_17_Part1
from bevymigrate.migrations.v0_16_to_0_17_part2 import Migration_0_16_to_0_17_Part2
from bevymigrate.migrations.v0_16_to_0_17_part3 import Migration_0_16_to_0_17_Part3
from bevymigrate.core.ast_processor import ASTProcessor
from bevymigrate.core.file_manager import FileManager


class TestBevy016To017Part1Complex(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        project_path = Path(self.test_dir)
        self.processor = ASTProcessor(project_path=project_path)
        self.file_manager = FileManager(project_path=project_path)
        self.migration = Migration_0_16_to_0_17_Part1(
            project_path=project_path,
            file_manager=self.file_manager
        )
        self.transformations = self.migration.get_transformations()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def apply_trans(self, content):
        file_path = Path(self.test_dir) / "test.rs"
        file_path.write_text(content)

        results = self.processor.apply_transformations([file_path], self.transformations)
        if results and results[0].success:
            if results[0].applied_transformations:
                print(f"Applied: {results[0].applied_transformations}")
            else:
                print("No transformations applied")
            return results[0].transformed_content

        if results and not results[0].success:
            print(f"Error: {results[0].error_message}")

        return file_path.read_text()

    def test_event_writer_to_message_writer(self):
        content = 'fn system(mut writer: EventWriter<MyEvent>) {}'
        result = self.apply_trans(content)
        self.assertIn('MessageWriter<MyEvent>', result)

    def test_event_reader_to_message_reader(self):
        content = 'fn system(reader: EventReader<MyEvent>) {}'
        result = self.apply_trans(content)
        self.assertIn('MessageReader<MyEvent>', result)

    def test_events_to_messages(self):
        content = 'fn system(events: Events<MyEvent>) {}'
        result = self.apply_trans(content)
        self.assertIn('Messages<MyEvent>', result)

    def test_world_send_event_to_write_message(self):
        content = 'world.send_event(MyEvent);'
        result = self.apply_trans(content)
        self.assertIn('world.write_message(MyEvent)', result)

    def test_commands_send_event_to_write_message(self):
        content = 'commands.send_event(MyEvent);'
        result = self.apply_trans(content)
        self.assertIn('commands.write_message(MyEvent)', result)

    def test_trigger_to_on_simple(self):
        content = 'fn observer(trigger: Trigger<Add, Player>) {}'
        result = self.apply_trans(content)
        # The callback should convert this to On<Add, Player>
        self.assertIn('on: On<Add, Player>', result)

    def test_trigger_to_on_with_filter(self):
        content = 'fn observer(trigger: Trigger<Add, Player, With<Health>>) {}'
        result = self.apply_trans(content)
        # The callback should convert this to On<Add, Player, With<Health>>
        self.assertIn('on: On<Add, Player, With<Health>>', result)

    def test_trigger_target_to_entity(self):
        content = 'fn observer(trigger: On<Add, Player>) { let entity = trigger.target(); }'
        result = self.apply_trans(content)
        # The callback should convert trigger.target() to trigger.entity
        self.assertIn('.entity', result)

    def test_weak_handle_to_uuid_handle(self):
        content = 'const IMG: Handle<Image> = weak_handle!("b20988e9-b1b9-4176-b5f3-a6fa73aa617f");'
        result = self.apply_trans(content)
        self.assertIn('uuid_handle!', result)


class TestBevy016To017Part2Complex(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        project_path = Path(self.test_dir)
        self.processor = ASTProcessor(project_path=project_path)
        self.file_manager = FileManager(project_path=project_path)
        self.migration = Migration_0_16_to_0_17_Part2(
            project_path=project_path,
            file_manager=self.file_manager
        )
        self.transformations = self.migration.get_transformations()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def apply_trans(self, content):
        file_path = Path(self.test_dir) / "test.rs"
        file_path.write_text(content)

        results = self.processor.apply_transformations([file_path], self.transformations)
        if results and results[0].success:
            if results[0].applied_transformations:
                print(f"Applied: {results[0].applied_transformations}")
            else:
                print("No transformations applied")
            return results[0].transformed_content

        if results and not results[0].success:
            print(f"Error: {results[0].error_message}")

        return file_path.read_text()

    def test_import_reorganization_camera(self):
        content = 'use bevy::render::camera::Camera;'
        result = self.apply_trans(content)
        self.assertIn('use bevy::camera::Camera', result)

    def test_import_reorganization_shader(self):
        content = 'use bevy::render::render_resource::Shader;'
        result = self.apply_trans(content)
        self.assertIn('use bevy::shader::Shader', result)

    def test_import_reorganization_light(self):
        content = 'use bevy::pbr::PointLight;'
        result = self.apply_trans(content)
        self.assertIn('use bevy::light::PointLight', result)

    def test_system_set_rename(self):
        content = 'use bevy::ecs::schedule::AccessibilitySystem;'
        result = self.apply_trans(content)
        self.assertIn('AccessibilitySystems', result)

    def test_pointer_pressed_to_press(self):
        content = 'Pointer<Pressed>'
        result = self.apply_trans(content)
        self.assertIn('Pointer<Press>', result)

    def test_pointer_released_to_release(self):
        content = 'Pointer<Released>'
        result = self.apply_trans(content)
        self.assertIn('Pointer<Release>', result)

    def test_computed_node_target_to_computed_ui_target_camera(self):
        content = 'ComputedNodeTarget'
        result = self.apply_trans(content)
        self.assertIn('ComputedUiTargetCamera', result)


class TestBevy016To017Part3Complex(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        project_path = Path(self.test_dir)
        self.processor = ASTProcessor(project_path=project_path)
        self.file_manager = FileManager(project_path=project_path)
        self.migration = Migration_0_16_to_0_17_Part3(
            project_path=project_path,
            file_manager=self.file_manager
        )
        self.transformations = self.migration.get_transformations()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def apply_trans(self, content):
        file_path = Path(self.test_dir) / "test.rs"
        file_path.write_text(content)

        results = self.processor.apply_transformations([file_path], self.transformations)
        if results and results[0].success:
            if results[0].applied_transformations:
                print(f"Applied: {results[0].applied_transformations}")
            else:
                print("No transformations applied")
            return results[0].transformed_content

        if results and not results[0].success:
            print(f"Error: {results[0].error_message}")

        return file_path.read_text()

    def test_entity_from_raw_to_from_raw_u32(self):
        content = 'let entity = Entity::from_raw(1);'
        result = self.apply_trans(content)
        self.assertIn('Entity::from_raw_u32(1).unwrap()', result)

    def test_timer_paused_to_is_paused(self):
        content = 'if timer.paused() {}'
        result = self.apply_trans(content)
        self.assertIn('timer.is_paused()', result)

    def test_timer_finished_to_is_finished(self):
        content = 'if timer.finished() {}'
        result = self.apply_trans(content)
        self.assertIn('timer.is_finished()', result)

    def test_volume_add_to_increase_by_percentage(self):
        content = 'let new_volume = volume + 0.1;'
        result = self.apply_trans(content)
        # With the callback, this should be transformed to use increase_by_percentage
        self.assertIn('increase_by_percentage', result)

    def test_volume_sub_to_decrease_by_percentage(self):
        content = 'let new_volume = volume - 0.1;'
        result = self.apply_trans(content)
        # With the callback, this should be transformed to use decrease_by_percentage
        self.assertIn('decrease_by_percentage', result)

    def test_face_normal_to_triangle_normal(self):
        content = 'face_normal(a, b, c)'
        result = self.apply_trans(content)
        self.assertIn('triangle_normal(a, b, c)', result)

    def test_face_area_normal_to_triangle_area_normal(self):
        content = 'face_area_normal(a, b, c)'
        result = self.apply_trans(content)
        self.assertIn('triangle_area_normal(a, b, c)', result)

    def test_entry_enum_rename(self):
        content = 'Entry::'
        result = self.apply_trans(content)
        self.assertIn('ComponentEntry::', result)

    def test_compute_matrix_to_to_matrix(self):
        content = 'transform.compute_matrix()'
        result = self.apply_trans(content)
        self.assertIn('transform.to_matrix()', result)


if __name__ == "__main__":
    unittest.main()