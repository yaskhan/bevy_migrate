# Bevy Engine Migration Tool

Automated migration tool for Bevy Engine projects between versions 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, and 0.18.

## 📋 Description

This tool automates the migration process for projects using the Bevy game engine between different versions. It supports migrations from version 0.12 to 0.18 using a modular architecture and AST code analysis.

### Key Features

- 🔄 **Automatic migration** between Bevy versions 0.12 → 0.13 → 0.14 → 0.15 → 0.16 → 0.17 → 0.18
- 🧩 **Modular architecture** with separate modules for each version
- 🔍 **AST analysis** using ast-grep for precise code transformations
- 📁 **Smart file management** with automatic backups
- 🎯 **Automatic version detection** of your project
- 🧠 **Complex logic support** using Python callbacks for advanced transformations
- 🛡️ **Safe dry-run mode** for previewing changes
- 📊 **Detailed reporting** of the migration process

### Supported Migrations

- **0.12 → 0.13**: WorldQuery split into QueryData/QueryFilter, Input renamed to ButtonInput, TextureAtlas rework, rendering and UI changes
- **0.13 → 0.14**: Complete Color overhaul (Srgba/LinearRgba), AnimationGraph, SubApp split, Dir2/Dir3, massive rendering changes, winit 0.30, wgpu 0.20
- **0.15 → 0.16**: Plugin system updates, system registration, entity creation improvements (72 transformations)
- **0.16 → 0.17**: Required components system, observer updates, input system changes (130+ transformations in 3 parts)
- **0.17 → 0.18**: Rendering improvements, UI system, window system, new features (105+ transformations)

## 🛠️ Installation

### Requirements

- Python 3.7 or higher
- ast-grep (recommended for better transformation accuracy)
- Rust project with Bevy Engine

### Installing Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd bevy-migration-tool

# Install Python dependencies
pip install -r requirements.txt

# Install ast-grep (optional but recommended)
# On Windows:
cargo install ast-grep

# On macOS:
brew install ast-grep

# On Linux:
cargo install ast-grep
# or use your distribution's package manager
```

## 🚀 Usage

### Basic Usage

```bash
# Migrate project to the latest supported version (0.18)
python src/main.py /path/to/your/bevy/project

# Migrate to a specific version
python src/main.py /path/to/your/bevy/project --target-version 0.17

# Preview changes without modifying files
python src/main.py /path/to/your/bevy/project --dry-run

# Verbose output with debug information
python src/main.py /path/to/your/bevy/project --verbose
```

### Advanced Options

```bash
# Migrate with custom backup directory
python src/main.py /path/to/project --backup-dir ./my_backups

# Force migration (if version is not detected automatically)
python src/main.py /path/to/project --force

# Exclude specific files or directories
python src/main.py /path/to/project --exclude "target/**" "*.bak" "custom_dir/**"

# Combined example
python src/main.py ./my_bevy_game --target-version 0.17 --dry-run --verbose --backup-dir ./backups
```

### Command Examples

```bash
# Example 1: Migrate a simple project
python src/main.py ./my_game

# Example 2: Preview migration with verbose output
python src/main.py ./my_game --dry-run --verbose

# Example 3: Step-by-step migration to version 0.16
python src/main.py ./my_game --target-version 0.16

# Example 4: Migration with custom settings
python src/main.py ./my_game --backup-dir ./project_backups --exclude "assets/**" --verbose
```

## 📖 How to Use

### Step-by-Step Guide

1. **Prepare your project**
   ```bash
   # Make sure your project is under version control
   cd /path/to/your/bevy/project
   git add .
   git commit -m "Before Bevy migration"
   ```

2. **Check current version**
   ```bash
   # The tool will auto-detect the version, but you can check Cargo.toml
   cat Cargo.toml | grep bevy
   ```

3. **Run migration in preview mode**
   ```bash
   python src/main.py . --dry-run --verbose
   ```

4. **Execute migration**
   ```bash
   python src/main.py .
   ```

5. **Verify results**
   ```bash
   # Check that the project compiles
   cargo check
   
   # Run tests
   cargo test
   
   # Run the project
   cargo run
   ```

### Command Line Parameters

| Parameter | Description | Example |
|----------|----------|---------|
| `project_path` | Path to Bevy project (required) | `./my_game` |
| `--target-version` | Target version for migration | `--target-version 0.17` |
| `--dry-run` | Preview mode | `--dry-run` |
| `--backup-dir` | Directory for backups | `--backup-dir ./backups` |
| `--verbose, -v` | Verbose output | `--verbose` |
| `--force` | Force migration | `--force` |
| `--exclude` | Exclude files/directories | `--exclude "target/**" "*.tmp"` |

## 🏗️ Project Architecture

```
src/
├── main.py                     # Application entry point
├── core/                       # Core components
│   ├── migration_engine.py     # Migration engine
│   ├── ast_processor.py        # AST processor
│   └── file_manager.py         # File manager
├── migrations/                 # Migration modules
│   ├── base_migration.py       # Base migration class
│   ├── v0_12_to_0_13.py       # Migration 0.12 → 0.13
│   ├── v0_13_to_0_14.py       # Migration 0.13 → 0.14
│   ├── v0_14_to_0_15_part1.py # Migration 0.14 → 0.15 Part 1 (Core API)
│   ├── v0_14_to_0_15_part2.py # Migration 0.14 → 0.15 Part 2 (Required Components)
│   ├── v0_15_to_0_16.py       # Migration 0.15 → 0.16 (72 transformations)
│   ├── v0_16_to_0_17_part1.py # Migration 0.16 → 0.17 Part 1 (Event/Message split)
│   ├── v0_16_to_0_17_part2.py # Migration 0.16 → 0.17 Part 2 (bevy_render reorganization)
│   ├── v0_16_to_0_17_part3.py # Migration 0.16 → 0.17 Part 3 (Entity representation)
│   └── v0_17_to_0_18.py       # Migration 0.17 → 0.18 (105+ transformations)
├── utils/                      # Utilities
│   └── version_detector.py     # Version detection
└── config/                     # Configuration
    └── migration_rules.py      # Migration rules
```

### Core Components

- **MigrationEngine**: Coordinates the migration process
- **ASTProcessor**: Performs code transformations using AST
- **FileManager**: Manages file operations and backups
- **VersionDetector**: Automatically detects Bevy version in the project
- **BaseMigration**: Base class for all migration modules

## 📊 Migration Statistics

| Migration | Transformations | Parts | Breaking Changes |
|-----------|----------------|-------|------------------|
| 0.12→0.13 | ~40 | 1 | 40+ |
| 0.13→0.14 | ~60 | 1 | 60+ |
| 0.14→0.15 | ~80 | 2 | 80+ |
| 0.15→0.16 | 72 | 1 | 70+ |
| 0.16→0.17 | 130+ | 3 | 150+ |
| 0.17→0.18 | 105+ | 1 | 80+ |
| **Total** | **485+** | **9** | **480+** |

## 🔧 Configuration

The tool uses a centralized configuration system in `src/config/migration_rules.py`. You can customize:

- Transformation rules for each version
- File patterns to process
- Exclusions and filters
- Rule priority levels

### Example Custom Rule

```python
# Add a custom migration rule
rule = MigrationRule(
    name="custom_transformation",
    description="Custom transformation",
    pattern=r"old_pattern",
    replacement="new_pattern",
    file_patterns=["**/*.rs"],
    priority=100
)
```

## 🛡️ Safety

The tool automatically creates backups before making changes:

- **Automatic backup** of all modified files
- **Dry-run mode** for safe preview
- **Validation** of project structure before migration
- **Rollback** in case of errors

### Backup Location

By default, backups are saved to:
```
your_project/
└── migration_backup/
    └── backup_YYYYMMDD_HHMMSS/
        ├── Cargo.toml
        ├── src/
        └── ...
```

## 📊 Reporting

The tool provides detailed information about the migration process:

- Number of processed files
- Applied transformations
- Warnings and errors
- Recommendations for manual review

### Example Output

```
2024-02-04 08:07:56 - INFO - Detected Bevy version: 0.15
2024-02-04 08:07:57 - INFO - Starting migration from 0.15 to 0.18
2024-02-04 08:07:58 - INFO - Migration path: 0.15 -> 0.16 -> 0.17 -> 0.18
2024-02-04 08:08:00 - INFO - Files processed: 25
2024-02-04 08:08:00 - INFO - Files modified: 18
2024-02-04 08:08:00 - INFO - Transformations applied: 47
2024-02-04 08:08:00 - INFO - Migration completed successfully!
```

## 🔍 Troubleshooting

### Common Issues

1. **ast-grep not found**
   ```bash
   # Install ast-grep
   cargo install ast-grep
   ```

2. **Cannot detect Bevy version**
   ```bash
   # Use the --force flag
   python src/main.py . --force
   ```

3. **Compilation errors after migration**
   - Check files requiring manual review
   - Refer to Bevy documentation for the specific version
   - Restore from backup if needed

### Logging

For detailed debug information:

```bash
python src/main.py . --verbose
```

Logs include:
- Detected code patterns
- Applied transformations
- Warnings about potential issues
- File processing statistics

## 🧠 Complex Migrations (Callbacks)

For transformations that require more than simple pattern replacement, you can use Python callbacks. This is useful for:
- Conditional replacements based on captured variables
- Dynamic string manipulation (e.g., casing, prefixing)
- Context-aware transformations

### Example: Dynamic Input Migration
```python
def input_callback(vars, file_path):
    t_type = vars.get("T", "")
    return f"Res<ButtonInput<{t_type}>>"

# In get_transformations:
transformations.append(self.create_transformation(
    pattern="Res<Input<$T>>",
    replacement="", # replacement is ignored when callback is present
    description="Res<Input<T>> -> Res<ButtonInput<T>>",
    callback=input_callback
))
```

## 🤝 Contributing

### Adding a New Migration

1. Create a new file in `src/migrations/`
2. Inherit from `BaseMigration`
3. Implement required methods
4. Register the migration in `MigrationEngine`

### Example Migration Module

```python
from migrations.base_migration import BaseMigration
from core.ast_processor import ASTTransformation

class Migration_0_18_to_0_19(BaseMigration):
    @property
    def from_version(self) -> str:
        return "0.18"
    
    @property
    def to_version(self) -> str:
        return "0.19"
    
    def get_transformations(self) -> List[ASTTransformation]:
        return [
            self.create_transformation(
                pattern="old_pattern",
                replacement="new_pattern",
                description="Transformation description"
            )
        ]
```

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support

If you encounter issues or have questions:

1. Check the "Troubleshooting" section
2. Create an issue in the project repository
3. Include logs from running with the `--verbose` flag

## 📚 Additional Resources

- [Official Bevy Documentation](https://bevyengine.org/)
- [Bevy Migration Guides](https://bevyengine.org/learn/migration-guides/)
- [ast-grep Documentation](https://ast-grep.github.io/)

---

**Note**: Always create backups of your projects before running migrations. While the tool creates automatic backups, extra precaution never hurts.
