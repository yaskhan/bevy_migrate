import pytest
import os
from pathlib import Path
from bevymigrate.core.ast_processor import ASTProcessor, ASTTransformation

def test_nested_imports_transformation():
    """
    Test that nested imports are correctly transformed using both full and sub-path patterns.
    """
    project_root = Path(".").absolute()
    processor = ASTProcessor(project_root, dry_run=True)
    
    # Realistic transformations based on the fix
    transformations = [
        # Full path
        ASTTransformation(
            pattern="bevy::a11y::Focus",
            replacement="bevy::input_focus::InputFocus",
            description="Replace Focus path"
        ),
        # Sub-path for nested use
        ASTTransformation(
            pattern="a11y::Focus",
            replacement="input_focus::InputFocus",
            description="Replace Focus sub-path"
        ),
        # Module path
        ASTTransformation(
            pattern="bevy::a11y",
            replacement="bevy::input_focus",
            description="Replace a11y module path"
        ),
        # Final identifier
        ASTTransformation(
            pattern="Focus",
            replacement="InputFocus",
            description="Replace Focus identifier"
        )
    ]
    
    content = """
use bevy::a11y::Focus;
use bevy::{a11y::Focus, window::Window};
use bevy::a11y::{Focus, SomethingElse};

fn main() {
    let _ = Focus;
    let _ = a11y::Focus;
}
"""
    
    # Create a temporary file in the project root to satisfy subpath check
    temp_path = project_root / "test_nested_final.rs"
    with open(temp_path, "w") as f:
        f.write(content)
    
    try:
        result = processor._process_file(temp_path, transformations)
        transformed = result.transformed_content
        
        print(f"Transformed content:\n{transformed}")
        
        # Verify transformations
        assert "use bevy::input_focus::InputFocus;" in transformed
        assert "use bevy::{input_focus::InputFocus, window::Window};" in transformed
        assert "use bevy::input_focus::{InputFocus, SomethingElse};" in transformed
        assert "let _ = InputFocus;" in transformed
        assert "let _ = input_focus::InputFocus;" in transformed
        
    finally:
        if temp_path.exists():
            temp_path.unlink()

if __name__ == "__main__":
    test_nested_imports_transformation()
