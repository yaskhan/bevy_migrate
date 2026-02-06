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
        # Case 1: App insert
        content = 'app.insert_resource(AmbientLight { color: Color::WHITE });'
        result = self.apply_trans(content)
        self.assertIn('GlobalAmbientLight', result)
        
        # Case 2: Init resource
        content = 'app.init_resource::<AmbientLight>();'
        result = self.apply_trans(content)
        self.assertIn('GlobalAmbientLight', result)

        # Case 3: Commands/World insert
        content = 'commands.insert_resource(AmbientLight::default());'
        result = self.apply_trans(content)
        self.assertIn('GlobalAmbientLight', result)

        # Case 4: Res usage
        content = 'fn system(ambient: Res<AmbientLight>) {}'
        result = self.apply_trans(content)
        self.assertIn('Res<GlobalAmbientLight>', result)

    def test_animation_target(self):
        # Case 1: Standard usage
        content = 'entity.insert(AnimationTarget { id: AnimationTargetId(id), player: player_entity });'
        result = self.apply_trans(content)
        self.assertIn('(AnimationTargetId(id), AnimatedBy(player_entity))', result)
        
        # Case 2: Swapped order
        content = 'entity.insert(AnimationTarget { player: player_entity, id: AnimationTargetId(id) });'
        result = self.apply_trans(content)
        self.assertIn('(AnimationTargetId(id), AnimatedBy(player_entity))', result)
        
        # Case 3: Raw identifier for id (auto-wrap with AnimationTargetId)
        content = 'AnimationTarget { id: my_id, player: my_player }'
        result = self.apply_trans(content)
        self.assertIn('(AnimationTargetId(my_id), AnimatedBy(my_player))', result)

    def test_render_target(self):
        # Case 1: Simple target only
        content = 'Camera { target: RenderTarget::Image(handle.into()), ..default() }'
        result = self.apply_trans(content)
        self.assertEqual(result, 'RenderTarget::Image(handle.into())')
        
        # Case 2: With other fields
        content = 'Camera { hdr: true, target: RenderTarget::Window(WindowRef::Primary), ..default() }'
        result = self.apply_trans(content)
        self.assertIn('(Camera { hdr: true, ..default() }, RenderTarget::Window(WindowRef::Primary))', result)
        
        # Case 3: Inside spawn
        content = 'commands.spawn((Camera3d::default(), Camera { target: RenderTarget::Image(h), ..default() }));'
        result = self.apply_trans(content)
        self.assertIn('(Camera3d::default(), RenderTarget::Image(h))', result)

if __name__ == "__main__":
    unittest.main()
