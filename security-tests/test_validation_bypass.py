"""Tests for validation bypass vulnerabilities."""

import pytest
from app.services.code_validator import CodeValidator


class TestValidationBypassAttacks:
    """Test attempts to bypass code validation mechanisms."""

    @pytest.mark.critical
    def test_comment_sanitization_vulnerability(self, code_validator: CodeValidator):
        """Test the critical comment sanitization vulnerability."""
        # This test exposes the actual vulnerability in the current implementation
        vulnerable_codes = [
            'import os; x = "safe string" # os.system("rm -rf /")',
            'print("hello") # import subprocess; subprocess.run(["ls"])',
            'safe_var = "value" # __import__("sys").exit()',
            'data = {"key": "value"} # eval("malicious_code")',
            "normal_code() # exec('import os')",
        ]
        
        for code in vulnerable_codes:
            # The current sanitize_code method has a bug:
            # It only removes comments if there are no quotes in the line
            # This allows dangerous code to be hidden in comments when quotes are present
            sanitized = code_validator.sanitize_code(code)
            
            # Check if dangerous code remains after sanitization
            if 'import os' in sanitized or 'subprocess' in sanitized or '__import__' in sanitized:
                pytest.fail(
                    f"CRITICAL VULNERABILITY: Comment sanitization failed!\n"
                    f"Original: {code}\n"
                    f"Sanitized: {sanitized}\n"
                    f"Dangerous code remains in sanitized output!"
                )

    @pytest.mark.high
    def test_multiline_comment_bypass(self, code_validator: CodeValidator):
        """Test multiline comment bypass attempts."""
        malicious_codes = [
            '"""\nSafe docstring\n"""\nimport os',
            "'''\nMultiline comment\n'''\nimport sys",
            '# Safe comment\nimport os  # Hidden danger',
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Multiline comment bypass should be blocked: {code}"

    @pytest.mark.high
    def test_string_literal_hiding(self, code_validator: CodeValidator):
        """Test hiding dangerous code in string literals."""
        malicious_codes = [
            'code = "import os"; exec(code)',
            'dangerous = "eval"; globals()[dangerous]("__import__(\'os\')")',
            'cmd = "system"; getattr(__import__("os"), cmd)("ls")',
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"String literal hiding should be blocked: {code}"

    @pytest.mark.medium
    def test_whitespace_obfuscation(self, code_validator: CodeValidator):
        """Test whitespace and formatting obfuscation."""
        malicious_codes = [
            "import\tos",  # Tab character
            "import \nos",  # Space + newline
            "import\u00a0os",  # Non-breaking space
            "import\u2000os",  # En quad space
            "import\u3000os",  # Ideographic space
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Whitespace obfuscation should be blocked: {code}"

    @pytest.mark.medium
    def test_case_sensitivity_bypass(self, code_validator: CodeValidator):
        """Test case sensitivity bypass attempts."""
        # Note: Python is case-sensitive, but test for completeness
        malicious_codes = [
            "Import os",  # Capital I
            "IMPORT OS",  # All caps
            "Import OS",  # Mixed case
        ]
        
        for code in malicious_codes:
            # These should fail due to syntax errors, not security validation
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Case sensitivity bypass should fail: {code}"

    @pytest.mark.high
    def test_ast_parsing_edge_cases(self, code_validator: CodeValidator):
        """Test edge cases in AST parsing."""
        edge_cases = [
            "# Just a comment",
            "",  # Empty code
            "   ",  # Whitespace only
            "\n\n\n",  # Newlines only
            "pass",  # No-op statement
            "...",  # Ellipsis
        ]
        
        for code in edge_cases:
            # These should be safe (or fail gracefully)
            is_safe, violations = code_validator.validate_code(code)
            # Empty/whitespace code should be handled gracefully
            assert is_safe or "Syntax error" in str(violations), f"Edge case should be handled: {code}"

    @pytest.mark.medium
    def test_complexity_calculation_accuracy(self, code_validator: CodeValidator):
        """Test that complexity calculation is accurate."""
        test_cases = [
            ("x = 1", 0),  # Simple assignment
            ("if True: pass", 1),  # Single if
            ("for i in range(5): pass", 1),  # Single loop
            ("def func(): pass", 2),  # Function definition
            ("class Test: pass", 3),  # Class definition
            ("if True:\n    for i in range(5):\n        if i > 2: pass", 3),  # Nested
        ]
        
        for code, expected_min_complexity in test_cases:
            complexity = code_validator.get_complexity_score(code)
            assert complexity >= expected_min_complexity, f"Complexity underestimated for: {code}"

    @pytest.mark.high
    def test_length_validation_accuracy(self, code_validator: CodeValidator):
        """Test that length validation is accurate."""
        # Test maximum code length
        max_length = 10000  # From settings.MAX_CODE_LENGTH
        
        # Code just under limit should pass
        long_safe_code = "print('x')\n" * (max_length // 12)  # Each line ~12 chars
        is_safe, violations = code_validator.validate_code(long_safe_code)
        assert is_safe, "Code under length limit should pass"
        
        # Code over limit should fail
        too_long_code = "x" * (max_length + 1)
        is_safe, violations = code_validator.validate_code(too_long_code)
        assert not is_safe, "Code over length limit should fail"
        assert any("exceeds maximum length" in violation for violation in violations)

    @pytest.mark.high
    def test_line_count_validation(self, code_validator: CodeValidator):
        """Test line count validation."""
        # Test maximum line count (100 lines)
        many_lines = "\n".join(["print('line')" for _ in range(101)])
        is_safe, violations = code_validator.validate_code(many_lines)
        assert not is_safe, "Code with >100 lines should fail"
        assert any("too many lines" in violation for violation in violations)

    @pytest.mark.medium
    def test_syntax_error_handling(self, code_validator: CodeValidator):
        """Test handling of syntax errors."""
        syntax_errors = [
            "import os(",  # Unclosed parenthesis
            "if True",  # Missing colon
            "def func(",  # Incomplete function
            "import",  # Incomplete import
            "print('unclosed string",  # Unclosed string
        ]
        
        for code in syntax_errors:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Syntax error should be caught: {code}"
            assert any("syntax error" in violation.lower() for violation in violations)

    @pytest.mark.critical
    def test_safe_code_passes_validation(self, code_validator: CodeValidator, safe_code_samples: list):
        """Test that legitimate safe code passes validation."""
        for code in safe_code_samples:
            is_safe, violations = code_validator.validate_code(code)
            assert is_safe, f"Safe code should pass validation: {code}\nViolations: {violations}"
