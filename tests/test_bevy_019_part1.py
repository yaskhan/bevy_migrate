import sys
from pathlib import Path
import unittest
import tempfile
import shutil

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from bevymigrate.migrations.v0_18_to_0_19_part1 import Migration_0_18_to_0_19_Part1
from bevymigrate.core.ast_processor import ASTProcessor
from bevymigrate.core.file_manager import FileManager

class TestBevy019Part1ComplexLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        project_path = Path(self.test_dir)
        self.processor = ASTProcessor(project_path=project_path)
        self.file_manager = FileManager(project_path=project_path)
        self.migration = Migration_0_18_to_0_19_Part1(
            project_path=project_path,
            file_manager=self.file_manager
        )
        self.transformations = self.migration.get_transformations()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def apply_trans(self, content):
        file_path = Path(self.test_dir) / "test.rs"
        file_path.write_text(content)
        
        # print(f"DEBUG: Processing transformations for: {content}")
        results = self.processor.apply_transformations([file_path], self.transformations)
        if results:
            # print(f"DEBUG: Result success: {results[0].success}")
            if results[0].success:
                if results[0].applied_transformations:
                    print(f"Applied: {results[0].applied_transformations}")
                else:
                    print(f"No transformations applied to: {content}")
                return results[0].transformed_content
            else:
                print(f"Error processing {content}: {results[0].error_message}")
        else:
            print(f"No results returned for: {content}")
        
        return content

    def test_text_font(self):
        content = 'fn setup() { let font = TextFont { font: asset_server.load("font.ttf"), font_size: 35.0, ..default() }; }'
        result = self.apply_trans(content)
        self.assertIn('font: asset_server.load("font.ttf").into()', result)
        self.assertIn('font_size: FontSize::Px(35.0)', result)

    def test_frustum(self):
        content = 'fn main() { let f = Frustum { half_spaces: [HalfSpace::default(); 6] }; }'
        result = self.apply_trans(content)
        self.assertIn('Frustum(ViewFrustum { half_spaces: [HalfSpace::default(); 6] })', result)

    def test_entity_event(self):
        # Case 1: Simple struct
        content = '#[derive(Event)]\nstruct MyEvent;'
        result = self.apply_trans(content)
        self.assertIn('#[derive(EntityEvent)]', result)
        self.assertIn('struct MyEvent { entity: Entity }', result)

        # Case 2: Struct with fields
        content = '#[derive(Event)]\nstruct MyEvent {\n    value: f32\n}'
        result = self.apply_trans(content)
        self.assertIn('#[derive(EntityEvent)]', result)
        self.assertIn('entity: Entity,', result)
        self.assertIn('value: f32', result)

    def test_reflect_reorg(self):
        content = 'use bevy_reflect::Struct;'
        result = self.apply_trans(content)
        self.assertEqual(result, 'use bevy_reflect::structs::Struct;')

        content = 'use bevy_reflect::{Struct, DynamicStruct};'
        result = self.apply_trans(content)
        self.assertIn('use bevy_reflect::structs::{Struct, DynamicStruct}', result)

    def test_message_renames(self):
        content = 'fn sys(writer: EventWriter<MyEvent>) {}'
        result = self.apply_trans(content)
        self.assertIn('MessageWriter<MyEvent>', result)

if __name__ == "__main__":
    unittest.main()
