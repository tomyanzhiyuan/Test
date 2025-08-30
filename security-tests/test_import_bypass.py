"""Tests for import bypass attack vectors."""

import pytest
from app.services.code_validator import CodeValidator


class TestImportBypassAttacks:
    """Test sophisticated import bypass techniques."""

    @pytest.mark.critical
    def test_dangerous_module_imports_blocked(self, code_validator: CodeValidator):
        """Test that dangerous module imports are blocked."""
        dangerous_imports = [
            "import os",
            "import sys",
            "import subprocess",
            "import socket",
            "import urllib",
            "import requests",
            "import pickle",
            "import marshal",
            "import ctypes",
            "import multiprocessing",
            "import threading",
            "import importlib",
        ]
        
        for code in dangerous_imports:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Dangerous import should be blocked: {code}"
            assert any("import" in violation.lower() for violation in violations)

    @pytest.mark.critical
    def test_from_import_bypass_blocked(self, code_validator: CodeValidator):
        """Test that 'from module import' bypasses are blocked."""
        malicious_codes = [
            "from os import system",
            "from subprocess import run",
            "from sys import exit",
            "from socket import socket",
            "from urllib.request import urlopen",
            "from pickle import loads",
            "from ctypes import CDLL",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"From import should be blocked: {code}"

    @pytest.mark.high
    def test_importlib_bypass_blocked(self, code_validator: CodeValidator):
        """Test importlib-based import bypasses."""
        malicious_codes = [
            "import importlib; importlib.import_module('os')",
            "from importlib import import_module; import_module('sys')",
            "importlib.__import__('subprocess')",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"importlib bypass should be blocked: {code}"

    @pytest.mark.high
    def test_dynamic_import_construction(self, code_validator: CodeValidator):
        """Test dynamic import construction techniques."""
        malicious_codes = [
            "__import__('o' + 's')",
            "__import__(''.join(['o', 's']))",
            "__import__(chr(111) + chr(115))",  # 'os'
            "__import__('sys'[::-1][::-1])",  # reverse twice
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Dynamic import construction should be blocked: {code}"

    @pytest.mark.high
    def test_attribute_access_import_bypass(self, code_validator: CodeValidator):
        """Test attribute access to bypass import restrictions."""
        malicious_codes = [
            "print.__class__.__bases__[0].__subclasses__()[104].__init__.__globals__['sys']",
            "[].__class__.__bases__[0].__subclasses__()[59].__init__.__globals__['__builtins__']",
            "().__class__.__bases__[0].__subclasses__()[40].__init__.__globals__['sys']",
            "''.__class__.__mro__[1].__subclasses__()[40]",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Attribute access bypass should be blocked: {code}"

    @pytest.mark.medium
    def test_nested_getattr_bypass(self, code_validator: CodeValidator):
        """Test nested getattr calls to access dangerous modules."""
        malicious_codes = [
            "getattr(getattr(__builtins__, '__import__'), '__call__')('os')",
            "getattr(__builtins__, 'getattr')(__builtins__, '__import__')('sys')",
            "vars(__builtins__)['__import__']('os')",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Nested getattr bypass should be blocked: {code}"

    @pytest.mark.medium
    def test_module_aliasing_bypass(self, code_validator: CodeValidator):
        """Test module aliasing to hide dangerous imports."""
        malicious_codes = [
            "import os as safe_module; safe_module.system('ls')",
            "from os import system as safe_function",
            "import sys as s; s.exit()",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Module aliasing should be blocked: {code}"

    @pytest.mark.medium
    def test_conditional_import_bypass(self, code_validator: CodeValidator):
        """Test conditional imports to bypass detection."""
        malicious_codes = [
            "if True: import os",
            "try:\n    import sys\nexcept: pass",
            "for _ in [1]: import subprocess",
            "with open('/dev/null') as f: import socket",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Conditional import should be blocked: {code}"

    @pytest.mark.high
    def test_allowed_modules_pass_validation(self, code_validator: CodeValidator):
        """Test that allowed modules pass validation."""
        safe_imports = [
            "import pandas",
            "import numpy",
            "import scipy",
            "import math",
            "import statistics",
            "import random",
            "import datetime",
            "import json",
            "import csv",
            "import re",
            "import collections",
            "import itertools",
            "import functools",
            "import operator",
        ]
        
        for code in safe_imports:
            is_safe, violations = code_validator.validate_code(code)
            assert is_safe, f"Safe import should be allowed: {code}"

    @pytest.mark.medium
    def test_mixed_safe_dangerous_imports(self, code_validator: CodeValidator):
        """Test code with both safe and dangerous imports."""
        malicious_codes = [
            "import pandas\nimport os",
            "import numpy\nfrom sys import exit",
            "import math\nimport subprocess",
        ]
        
        for code in malicious_codes:
            is_safe, violations = code_validator.validate_code(code)
            assert not is_safe, f"Mixed imports with dangerous modules should be blocked: {code}"
