"""
Migration Rules Configuration
Centralized configuration for migration rules, patterns, and transformations
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MigrationRule:
    """Configuration for a single migration rule"""
    name: str
    description: str
    pattern: str
    replacement: str
    file_patterns: List[str] = field(default_factory=lambda: ["*.rs"])
    enabled: bool = True
    priority: int = 0  # Higher priority rules are applied first
    requires_manual_review: bool = False
    breaking_change: bool = False
    
    def __post_init__(self):
        """Validate rule configuration"""
        if not self.name:
            raise ValueError("Rule name cannot be empty")
        if not self.pattern:
            raise ValueError("Rule pattern cannot be empty")
        if not self.replacement:
            raise ValueError("Rule replacement cannot be empty")


@dataclass
class VersionMigrationConfig:
    """Configuration for migration between specific versions"""
    from_version: str
    to_version: str
    description: str
    rules: List[MigrationRule] = field(default_factory=list)
    pre_migration_checks: List[str] = field(default_factory=list)
    post_migration_checks: List[str] = field(default_factory=list)
    manual_review_patterns: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    
    def add_rule(self, rule: MigrationRule) -> None:
        """Add a migration rule to this version configuration"""
        self.rules.append(rule)
    
    def get_enabled_rules(self) -> List[MigrationRule]:
        """Get only enabled rules, sorted by priority"""
        enabled_rules = [rule for rule in self.rules if rule.enabled]
        return sorted(enabled_rules, key=lambda r: r.priority, reverse=True)


class MigrationRulesConfig:
    """
    Central configuration manager for all migration rules
    """
    
    def __init__(self):
        """Initialize the migration rules configuration"""
        self.logger = logging.getLogger(__name__)
        self._version_configs: Dict[str, VersionMigrationConfig] = {}
        self._global_settings = {
            "backup_enabled": True,
            "dry_run_default": False,
            "max_file_size_mb": 10,
            "exclude_patterns": [
                "target/**",
                ".git/**",
                "*.lock",
                "migration_backup/**"
            ],
            "supported_file_types": [".rs", ".toml", ".yaml", ".yml", ".json"],
            "ast_grep_timeout": 30,
            "validation_enabled": True
        }
        
        # Initialize all version configurations
        self._initialize_version_configs()
        
        self.logger.info("Migration rules configuration initialized")
    
    def _initialize_version_configs(self) -> None:
        """Initialize migration configurations for all supported version transitions"""
        # Initialize 0.15 -> 0.16 migration
        self._init_0_15_to_0_16()
        
        # Initialize 0.16 -> 0.17 migration
        self._init_0_16_to_0_17()
        
        # Initialize 0.17 -> 0.18 migration
        self._init_0_17_to_0_18()
    
    def _init_0_15_to_0_16(self) -> None:
        """Initialize migration rules for 0.15 -> 0.16"""
        config = VersionMigrationConfig(
            from_version="0.15",
            to_version="0.16",
            description="Migration from Bevy 0.15 to 0.16 - Plugin system and ECS updates",
            pre_migration_checks=[
                "check_bevy_dependency_version",
                "validate_rust_project_structure",
                "check_for_custom_plugins"
            ],
            post_migration_checks=[
                "validate_cargo_toml_updated",
                "check_compilation_success",
                "validate_plugin_registration"
            ],
            manual_review_patterns=[
                "SystemLabel",
                "RunCriteria",
                "ParallelSystemDescriptorCoercion",
                "insert_bundle"
            ],
            breaking_changes=[
                "Plugin system API changes",
                "System registration changes",
                "Bundle spawning changes"
            ]
        )
        
        # Plugin system rules
        config.add_rule(MigrationRule(
            name="update_add_plugin_to_add_plugins",
            description="Update add_plugin to add_plugins for single plugin",
            pattern=r"\.add_plugin\(([^)]+)\)",
            replacement=r".add_plugins(\1)",
            priority=100,
            breaking_change=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_default_plugins",
            description="Update DefaultPlugins to use add_plugins",
            pattern=r"\.add_plugin\(DefaultPlugins\)",
            replacement=r".add_plugins(DefaultPlugins)",
            priority=95
        ))
        
        config.add_rule(MigrationRule(
            name="update_minimal_plugins",
            description="Update MinimalPlugins to use add_plugins",
            pattern=r"\.add_plugin\(MinimalPlugins\)",
            replacement=r".add_plugins(MinimalPlugins)",
            priority=95
        ))
        
        # System registration rules
        config.add_rule(MigrationRule(
            name="update_add_system",
            description="Update system registration to use schedules",
            pattern=r"\.add_system\(([^)]+)\)",
            replacement=r".add_systems(Update, \1)",
            priority=90,
            breaking_change=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_add_startup_system",
            description="Update startup system registration",
            pattern=r"\.add_startup_system\(([^)]+)\)",
            replacement=r".add_systems(Startup, \1)",
            priority=90,
            breaking_change=True
        ))
        
        # Entity spawning rules
        config.add_rule(MigrationRule(
            name="update_spawn_tuple_wrapping",
            description="Update Commands::spawn to not require tuple wrapping",
            pattern=r"commands\.spawn\(\(([^)]+)\)\)",
            replacement=r"commands.spawn(\1)",
            priority=85
        ))
        
        config.add_rule(MigrationRule(
            name="update_insert_bundle",
            description="Update entity spawning to use new bundle syntax",
            pattern=r"commands\.spawn\(\)\.insert_bundle\(([^)]+)\)",
            replacement=r"commands.spawn(\1)",
            priority=85,
            requires_manual_review=True
        ))
        
        self._version_configs["0.15->0.16"] = config
    
    def _init_0_16_to_0_17(self) -> None:
        """Initialize migration rules for 0.16 -> 0.17"""
        config = VersionMigrationConfig(
            from_version="0.16",
            to_version="0.17",
            description="Migration from Bevy 0.16 to 0.17 - Required components and observer system",
            pre_migration_checks=[
                "check_bevy_dependency_version",
                "validate_bundle_usage",
                "check_observer_system_usage"
            ],
            post_migration_checks=[
                "validate_cargo_toml_updated",
                "check_required_components",
                "validate_observer_migration"
            ],
            manual_review_patterns=[
                "Bundle",
                "Observer",
                "ComponentHooks",
                "AssetEvent",
                "UiImage",
                "Interaction"
            ],
            breaking_changes=[
                "Bundle system replaced with required components",
                "Observer system API changes",
                "Input system updates",
                "Camera bundle changes"
            ]
        )
        
        # Camera bundle rules
        config.add_rule(MigrationRule(
            name="update_camera2d_bundle",
            description="Update Camera2dBundle to use required components",
            pattern=r"Camera2dBundle::default\(\)",
            replacement=r"Camera2d",
            priority=100,
            breaking_change=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_camera3d_bundle",
            description="Update Camera3dBundle to use required components",
            pattern=r"Camera3dBundle::default\(\)",
            replacement=r"Camera3d",
            priority=100,
            breaking_change=True
        ))
        
        # UI bundle rules
        config.add_rule(MigrationRule(
            name="update_node_bundle",
            description="Update NodeBundle to use required components system",
            pattern=r"NodeBundle\s*\{\s*style:\s*Style\s*\{[^}]*\}[^}]*\}",
            replacement=r"Node::default()",
            priority=95,
            requires_manual_review=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_button_bundle",
            description="Update ButtonBundle to use required components",
            pattern=r"ButtonBundle::default\(\)",
            replacement=r"Button",
            priority=95
        ))
        
        config.add_rule(MigrationRule(
            name="update_text_bundle",
            description="Update TextBundle to use new Text component",
            pattern=r"TextBundle::from_section\(([^,]+),\s*([^)]+)\)",
            replacement=r"Text::new(\1)",
            priority=90,
            requires_manual_review=True
        ))
        
        # Input system rules
        config.add_rule(MigrationRule(
            name="update_input_keycode",
            description="Update input system to use ButtonInput",
            pattern=r"Input<KeyCode>",
            replacement=r"ButtonInput<KeyCode>",
            priority=85,
            breaking_change=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_input_mousebutton",
            description="Update mouse input to use ButtonInput",
            pattern=r"Input<MouseButton>",
            replacement=r"ButtonInput<MouseButton>",
            priority=85,
            breaking_change=True
        ))
        
        # Observer system rules
        config.add_rule(MigrationRule(
            name="update_observer_registration",
            description="Update observer registration to use new API",
            pattern=r"app\.add_observer\(([^)]+)\)",
            replacement=r"app.observe(\1)",
            priority=80,
            breaking_change=True
        ))
        
        # Mesh and material rules
        config.add_rule(MigrationRule(
            name="update_pbr_bundle",
            description="Update PbrBundle to use required components",
            pattern=r"PbrBundle\s*\{\s*mesh:\s*([^,]+),\s*material:\s*([^,]+)[^}]*\}",
            replacement=r"(\1, \2)",
            priority=75,
            requires_manual_review=True
        ))
        
        # Light bundle rules
        config.add_rule(MigrationRule(
            name="update_point_light_bundle",
            description="Update PointLightBundle to use required components",
            pattern=r"PointLightBundle::default\(\)",
            replacement=r"PointLight::default()",
            priority=70
        ))
        
        config.add_rule(MigrationRule(
            name="update_directional_light_bundle",
            description="Update DirectionalLightBundle to use required components",
            pattern=r"DirectionalLightBundle::default\(\)",
            replacement=r"DirectionalLight::default()",
            priority=70
        ))
        
        self._version_configs["0.16->0.17"] = config
    
    def _init_0_17_to_0_18(self) -> None:
        """Initialize migration rules for 0.17 -> 0.18"""
        config = VersionMigrationConfig(
            from_version="0.17",
            to_version="0.18",
            description="Migration from Bevy 0.17 to 0.18 - Rendering, UI, and system improvements",
            pre_migration_checks=[
                "check_bevy_dependency_version",
                "validate_rendering_usage",
                "check_ui_system_usage",
                "validate_window_system"
            ],
            post_migration_checks=[
                "validate_cargo_toml_updated",
                "check_rendering_pipeline",
                "validate_ui_updates",
                "check_window_configuration"
            ],
            manual_review_patterns=[
                "WindowDescriptor",
                "shape::",
                "TextStyle",
                "ComputedVisibility",
                "AssetLoader",
                "Shader::from_wgsl",
                "Image::new_fill",
                "OrthographicProjection"
            ],
            breaking_changes=[
                "Window system redesign",
                "Mesh shape API changes",
                "Text styling reorganization",
                "Visibility system updates",
                "Asset loading API changes",
                "Shader system improvements"
            ]
        )
        
        # Window system rules
        config.add_rule(MigrationRule(
            name="update_window_descriptor",
            description="Update window configuration to use Window struct",
            pattern=r"WindowDescriptor\s*\{\s*title:\s*([^,]+)[^}]*\}",
            replacement=r"Window { title: \1, .. }",
            priority=100,
            breaking_change=True,
            requires_manual_review=True
        ))
        
        # Mesh system rules
        config.add_rule(MigrationRule(
            name="update_cube_mesh",
            description="Update cube mesh creation to use Cuboid",
            pattern=r"Mesh::from\(shape::Cube\s*\{\s*size:\s*([^}]+)\s*\}\)",
            replacement=r"Mesh::from(Cuboid::new(\1, \1, \1))",
            priority=95,
            breaking_change=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_plane_mesh",
            description="Update plane mesh creation",
            pattern=r"Mesh::from\(shape::Plane\s*\{\s*size:\s*([^}]+)\s*\}\)",
            replacement=r"Mesh::from(Plane3d::default().mesh().size(\1, \1))",
            priority=95,
            breaking_change=True,
            requires_manual_review=True
        ))
        
        # Text system rules
        config.add_rule(MigrationRule(
            name="update_text_style",
            description="Update text styling to use TextFont",
            pattern=r"TextStyle\s*\{\s*font_size:\s*([^,]+)[^}]*\}",
            replacement=r"TextFont { font_size: \1, .. }",
            priority=90,
            breaking_change=True,
            requires_manual_review=True
        ))
        
        # UI system rules
        config.add_rule(MigrationRule(
            name="update_ui_positioning",
            description="Update UI positioning system",
            pattern=r"position_type:\s*PositionType::Absolute",
            replacement=r"position: Position::Absolute",
            priority=85,
            breaking_change=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_ui_interaction",
            description="Update UI interaction states",
            pattern=r"Interaction::Clicked",
            replacement=r"Interaction::Pressed",
            priority=85,
            breaking_change=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_ui_margin_values",
            description="Update UI margin values to use Val::Px",
            pattern=r"margin:\s*UiRect::all\(([^)]+)\)",
            replacement=r"margin: UiRect::all(Val::Px(\1))",
            priority=80,
            requires_manual_review=True
        ))
        
        # Input system rules
        config.add_rule(MigrationRule(
            name="update_keyboard_input",
            description="Update keyboard input to use logical keys",
            pattern=r"KeyboardInput\s*\{\s*key_code:\s*Some\(([^)]+)\)[^}]*\}",
            replacement=r"KeyboardInput { logical_key: Some(\1), .. }",
            priority=75,
            breaking_change=True
        ))
        
        # Camera system rules
        config.add_rule(MigrationRule(
            name="update_orthographic_projection",
            description="Update orthographic projection scaling",
            pattern=r"OrthographicProjection\s*\{\s*scale:\s*([^,]+)[^}]*\}",
            replacement=r"OrthographicProjection { scaling_mode: ScalingMode::FixedVertical(\1), .. }",
            priority=70,
            breaking_change=True,
            requires_manual_review=True
        ))
        
        # Asset system rules
        config.add_rule(MigrationRule(
            name="update_asset_watching",
            description="Update asset watching with improved error handling",
            pattern=r"asset_server\.watch_for_changes\(\)",
            replacement=r"asset_server.watch_for_changes().unwrap()",
            priority=65,
            requires_manual_review=True
        ))
        
        config.add_rule(MigrationRule(
            name="update_shader_creation",
            description="Update shader creation with file tracking",
            pattern=r"Shader::from_wgsl\(([^)]+)\)",
            replacement=r"Shader::from_wgsl(\1, file!())",
            priority=60,
            breaking_change=True
        ))
        
        # Visibility system rules
        config.add_rule(MigrationRule(
            name="update_computed_visibility",
            description="Update visibility system components",
            pattern=r"ComputedVisibility",
            replacement=r"InheritedVisibility",
            priority=55,
            breaking_change=True
        ))
        
        # Transform system rules
        config.add_rule(MigrationRule(
            name="remove_transform_bundle",
            description="Remove TransformBundle usage in favor of Transform component",
            pattern=r"TransformBundle::from_transform\(([^)]+)\)",
            replacement=r"\1",
            priority=50,
            breaking_change=True
        ))
        
        self._version_configs["0.17->0.18"] = config
    
    def get_migration_config(self, from_version: str, to_version: str) -> Optional[VersionMigrationConfig]:
        """
        Get migration configuration for specific version transition
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            VersionMigrationConfig or None if not found
        """
        key = f"{from_version}->{to_version}"
        return self._version_configs.get(key)
    
    def get_all_migration_configs(self) -> Dict[str, VersionMigrationConfig]:
        """Get all available migration configurations"""
        return self._version_configs.copy()
    
    def get_supported_versions(self) -> List[str]:
        """Get list of all supported versions"""
        versions = set()
        for config in self._version_configs.values():
            versions.add(config.from_version)
            versions.add(config.to_version)
        return sorted(list(versions))
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """
        Get the migration path between two versions
        
        Args:
            from_version: Starting version
            to_version: Target version
            
        Returns:
            List of version transition keys
        """
        supported_versions = ["0.15", "0.16", "0.17", "0.18"]
        
        try:
            from_idx = supported_versions.index(from_version)
            to_idx = supported_versions.index(to_version)
        except ValueError:
            return []
        
        if from_idx >= to_idx:
            return []
        
        path = []
        for i in range(from_idx, to_idx):
            current_version = supported_versions[i]
            next_version = supported_versions[i + 1]
            path.append(f"{current_version}->{next_version}")
        
        return path
    
    def validate_rule(self, rule: MigrationRule) -> List[str]:
        """
        Validate a migration rule
        
        Args:
            rule: Rule to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not rule.name:
            errors.append("Rule name cannot be empty")
        
        if not rule.pattern:
            errors.append("Rule pattern cannot be empty")
        
        if not rule.replacement:
            errors.append("Rule replacement cannot be empty")
        
        # Try to compile the pattern as regex
        try:
            import re
            re.compile(rule.pattern)
        except re.error as e:
            errors.append(f"Invalid regex pattern: {e}")
        
        # Validate file patterns
        if not rule.file_patterns:
            errors.append("At least one file pattern must be specified")
        
        return errors
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """Get a global configuration setting"""
        return self._global_settings.get(key, default)
    
    def set_global_setting(self, key: str, value: Any) -> None:
        """Set a global configuration setting"""
        self._global_settings[key] = value
        self.logger.debug(f"Updated global setting: {key} = {value}")
    
    def get_all_global_settings(self) -> Dict[str, Any]:
        """Get all global configuration settings"""
        return self._global_settings.copy()
    
    def export_config(self, file_path: Path) -> bool:
        """
        Export configuration to a file
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            import json
            
            export_data = {
                "global_settings": self._global_settings,
                "version_configs": {}
            }
            
            # Convert version configs to serializable format
            for key, config in self._version_configs.items():
                export_data["version_configs"][key] = {
                    "from_version": config.from_version,
                    "to_version": config.to_version,
                    "description": config.description,
                    "pre_migration_checks": config.pre_migration_checks,
                    "post_migration_checks": config.post_migration_checks,
                    "manual_review_patterns": config.manual_review_patterns,
                    "breaking_changes": config.breaking_changes,
                    "rules": [
                        {
                            "name": rule.name,
                            "description": rule.description,
                            "pattern": rule.pattern,
                            "replacement": rule.replacement,
                            "file_patterns": rule.file_patterns,
                            "enabled": rule.enabled,
                            "priority": rule.priority,
                            "requires_manual_review": rule.requires_manual_review,
                            "breaking_change": rule.breaking_change
                        }
                        for rule in config.rules
                    ]
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Configuration exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}", exc_info=True)
            return False
    
    def import_config(self, file_path: Path) -> bool:
        """
        Import configuration from a file
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if import was successful, False otherwise
        """
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Import global settings
            if "global_settings" in import_data:
                self._global_settings.update(import_data["global_settings"])
            
            # Import version configs
            if "version_configs" in import_data:
                for key, config_data in import_data["version_configs"].items():
                    config = VersionMigrationConfig(
                        from_version=config_data["from_version"],
                        to_version=config_data["to_version"],
                        description=config_data["description"],
                        pre_migration_checks=config_data.get("pre_migration_checks", []),
                        post_migration_checks=config_data.get("post_migration_checks", []),
                        manual_review_patterns=config_data.get("manual_review_patterns", []),
                        breaking_changes=config_data.get("breaking_changes", [])
                    )
                    
                    # Import rules
                    for rule_data in config_data.get("rules", []):
                        rule = MigrationRule(
                            name=rule_data["name"],
                            description=rule_data["description"],
                            pattern=rule_data["pattern"],
                            replacement=rule_data["replacement"],
                            file_patterns=rule_data.get("file_patterns", ["*.rs"]),
                            enabled=rule_data.get("enabled", True),
                            priority=rule_data.get("priority", 0),
                            requires_manual_review=rule_data.get("requires_manual_review", False),
                            breaking_change=rule_data.get("breaking_change", False)
                        )
                        config.add_rule(rule)
                    
                    self._version_configs[key] = config
            
            self.logger.info(f"Configuration imported from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}", exc_info=True)
            return False
    
    def get_rules_by_priority(self, from_version: str, to_version: str) -> List[MigrationRule]:
        """
        Get migration rules sorted by priority
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            List of rules sorted by priority (highest first)
        """
        config = self.get_migration_config(from_version, to_version)
        if not config:
            return []
        
        return config.get_enabled_rules()
    
    def get_breaking_change_rules(self, from_version: str, to_version: str) -> List[MigrationRule]:
        """
        Get rules that represent breaking changes
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            List of breaking change rules
        """
        config = self.get_migration_config(from_version, to_version)
        if not config:
            return []
        
        return [rule for rule in config.get_enabled_rules() if rule.breaking_change]
    
    def get_manual_review_rules(self, from_version: str, to_version: str) -> List[MigrationRule]:
        """
        Get rules that require manual review
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            List of rules requiring manual review
        """
        config = self.get_migration_config(from_version, to_version)
        if not config:
            return []
        
        return [rule for rule in config.get_enabled_rules() if rule.requires_manual_review]
    
    def get_migration_summary(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Get a summary of migration configuration
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            Dictionary with migration summary
        """
        config = self.get_migration_config(from_version, to_version)
        if not config:
            return {"error": "Migration configuration not found"}
        
        enabled_rules = config.get_enabled_rules()
        breaking_rules = [r for r in enabled_rules if r.breaking_change]
        manual_rules = [r for r in enabled_rules if r.requires_manual_review]
        
        return {
            "from_version": from_version,
            "to_version": to_version,
            "description": config.description,
            "total_rules": len(enabled_rules),
            "breaking_change_rules": len(breaking_rules),
            "manual_review_rules": len(manual_rules),
            "pre_migration_checks": len(config.pre_migration_checks),
            "post_migration_checks": len(config.post_migration_checks),
            "manual_review_patterns": config.manual_review_patterns,
            "breaking_changes": config.breaking_changes,
            "rule_priorities": [r.priority for r in enabled_rules],
            "file_patterns_affected": list(set(
                pattern for rule in enabled_rules for pattern in rule.file_patterns
            ))
        }


# Global instance for easy access
migration_rules_config = MigrationRulesConfig()


def get_migration_rules_config() -> MigrationRulesConfig:
    """Get the global migration rules configuration instance"""
    return migration_rules_config


def get_migration_rules(from_version: str, to_version: str) -> List[MigrationRule]:
    """
    Convenience function to get migration rules for a version transition
    
    Args:
        from_version: Source version
        to_version: Target version
        
    Returns:
        List of migration rules
    """
    config = migration_rules_config.get_migration_config(from_version, to_version)
    if config:
        return config.get_enabled_rules()
    return []


def validate_migration_path(from_version: str, to_version: str) -> bool:
    """
    Validate that a migration path exists between two versions
    
    Args:
        from_version: Source version
        to_version: Target version
        
    Returns:
        True if migration path exists, False otherwise
    """
    path = migration_rules_config.get_migration_path(from_version, to_version)
    return len(path) > 0


def get_supported_migration_versions() -> List[str]:
    """Get list of all supported migration versions"""
    return migration_rules_config.get_supported_versions()