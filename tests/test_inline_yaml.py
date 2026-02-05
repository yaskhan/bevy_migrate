
import unittest
from pathlib import Path
from typing import Dict
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.ast_processor import ASTProcessor, ASTTransformation

class TestInlineYAML(unittest.TestCase):
    def setUp(self):
        self.project_path = Path(".").resolve()
        self.processor = ASTProcessor(self.project_path, dry_run=True)

    def test_inline_yaml_standard(self):
        # A full YAML rule as a string
        yaml_rule = """
id: test-rule
language: rust
rule:
  pattern: foo($A)
fix: bar($A)
"""
        transformation = ASTTransformation(
            pattern="foo($A)",
            replacement="ignored",
            description="Test inline YAML",
            rule_yaml=yaml_rule
        )

        content = "fn main() { foo(1); }"
        result = self.processor._apply_ast_grep_transformation(
            content, 
            transformation, 
            Path("test.rs")
        )

        self.assertEqual(result, "fn main() { bar(1); }")

    def test_inline_yaml_with_callback(self):
        # A YAML rule that finds patterns for a callback
        yaml_rule = """
id: callback-rule
language: rust
rule:
  pattern: transform($VAL)
"""
        def my_callback(vars, path):
            val = vars.get("VAL", "")
            return f"RESULT_{val}"

        transformation = ASTTransformation(
            pattern="transform($VAL)",
            replacement="ignored",
            description="Test callback with inline YAML",
            rule_yaml=yaml_rule,
            callback=my_callback
        )

        content = "fn main() { transform(42); }"
        result = self.processor._apply_ast_grep_transformation(
            content, 
            transformation, 
            Path("test.rs")
        )

        self.assertEqual(result, "fn main() { RESULT_42; }")

if __name__ == "__main__":
    unittest.main()
