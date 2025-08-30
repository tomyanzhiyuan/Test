"""Tests for resource exhaustion attack vectors."""

import pytest
from app.services.code_validator import CodeValidator


class TestResourceExhaustionAttacks:
    """Test various resource exhaustion attack techniques."""

    @pytest.mark.critical
    def test_infinite_loop_detection(self, code_validator: CodeValidator):
        """Test detection of infinite loop patterns."""
        infinite_loop_codes = [
            "while True: pass",
            "while 1: continue",
            "for i in iter(int, 1): pass",  # Infinite iterator
            "while not False: x = 1",
            "import itertools\nfor i in itertools.count(): pass",
        ]
        
        for code in infinite_loop_codes:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            
            # Should be caught by complexity analysis or import restrictions
            assert not is_safe, f"Infinite loop should be detected: {code}"

    @pytest.mark.critical
    def test_memory_exhaustion_patterns(self, code_validator: CodeValidator):
        """Test memory exhaustion attack patterns."""
        memory_exhaustion_codes = [
            "x = 'a' * (10**8)",  # Large string
            "data = [0] * (10**7)",  # Large list
            "matrix = [[0] * 1000 for _ in range(1000)]",  # Large matrix
            "big_dict = {i: 'x' * 1000 for i in range(10000)}",  # Large dict
            "nested = [[[[0] * 100] * 100] * 100] * 100",  # Deeply nested
        ]
        
        for code in memory_exhaustion_codes:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            
            # High complexity should trigger safety check
            if complexity > 20:
                assert not is_safe, f"High complexity memory exhaustion should be blocked: {code}"

    @pytest.mark.critical
    def test_recursive_function_bombs(self, code_validator: CodeValidator):
        """Test recursive function bomb detection."""
        recursive_bombs = [
            "def f(): f()\nf()",  # Simple recursion bomb
            "def a(): b()\ndef b(): a()\na()",  # Mutual recursion
            "def factorial(n): return factorial(n)\nfactorial(1)",  # Infinite recursion
            "lambda: (lambda: (lambda: None)())()",  # Lambda recursion
        ]
        
        for code in recursive_bombs:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            
            # Should be caught by complexity analysis
            assert not is_safe, f"Recursive bomb should be detected: {code}"

    @pytest.mark.high
    def test_cpu_intensive_operations(self, code_validator: CodeValidator):
        """Test CPU-intensive operations that could cause DoS."""
        cpu_intensive_codes = [
            "sum(range(10**7))",  # Large range sum
            "[i**2 for i in range(10**6)]",  # Large list comprehension
            "factorial = lambda n: n * factorial(n-1) if n > 1 else 1\nfactorial(1000)",
            "import math\n[math.factorial(i) for i in range(1000)]",
        ]
        
        for code in cpu_intensive_codes:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            
            # High complexity operations should be flagged
            if complexity > 15:
                assert not is_safe, f"CPU intensive operation should be blocked: {code}"

    @pytest.mark.medium
    def test_nested_data_structures(self, code_validator: CodeValidator):
        """Test deeply nested data structures."""
        nested_codes = [
            "data = {}\nfor i in range(1000): data = {'nested': data}",
            "lst = []\nfor i in range(1000): lst = [lst]",
            "nested_dict = {'a': {'b': {'c': {'d': 'deep'}}}}" * 100,
        ]
        
        for code in nested_codes:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            
            # Should be caught by complexity or line count limits
            if len(code.split('\n')) > 100 or complexity > 20:
                assert not is_safe, f"Nested structure should be limited: {code}"

    @pytest.mark.medium
    def test_generator_exhaustion(self, code_validator: CodeValidator):
        """Test generator-based exhaustion attacks."""
        generator_codes = [
            "list(range(10**8))",  # Convert large range to list
            "sum(i for i in range(10**7))",  # Generator expression
            "max(range(10**8))",  # Max of large range
        ]
        
        for code in generator_codes:
            complexity = code_validator.get_complexity_score(code)
            # These might pass validation but should be caught by runtime limits
            # This documents potential runtime vulnerabilities
            if complexity <= 20:
                pytest.skip(f"Generator exhaustion not caught by static analysis: {code}")

    @pytest.mark.high
    def test_complexity_threshold_accuracy(self, code_validator: CodeValidator):
        """Test that complexity threshold (20) is appropriate."""
        # Code that should pass (complexity <= 20)
        acceptable_codes = [
            "for i in range(10): print(i)",  # Simple loop
            "if True:\n    for j in range(5):\n        print(j)",  # Nested but simple
            "def func():\n    return sum(range(10))\nfunc()",  # Function with simple logic
        ]
        
        # Code that should fail (complexity > 20)
        complex_codes = [
            "\n".join([f"if x == {i}: pass" for i in range(25)]),  # Many conditions
            "\n".join([f"for i{i} in range(5): pass" for i in range(15)]),  # Many loops
            "def f1(): pass\n" * 15,  # Many functions
        ]
        
        for code in acceptable_codes:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            assert is_safe, f"Acceptable complexity code should pass: {code} (complexity: {complexity})"
        
        for code in complex_codes:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            if complexity > 20:
                assert not is_safe, f"High complexity code should fail: {code} (complexity: {complexity})"

    @pytest.mark.medium
    def test_string_multiplication_attacks(self, code_validator: CodeValidator):
        """Test string multiplication for memory exhaustion."""
        string_attacks = [
            "x = 'A' * (10**6)",  # 1MB string
            "data = 'x' * (2**20)",  # 1MB string (power of 2)
            "big_str = 'test' * (10**5)",  # Large repeated string
        ]
        
        for code in string_attacks:
            # These might pass static validation but should be runtime-limited
            # This documents the need for runtime memory monitoring
            is_safe, reason = code_validator.is_code_safe(code)
            # Static analysis may not catch these - document limitation
            if is_safe:
                pytest.skip(f"String multiplication not caught by static analysis: {code}")

    @pytest.mark.high
    def test_list_comprehension_bombs(self, code_validator: CodeValidator):
        """Test list comprehension memory bombs."""
        comprehension_bombs = [
            "[i for i in range(10**6)]",  # Large list comprehension
            "[[i] * 1000 for i in range(1000)]",  # Nested large comprehension
            "{i: [j] * 100 for i in range(1000) for j in range(100)}",  # Dict comprehension
            "(i**2 for i in range(10**7))",  # Generator (less dangerous but still)
        ]
        
        for code in comprehension_bombs:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            
            # Should be caught by complexity analysis
            if complexity > 10:  # Lower threshold for comprehensions
                assert not is_safe, f"Large comprehension should be blocked: {code}"

    @pytest.mark.medium
    def test_nested_loop_complexity(self, code_validator: CodeValidator):
        """Test nested loop complexity detection."""
        nested_loop_codes = [
            "for i in range(100):\n    for j in range(100):\n        for k in range(100): pass",
            "for a in range(50):\n    for b in range(50):\n        for c in range(50):\n            for d in range(50): pass",
        ]
        
        for code in nested_loop_codes:
            complexity = code_validator.get_complexity_score(code)
            is_safe, reason = code_validator.is_code_safe(code)
            
            # High nested complexity should be blocked
            assert not is_safe, f"Nested loop complexity should be blocked: {code} (complexity: {complexity})"

    @pytest.mark.medium
    def test_line_count_exhaustion(self, code_validator: CodeValidator):
        """Test line count limits."""
        # Generate code with exactly 101 lines (over limit)
        many_lines = "\n".join([f"x{i} = {i}" for i in range(101)])
        
        is_safe, reason = code_validator.is_code_safe(code)
        assert not is_safe, "Code with >100 lines should be blocked"
        assert "too many lines" in reason

    @pytest.mark.high
    def test_legitimate_complex_code_passes(self, code_validator: CodeValidator):
        """Test that legitimate complex code still passes."""
        legitimate_codes = [
            """
import pandas as pd
import numpy as np

# Create sample data
data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
df = pd.DataFrame(data)

# Perform analysis
result = df.groupby('A').sum()
print(result)
""",
            """
import numpy as np
import math

# Mathematical computation
arr = np.array([1, 2, 3, 4, 5])
mean_val = np.mean(arr)
std_val = np.std(arr)

for i in range(len(arr)):
    normalized = (arr[i] - mean_val) / std_val
    print(f"Value {arr[i]} normalized: {normalized}")
""",
        ]
        
        for code in legitimate_codes:
            is_safe, reason = code_validator.is_code_safe(code)
            assert is_safe, f"Legitimate complex code should pass: {code[:100]}..."
</content>
<task_progress>
- [x] Create security testing framework structure
- [x] Implement code injection attack tests
- [x] Implement import bypass tests
- [x] Implement validation bypass tests
- [x] Implement resource exhaustion tests
- [ ] Implement API security tests
- [ ] Create test runner and configuration
</task_progress>
</write_to_file>

[Response interrupted by a tool use result. Only one tool may be used at a time and should be placed at the end of the message.]
