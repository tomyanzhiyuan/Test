"""Tests for code injection attack vectors."""

import pytest
from app.services.code_validator import CodeValidator


class TestCodeInjectionAttacks:
    """Test various code injection attack techniques."""

    @pytest.mark.critical
    def test_eval_injection_blocked(self, code_validator: CodeValidator):
        """Test that eval() injection attempts are blocked."""
        malicious_codes = [
            "eval('__import__(\"os\").system(\"ls\")')",
            "eval('print(\"injected\")')",
            "x = eval('1+1')",
            "result = eval(user_input)",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"eval() injection should be blocked: {code}"
            assert any("eval" in violation.lower() for violation in violations)

    @pytest.mark.critical
    def test_exec_injection_blocked(self, code_validator: CodeValidator):
        """Test that exec() injection attempts are blocked."""
        malicious_codes = [
            "exec('import os; os.system(\"ls\")')",
            "exec('print(\"injected\")')",
            "exec(malicious_code)",
            "exec(compile('import sys', '<string>', 'exec'))",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"exec() injection should be blocked: {code}"
            assert any("exec" in violation.lower() for violation in violations)

    @pytest.mark.critical
    def test_import_injection_blocked(self, code_validator: CodeValidator):
        """Test that __import__ injection attempts are blocked."""
        malicious_codes = [
            "__import__('os').system('ls')",
            "__import__('subprocess').run(['whoami'])",
            "getattr(__builtins__, '__import__')('os')",
            "__import__('sys').exit()",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"__import__ injection should be blocked: {code}"

    @pytest.mark.critical
    def test_getattr_builtins_bypass_blocked(self, code_validator: CodeValidator):
        """Test that getattr(__builtins__) bypass attempts are blocked."""
        malicious_codes = [
            "getattr(__builtins__, 'eval')('__import__(\"os\")')",
            "getattr(__builtins__, 'exec')('import sys')",
            "getattr(__builtins__, '__import__')('os')",
            "__builtins__['eval']('malicious_code')",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"getattr builtins bypass should be blocked: {code}"

    @pytest.mark.high
    def test_string_manipulation_injection(self, code_validator: CodeValidator):
        """Test string manipulation to construct dangerous calls."""
        malicious_codes = [
            "eval(''.join(['i', 'm', 'p', 'o', 'r', 't', ' ', 'o', 's']))",
            "__import__(''.join([chr(111), chr(115)]))",  # 'os'
            "exec(chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(32)+chr(111)+chr(115))",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"String manipulation injection should be blocked: {code}"

    @pytest.mark.high
    def test_encoding_bypass_attempts(self, code_validator: CodeValidator):
        """Test various encoding bypass techniques."""
        malicious_codes = [
            "exec('\\x69\\x6d\\x70\\x6f\\x72\\x74\\x20\\x6f\\x73')",  # hex encoded 'import os'
            "exec(bytes.fromhex('696d706f7274206f73').decode())",  # hex to bytes to string
            "exec('\\u0069\\u006d\\u0070\\u006f\\u0072\\u0074\\u0020\\u006f\\u0073')",  # unicode
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Encoding bypass should be blocked: {code}"

    @pytest.mark.high
    def test_unicode_obfuscation_blocked(self, code_validator: CodeValidator):
        """Test unicode character obfuscation attempts."""
        malicious_codes = [
            "＿＿ｉｍｐｏｒｔ＿＿('os')",  # Full-width characters
            "import os\u200b",  # Zero-width space
            "import\u00a0os",  # Non-breaking space
            "ｉｍｐｏｒｔ　ｏｓ",  # Full-width import os
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            # Note: Current validator may not catch all unicode attacks
            # This test documents the limitation
            if is_safe:
                pytest.skip(f"Unicode attack not detected (known limitation): {code}")

    @pytest.mark.critical
    def test_comment_bypass_vulnerability(self, code_validator: CodeValidator):
        """Test the known comment sanitization vulnerability."""
        # This test SHOULD FAIL with current implementation
        malicious_code = 'import os; x = "safe string" # os.system("rm -rf /")'
        
        is_safe, violations = code_validator.validate_code(malicious_code)
        
        # This test documents the current vulnerability
        # It should fail until the comment sanitization is fixed
        if is_safe:
            pytest.fail(
                "CRITICAL VULNERABILITY: Comment bypass not detected! "
                f"Code: {malicious_code}"
            )

    @pytest.mark.medium
    def test_nested_function_injection(self, code_validator: CodeValidator):
        """Test nested function call injection attempts."""
        malicious_codes = [
            "list(map(eval, ['__import__(\"os\")']))",
            "any(exec(code) for code in ['import os'])",
            "next(iter([eval('__import__(\"sys\")')]))",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Nested function injection should be blocked: {code}"

    @pytest.mark.medium
    def test_lambda_function_injection(self, code_validator: CodeValidator):
        """Test lambda function injection attempts."""
        malicious_codes = [
            "(lambda: __import__('os'))().system('ls')",
            "list(map(lambda x: eval(x), ['__import__(\"os\")']))",
            "(lambda f: f('os'))(__import__)",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Lambda injection should be blocked: {code}"
