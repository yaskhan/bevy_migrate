import sys
from pathlib import Path
import unittest
import tempfile
import shutil

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from bevymigrate.migrations.v0_17_to_0_18 import Migration_0_17_to_0_18
from bevymigrate.core.ast_processor import ASTProcessor
from bevymigrate.core.file_manager import FileManager

class TestBevy018ComplexLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        project_path = Path(self.test_dir)
        self.processor = ASTProcessor(project_path=project_path)
        self.file_manager = FileManager(project_path=project_path)
        self.migration = Migration_0_17_to_0_18(
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

    def test_gltf_plugin(self):
        content = 'GltfPlugin { use_model_forward_direction: true, ..default() }'
        result = self.apply_trans(content)
        self.assertIn('rotate_scene_entity: true', result)
        self.assertNotIn('Some(', result)

    def test_gltf_loader_settings(self):
        content = 'GltfLoaderSettings { use_model_forward_direction: false, ..default() }'
        result = self.apply_trans(content)
        self.assertIn('rotate_scene_entity: false', result)
        self.assertIn('Some(', result)

    def test_border_rect(self):
        content = 'BorderRect { left: 1.0, right: 2.0, top: 3.0, bottom: 4.0 }'
        expected = 'BorderRect { min_inset: Vec2::new(1.0, 3.0), max_inset: Vec2::new(2.0, 4.0) }'
        result = self.apply_trans(content)
        self.assertIn('min_inset: Vec2::new(1.0, 3.0)', result)
        self.assertIn('max_inset: Vec2::new(2.0, 4.0)', result)

    def test_asset_processor(self):
        content = 'let p = AssetProcessor::new(s);'
        result = self.apply_trans(content)
        self.assertIn('let (p, _sources) = AssetProcessor::new(s, false)', result)

    def test_ambient_light(self):
        content = 'app.insert_resource(AmbientLight { color: Color::WHITE });'
        result = self.apply_trans(content)
        self.assertIn('GlobalAmbientLight', result)
        self.assertNotIn('app.insert_resource(AmbientLight {', result)

if __name__ == "__main__":
    unittest.main()
