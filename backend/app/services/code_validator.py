"""Code validation service for security analysis."""

import ast
import re
from typing import List, Set, Tuple

from app.core.config import settings


class CodeValidator:
    """Service for validating and analyzing Python code for security risks."""

    # Dangerous modules that should be blocked
    DANGEROUS_MODULES = {
        "os", "sys", "subprocess", "socket", "urllib", "requests",
        "http", "ftplib", "smtplib", "telnetlib", "xmlrpc",
        "pickle", "marshal", "shelve", "dbm", "sqlite3",
        "ctypes", "multiprocessing", "threading", "asyncio",
        "importlib", "pkgutil", "runpy", "code", "codeop",
        "compile", "eval", "exec", "globals", "locals", "vars",
        "__import__", "open", "file", "input", "raw_input",
        "reload", "execfile", "apply", "buffer", "intern"
    }

    # Dangerous built-in functions
    DANGEROUS_BUILTINS = {
        "eval", "exec", "compile", "__import__", "open", "file",
        "input", "raw_input", "reload", "execfile", "apply",
        "buffer", "intern", "globals", "locals", "vars"
    }

    # Dangerous attributes and methods
    DANGEROUS_ATTRIBUTES = {
        "__class__", "__bases__", "__subclasses__", "__mro__",
        "__globals__", "__code__", "__func__", "__self__",
        "__dict__", "__getattribute__", "__setattr__", "__delattr__"
    }

    # Allowed modules for data science
    ALLOWED_MODULES = {
        "pandas", "numpy", "scipy", "math", "statistics",
        "random", "datetime", "json", "csv", "re",
        "collections", "itertools", "functools", "operator"
    }

    def __init__(self) -> None:
        """Initialize the code validator."""
        pass

    def validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate Python code for security risks.
        
        Returns:
            Tuple of (is_safe, list_of_violations)
        """
        violations = []

        # Check code length
        if len(code) > settings.MAX_CODE_LENGTH:
            violations.append(f"Code exceeds maximum length of {settings.MAX_CODE_LENGTH} characters")

        # Check for dangerous patterns
        violations.extend(self._check_dangerous_patterns(code))

        # Parse and analyze AST
        try:
            tree = ast.parse(code)
            violations.extend(self._analyze_ast(tree))
        except SyntaxError as e:
            violations.append(f"Syntax error: {str(e)}")

        return len(violations) == 0, violations

    def _check_dangerous_patterns(self, code: str) -> List[str]:
        """Check for dangerous patterns in code using regex."""
        violations = []

        # Check for dangerous function calls
        dangerous_patterns = [
            (r'\b(eval|exec)\s*\(', "Use of eval() or exec() is not allowed"),
            (r'\b__import__\s*\(', "Use of __import__() is not allowed"),
            (r'\bopen\s*\(', "File operations are not allowed"),
            (r'\binput\s*\(', "Input operations are not allowed"),
            (r'\bprint\s*\(\s*open\s*\(', "File reading through print is not allowed"),
            (r'subprocess\.|os\.|sys\.', "System module access is not allowed"),
            (r'socket\.|urllib\.|requests\.', "Network operations are not allowed"),
            (r'pickle\.|marshal\.|shelve\.', "Serialization modules are not allowed"),
            (r'ctypes\.|multiprocessing\.', "Low-level system access is not allowed"),
            (r'__.*__\s*=', "Dunder attribute modification is not allowed"),
            (r'globals\(\)|locals\(\)', "Access to global/local scope is not allowed"),
        ]

        for pattern, message in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(message)

        return violations

    def _analyze_ast(self, tree: ast.AST) -> List[str]:
        """Analyze AST for dangerous constructs."""
        violations = []

        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.DANGEROUS_MODULES:
                        violations.append(f"Import of dangerous module '{alias.name}' is not allowed")
                    elif alias.name not in self.ALLOWED_MODULES:
                        violations.append(f"Import of module '{alias.name}' is not allowed")

            elif isinstance(node, ast.ImportFrom):
                if node.module in self.DANGEROUS_MODULES:
                    violations.append(f"Import from dangerous module '{node.module}' is not allowed")
                elif node.module and node.module not in self.ALLOWED_MODULES:
                    violations.append(f"Import from module '{node.module}' is not allowed")

            # Check function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_BUILTINS:
                        violations.append(f"Use of dangerous function '{node.func.id}' is not allowed")

            # Check attribute access
            elif isinstance(node, ast.Attribute):
                if node.attr in self.DANGEROUS_ATTRIBUTES:
                    violations.append(f"Access to dangerous attribute '{node.attr}' is not allowed")

            # Check for dangerous assignments
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.startswith('__'):
                        violations.append("Assignment to dunder variables is not allowed")

        return violations

    def sanitize_code(self, code: str) -> str:
        """Sanitize code by removing comments and normalizing whitespace."""
        # Remove comments but preserve string literals
        lines = []
        for line in code.split('\n'):
            # Simple comment removal (doesn't handle strings with # properly)
            if '#' in line and not ('"' in line or "'" in line):
                line = line[:line.index('#')]
            lines.append(line.rstrip())
        
        return '\n'.join(lines).strip()

    def get_complexity_score(self, code: str) -> int:
        """Calculate code complexity score."""
        try:
            tree = ast.parse(code)
            complexity = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    complexity += 1
                elif isinstance(node, ast.If):
                    complexity += 1
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity += 2
                elif isinstance(node, ast.ClassDef):
                    complexity += 3
                    
            return complexity
        except SyntaxError:
            return 100  # High complexity for invalid syntax

    def is_code_safe(self, code: str) -> Tuple[bool, str]:
        """
        Comprehensive safety check for code.
        
        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        # Basic validation
        is_valid, violations = self.validate_code(code)
        if not is_valid:
            return False, "; ".join(violations)

        # Complexity check
        complexity = self.get_complexity_score(code)
        if complexity > 20:
            return False, "Code complexity too high (potential infinite loops or resource exhaustion)"

        # Length check
        if len(code.split('\n')) > 100:
            return False, "Code has too many lines (maximum 100 lines allowed)"

        return True, ""
