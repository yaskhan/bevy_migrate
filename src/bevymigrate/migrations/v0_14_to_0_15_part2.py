"""
Migration from Bevy 0.14 to 0.15 - Part 2: Required Components
Handles bundle to required component migrations
Part 1 handles core API changes
"""

import logging
import re
from pathlib import Path
from typing import List

from bevymigrate.migrations.base_migration import BaseMigration, MigrationResult
from bevymigrate.core.ast_processor import ASTTransformation


class Migration_0_14_to_0_15_Part2(BaseMigration):
    """
    Migration class for upgrading Bevy projects from version 0.14 to 0.15 (Part 2)
    
    This is Part 2 of a two-part migration focusing on required components.
    Part 1 handles core API changes.
    
    Key changes in Part 2:
    - All bundles replaced with required components
    - Camera bundles → Camera components
    - Mesh/Material bundles → Mesh/Material components
    - Light bundles → Light components
    - Scene bundles → SceneRoot components
    - Sprite bundles → Sprite components
    - Text bundles → Text components with hierarchy
    - Transform/Visibility bundles → individual components
    """
    
    @property
    def from_version(self) -> str:
        """Source Bevy version for this migration"""
        return "0.15-part1"
    
    @property
    def to_version(self) -> str:
        """Target Bevy version for this migration"""
        return "0.15"
    
    @property
    def description(self) -> str:
        """Human-readable description of this migration"""
        return "Migrate Bevy project from version 0.14 to 0.15 (Part 2: Required Components)"
    
    def get_transformations(self) -> List[ASTTransformation]:
        """
        Get the list of AST transformations for Part 2
        
        Returns:
            List of ASTTransformation objects
        """
        transformations = []
        
        # ===== AUDIO BUNDLES =====
        
        # 1. AudioSourceBundle to AudioPlayer
        transformations.append(self.create_transformation(
            pattern="AudioSourceBundle { source: $SOURCE, $REST }",
            replacement="AudioPlayer($SOURCE)",
            description="Replace AudioSourceBundle with AudioPlayer component"
        ))
        
        # ===== CAMERA BUNDLES =====
        
        # 2. Camera2dBundle to Camera2d
        transformations.append(self.create_transformation(
            pattern="Camera2dBundle { $FIELDS }",
            replacement="Camera2d",
            description="Replace Camera2dBundle with Camera2d component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Camera2dBundle::default()",
            replacement="Camera2d",
            description="Replace Camera2dBundle::default() with Camera2d"
        ))
        
        # 3. Camera3dBundle to Camera3d
        transformations.append(self.create_transformation(
            pattern="Camera3dBundle { $FIELDS }",
            replacement="Camera3d",
            description="Replace Camera3dBundle with Camera3d component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="Camera3dBundle::default()",
            replacement="Camera3d",
            description="Replace Camera3dBundle::default() with Camera3d"
        ))
        
        # ===== FOG BUNDLES =====
        
        # 4. FogVolumeBundle to Visibility
        transformations.append(self.create_transformation(
            pattern="FogVolumeBundle { $FIELDS }",
            replacement="Visibility::default()",
            description="Replace FogVolumeBundle with Visibility component"
        ))
        
        # ===== LIGHT BUNDLES =====
        
        # 5. PointLightBundle to PointLight
        transformations.append(self.create_transformation(
            pattern="PointLightBundle { point_light: $LIGHT, transform: $TRANSFORM, $REST }",
            replacement="($LIGHT, $TRANSFORM)",
            description="Replace PointLightBundle with PointLight + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="PointLightBundle { point_light: $LIGHT, $REST }",
            replacement="$LIGHT",
            description="Replace PointLightBundle with PointLight component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="PointLightBundle::default()",
            replacement="PointLight::default()",
            description="Replace PointLightBundle::default() with PointLight::default()"
        ))
        
        # 6. SpotLightBundle to SpotLight
        transformations.append(self.create_transformation(
            pattern="SpotLightBundle { spot_light: $LIGHT, transform: $TRANSFORM, $REST }",
            replacement="($LIGHT, $TRANSFORM)",
            description="Replace SpotLightBundle with SpotLight + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpotLightBundle { spot_light: $LIGHT, $REST }",
            replacement="$LIGHT",
            description="Replace SpotLightBundle with SpotLight component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpotLightBundle::default()",
            replacement="SpotLight::default()",
            description="Replace SpotLightBundle::default() with SpotLight::default()"
        ))
        
        # 7. DirectionalLightBundle to DirectionalLight
        transformations.append(self.create_transformation(
            pattern="DirectionalLightBundle { directional_light: $LIGHT, transform: $TRANSFORM, $REST }",
            replacement="($LIGHT, $TRANSFORM)",
            description="Replace DirectionalLightBundle with DirectionalLight + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DirectionalLightBundle { directional_light: $LIGHT, $REST }",
            replacement="$LIGHT",
            description="Replace DirectionalLightBundle with DirectionalLight component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DirectionalLightBundle::default()",
            replacement="DirectionalLight::default()",
            description="Replace DirectionalLightBundle::default() with DirectionalLight::default()"
        ))
        
        # ===== MESH & MATERIAL BUNDLES =====
        
        # 8. MaterialMesh2dBundle to (Mesh2d, MeshMaterial2d)
        transformations.append(self.create_transformation(
            pattern="MaterialMesh2dBundle { mesh: $MESH, material: $MAT, transform: $TRANSFORM, $REST }",
            replacement="(Mesh2d($MESH), MeshMaterial2d($MAT), $TRANSFORM)",
            description="Replace MaterialMesh2dBundle with Mesh2d + MeshMaterial2d + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="MaterialMesh2dBundle { mesh: $MESH, material: $MAT, $REST }",
            replacement="(Mesh2d($MESH), MeshMaterial2d($MAT))",
            description="Replace MaterialMesh2dBundle with Mesh2d + MeshMaterial2d"
        ))
        
        # 9. MaterialMeshBundle to (Mesh3d, MeshMaterial3d)
        transformations.append(self.create_transformation(
            pattern="MaterialMeshBundle { mesh: $MESH, material: $MAT, transform: $TRANSFORM, $REST }",
            replacement="(Mesh3d($MESH), MeshMaterial3d($MAT), $TRANSFORM)",
            description="Replace MaterialMeshBundle with Mesh3d + MeshMaterial3d + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="MaterialMeshBundle { mesh: $MESH, material: $MAT, $REST }",
            replacement="(Mesh3d($MESH), MeshMaterial3d($MAT))",
            description="Replace MaterialMeshBundle with Mesh3d + MeshMaterial3d"
        ))
        
        # 10. PbrBundle to (Mesh3d, MeshMaterial3d)
        transformations.append(self.create_transformation(
            pattern="PbrBundle { mesh: $MESH, material: $MAT, transform: $TRANSFORM, $REST }",
            replacement="(Mesh3d($MESH), MeshMaterial3d($MAT), $TRANSFORM)",
            description="Replace PbrBundle with Mesh3d + MeshMaterial3d + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="PbrBundle { mesh: $MESH, material: $MAT, $REST }",
            replacement="(Mesh3d($MESH), MeshMaterial3d($MAT))",
            description="Replace PbrBundle with Mesh3d + MeshMaterial3d"
        ))
        
        # ===== POST-PROCESSING BUNDLES =====
        
        # 11. MotionBlurBundle to MotionBlur
        transformations.append(self.create_transformation(
            pattern="MotionBlurBundle { $FIELDS }",
            replacement="MotionBlur::default()",
            description="Replace MotionBlurBundle with MotionBlur component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="MotionBlurBundle::default()",
            replacement="MotionBlur::default()",
            description="Replace MotionBlurBundle::default() with MotionBlur::default()"
        ))
        
        # 12. TemporalAntiAliasBundle to TemporalAntiAliasing
        transformations.append(self.create_transformation(
            pattern="TemporalAntiAliasBundle { $FIELDS }",
            replacement="TemporalAntiAliasing::default()",
            description="Replace TemporalAntiAliasBundle with TemporalAntiAliasing component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="TemporalAntiAliasBundle::default()",
            replacement="TemporalAntiAliasing::default()",
            description="Replace TemporalAntiAliasBundle::default() with TemporalAntiAliasing::default()"
        ))
        
        # 13. ScreenSpaceAmbientOcclusionBundle to ScreenSpaceAmbientOcclusion
        transformations.append(self.create_transformation(
            pattern="ScreenSpaceAmbientOcclusionBundle { $FIELDS }",
            replacement="ScreenSpaceAmbientOcclusion::default()",
            description="Replace ScreenSpaceAmbientOcclusionBundle with ScreenSpaceAmbientOcclusion"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ScreenSpaceAmbientOcclusionBundle::default()",
            replacement="ScreenSpaceAmbientOcclusion::default()",
            description="Replace ScreenSpaceAmbientOcclusionBundle::default()"
        ))
        
        # 14. ScreenSpaceReflectionsBundle to ScreenSpaceReflections
        transformations.append(self.create_transformation(
            pattern="ScreenSpaceReflectionsBundle { $FIELDS }",
            replacement="ScreenSpaceReflections::default()",
            description="Replace ScreenSpaceReflectionsBundle with ScreenSpaceReflections"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ScreenSpaceReflectionsBundle::default()",
            replacement="ScreenSpaceReflections::default()",
            description="Replace ScreenSpaceReflectionsBundle::default()"
        ))
        
        # ===== PROBE BUNDLES =====
        
        # 15. ReflectionProbeBundle to (LightProbe, EnvironmentMapLight)
        transformations.append(self.create_transformation(
            pattern="ReflectionProbeBundle { $FIELDS }",
            replacement="(LightProbe, EnvironmentMapLight::default())",
            description="Replace ReflectionProbeBundle with LightProbe + EnvironmentMapLight"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ReflectionProbeBundle::default()",
            replacement="(LightProbe, EnvironmentMapLight::default())",
            description="Replace ReflectionProbeBundle::default()"
        ))
        
        # ===== SCENE BUNDLES =====
        
        # 16. SceneBundle to SceneRoot
        transformations.append(self.create_transformation(
            pattern="SceneBundle { scene: $SCENE, transform: $TRANSFORM, $REST }",
            replacement="(SceneRoot($SCENE), $TRANSFORM)",
            description="Replace SceneBundle with SceneRoot + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SceneBundle { scene: $SCENE, $REST }",
            replacement="SceneRoot($SCENE)",
            description="Replace SceneBundle with SceneRoot component"
        ))
        
        # 17. DynamicSceneBundle to DynamicSceneRoot
        transformations.append(self.create_transformation(
            pattern="DynamicSceneBundle { scene: $SCENE, transform: $TRANSFORM, $REST }",
            replacement="(DynamicSceneRoot($SCENE), $TRANSFORM)",
            description="Replace DynamicSceneBundle with DynamicSceneRoot + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="DynamicSceneBundle { scene: $SCENE, $REST }",
            replacement="DynamicSceneRoot($SCENE)",
            description="Replace DynamicSceneBundle with DynamicSceneRoot component"
        ))
        
        # ===== SPRITE BUNDLES =====
        
        # 18. SpriteBundle to Sprite
        transformations.append(self.create_transformation(
            pattern="SpriteBundle { texture: $TEXTURE, transform: $TRANSFORM, $REST }",
            replacement="(Sprite::from_image($TEXTURE), $TRANSFORM)",
            description="Replace SpriteBundle with Sprite::from_image + Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpriteBundle { texture: $TEXTURE, $REST }",
            replacement="Sprite::from_image($TEXTURE)",
            description="Replace SpriteBundle with Sprite::from_image"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpriteBundle { sprite: $SPRITE, texture: $TEXTURE, $REST }",
            replacement="Sprite::from_image($TEXTURE)",
            description="Replace SpriteBundle with Sprite (sprite field deprecated)"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpriteBundle::default()",
            replacement="Sprite::default()",
            description="Replace SpriteBundle::default() with Sprite::default()"
        ))
        
        # ===== TRANSFORM & VISIBILITY BUNDLES =====
        
        # 19. SpatialBundle to (Transform, Visibility)
        transformations.append(self.create_transformation(
            pattern="SpatialBundle { transform: $TRANSFORM, visibility: $VIS, $REST }",
            replacement="($TRANSFORM, $VIS)",
            description="Replace SpatialBundle with Transform + Visibility"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpatialBundle { transform: $TRANSFORM, $REST }",
            replacement="$TRANSFORM",
            description="Replace SpatialBundle with Transform"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpatialBundle { visibility: $VIS, $REST }",
            replacement="$VIS",
            description="Replace SpatialBundle with Visibility"
        ))
        
        transformations.append(self.create_transformation(
            pattern="SpatialBundle::default()",
            replacement="(Transform::default(), Visibility::default())",
            description="Replace SpatialBundle::default() with Transform + Visibility"
        ))
        
        # 20. VisibilityBundle to Visibility
        transformations.append(self.create_transformation(
            pattern="VisibilityBundle { $FIELDS }",
            replacement="Visibility::default()",
            description="Replace VisibilityBundle with Visibility component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="VisibilityBundle::default()",
            replacement="Visibility::default()",
            description="Replace VisibilityBundle::default() with Visibility::default()"
        ))
        
        # 21. TransformBundle to Transform
        transformations.append(self.create_transformation(
            pattern="TransformBundle { local: $TRANSFORM, $REST }",
            replacement="$TRANSFORM",
            description="Replace TransformBundle with Transform component"
        ))
        
        transformations.append(self.create_transformation(
            pattern="TransformBundle::default()",
            replacement="Transform::default()",
            description="Replace TransformBundle::default() with Transform::default()"
        ))
        
        # ===== UI BUNDLES =====
        
        # 22. NodeBundle to Node
        transformations.append(self.create_transformation(
            pattern="NodeBundle { style: $STYLE, $REST }",
            replacement="$STYLE",
            description="Replace NodeBundle with Node (style is now Node)"
        ))
        
        transformations.append(self.create_transformation(
            pattern="NodeBundle::default()",
            replacement="Node::default()",
            description="Replace NodeBundle::default() with Node::default()"
        ))
        
        # 23. ButtonBundle to Button
        transformations.append(self.create_transformation(
            pattern="ButtonBundle { style: $STYLE, $REST }",
            replacement="(Button, $STYLE)",
            description="Replace ButtonBundle with Button + Node"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ButtonBundle::default()",
            replacement="Button",
            description="Replace ButtonBundle::default() with Button"
        ))
        
        # 24. ImageBundle to ImageNode
        transformations.append(self.create_transformation(
            pattern="ImageBundle { image: $IMAGE, style: $STYLE, $REST }",
            replacement="(ImageNode::new($IMAGE), $STYLE)",
            description="Replace ImageBundle with ImageNode + Node"
        ))
        
        transformations.append(self.create_transformation(
            pattern="ImageBundle { image: $IMAGE, $REST }",
            replacement="ImageNode::new($IMAGE)",
            description="Replace ImageBundle with ImageNode"
        ))
        
        # ===== MESHLET BUNDLES =====
        
        # 25. MaterialMeshletMeshBundle to (MeshletMesh3d, MeshMaterial3d)
        transformations.append(self.create_transformation(
            pattern="MaterialMeshletMeshBundle { meshlet_mesh: $MESH, material: $MAT, $REST }",
            replacement="(MeshletMesh3d($MESH), MeshMaterial3d($MAT))",
            description="Replace MaterialMeshletMeshBundle with MeshletMesh3d + MeshMaterial3d"
        ))
        
        # Handle standalone Handle<MeshletMesh> component
        transformations.append(self.create_transformation(
            pattern="Handle<MeshletMesh>",
            replacement="MeshletMesh3d",
            description="Replace Handle<MeshletMesh> component with MeshletMesh3d"
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
            self.logger.info("Executing pre-migration steps for 0.14 -> 0.15 Part 2")
            
            # Check that Part 1 was run
            self.logger.warning("=" * 60)
            self.logger.warning("IMPORTANT: Ensure Part 1 migration was completed first!")
            self.logger.warning("Part 2 requires Part 1 API changes to be applied.")
            self.logger.warning("=" * 60)
            
            rust_files = self.file_manager.find_rust_files()
            
            # Count bundle usages
            bundle_patterns = [
                "Camera2dBundle", "Camera3dBundle",
                "MaterialMesh2dBundle", "MaterialMeshBundle", "PbrBundle",
                "SpriteBundle", "NodeBundle", "ButtonBundle",
                "PointLightBundle", "SpotLightBundle", "DirectionalLightBundle",
                "SpatialBundle", "VisibilityBundle", "TransformBundle",
                "SceneBundle", "DynamicSceneBundle",
            ]
            
            total_bundles = 0
            for pattern in bundle_patterns:
                files = self.find_files_with_pattern(pattern)
                if files:
                    count = len(files)
                    total_bundles += count
                    self.logger.info(f"Found {count} files using {pattern}")
            
            if total_bundles > 0:
                self.logger.info(f"Total: {total_bundles} bundle usages to migrate")
            else:
                self.logger.warning("No bundles found - Part 1 may have already migrated them?")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Pre-migration steps failed: {e}", exc_info=True)
            return False
    
    def post_migration_steps(self, result: MigrationResult) -> bool:
        """Execute steps after applying transformations"""
        try:
            self.logger.info("Executing post-migration steps for 0.14 -> 0.15 Part 2")
            
            # Update Cargo.toml to Bevy 0.15
            if not self._update_cargo_toml():
                self.logger.warning("Failed to update Cargo.toml automatically")
            
            # Check for manual migration patterns
            self._check_for_manual_migration_needed()
            
            self.logger.info("=" * 60)
            self.logger.info("Migration to Bevy 0.15 complete!")
            self.logger.info("Next steps:")
            self.logger.info("1. Review the changes, especially text hierarchy changes")
            self.logger.info("2. Run 'cargo check' to verify compilation")
            self.logger.info("3. Update any custom code that uses removed APIs")
            self.logger.info("4. Test your application thoroughly")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Post-migration steps failed: {e}", exc_info=True)
            return False
    
    def _update_cargo_toml(self) -> bool:
        """Update Cargo.toml to use Bevy 0.15"""
        try:
            cargo_toml_path = self.project_path / "Cargo.toml"
            if not cargo_toml_path.exists():
                self.logger.warning("Cargo.toml not found")
                return False
            
            content = cargo_toml_path.read_text(encoding='utf-8')
            original_content = content
            
            # Update bevy version
            content = re.sub(
                r'(bevy\s*=\s*["\'])0\.14(["\'])',
                r'\g<1>0.15\g<2>',
                content
            )
            content = re.sub(
                r'(bevy\s*=\s*\{[^}]*version\s*=\s*["\'])0\.14(["\'])',
                r'\g<1>0.15\g<2>',
                content
            )
            
            if content != original_content:
                cargo_toml_path.write_text(content, encoding='utf-8')
                self.logger.info("Updated Cargo.toml to Bevy 0.15")
                return True
            else:
                self.logger.warning("No Bevy version found in Cargo.toml to update")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update Cargo.toml: {e}", exc_info=True)
            return False
    
    def _check_for_manual_migration_needed(self) -> None:
        """Check for patterns that might need manual migration"""
        try:
            manual_patterns = [
                ("TextBundle", "Text now uses hierarchy - text sections are child entities with TextSpan"),
                ("Text2dBundle", "Text2d now uses hierarchy - text sections are child entities with TextSpan"),
                ("text.sections[", "Text sections are now child entities - use TextUiWriter/Text2dWriter"),
                ("Handle<Image>", "Handle<Image> no longer a component - use Sprite::from_image or ImageNode"),
                ("Handle<Mesh>", "Handle<Mesh> no longer a component - use Mesh2d/Mesh3d wrapper"),
                ("Handle<Material>", "Handle<Material> no longer a component - use MeshMaterial2d/3d wrapper"),
                ("TextureAtlas", "TextureAtlas no longer a component - use Sprite::from_atlas_image"),
                ("Msaa", "Msaa is now a per-camera component, not a global resource"),
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
