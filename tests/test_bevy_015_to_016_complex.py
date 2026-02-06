import sys
from pathlib import Path
import unittest
import tempfile
import shutil

sys.path.append(str(Path(__file__).parent.parent / "src"))

from migrations.v0_15_to_0_16 import Migration_0_15_to_0_16
from core.ast_processor import ASTProcessor
from core.file_manager import FileManager


class TestBevy015To016ComplexLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        project_path = Path(self.test_dir)
        self.processor = ASTProcessor(project_path=project_path)
        self.file_manager = FileManager(project_path=project_path)
        self.migration = Migration_0_15_to_0_16(
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

    def test_ease_function_steps_jump_at(self):
        content = 'let ease = EaseFunction::Steps(10);'
        result = self.apply_trans(content)
        self.assertIn('EaseFunction::Steps(10, JumpAt::default())', result)

    def test_audio_sink_param_mut(self):
        content = 'fn increase_volume(sink: Single<&AudioSink>) {}'
        result = self.apply_trans(content)
        self.assertIn('mut sink: Single<&mut AudioSink>', result)

    def test_set_parent_to_child_of(self):
        content = 'commands.spawn_empty().set_parent(parent);'
        result = self.apply_trans(content)
        self.assertIn('commands.spawn_empty().insert(ChildOf(parent))', result)

    def test_required_component_function(self):
        content = '#[require(A(returns_a))]\nstruct Foo;'
        result = self.apply_trans(content)
        self.assertIn('#[require(A = returns_a())]', result)

    def test_required_component_inline_closure(self):
        content = '#[require(A(|| A(10)))]\nstruct Foo;'
        result = self.apply_trans(content)
        self.assertIn('#[require(A(10))]', result)


if __name__ == "__main__":
    unittest.main()
