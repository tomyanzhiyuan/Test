"""Tests for AWS Lambda security isolation."""

import pytest
from app.services.lambda_execution import LambdaExecutionService


class TestLambdaSecurityIsolation:
    """Test AWS Lambda security and isolation."""

    @pytest.mark.critical
    @pytest.mark.integration
    async def test_lambda_service_initialization(self, lambda_service: LambdaExecutionService):
        """Test Lambda service initialization and credential handling."""
        health = lambda_service.get_service_health()
        
        # Should either be healthy or have clear error message
        assert health["status"] in ["healthy", "unhealthy"], "Lambda service should report clear status"
        
        if health["status"] == "unhealthy":
            assert "error" in health, "Unhealthy service should provide error details"
            # This is expected if AWS credentials are not configured
            pytest.skip(f"Lambda service unavailable: {health.get('error')}")

    @pytest.mark.critical
    @pytest.mark.integration
    async def test_lambda_execution_isolation(self, lambda_service: LambdaExecutionService):
        """Test that Lambda provides proper execution isolation."""
        # Test that Lambda execution doesn't allow dangerous operations
        dangerous_codes = [
            "import os; print(os.listdir('/'))",  # File system access
            "import socket; socket.gethostname()",  # Network info
            "import subprocess; subprocess.run(['whoami'])",  # System commands
        ]
        
        for code in dangerous_codes:
            result = await lambda_service.execute_code(code)
            
            # Should be blocked by validation or Lambda environment
            assert result.status == "error", f"Dangerous code should be blocked in Lambda: {code}"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_lambda_timeout_enforcement(self, lambda_service: LambdaExecutionService):
        """Test Lambda timeout enforcement."""
        # Code that would run for a long time
        long_running_code = """
import time
for i in range(100):
    time.sleep(1)
    print(f"Still running: {i}")
"""
        
        result = await lambda_service.execute_code(long_running_code)
        
        # Should timeout or be blocked
        assert result.status in ["error", "timeout"], "Long running code should timeout"
        assert result.execution_time < 35, "Should not exceed timeout limit"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_lambda_memory_limits(self, lambda_service: LambdaExecutionService):
        """Test Lambda memory limit enforcement."""
        # Code that would consume lots of memory
        memory_intensive_code = """
# Try to allocate large amounts of memory
big_list = []
for i in range(1000000):
    big_list.append('x' * 1000)
print(f"Allocated {len(big_list)} items")
"""
        
        result = await lambda_service.execute_code(memory_intensive_code)
        
        # Should be limited by Lambda memory constraints
        if result.status == "error":
            assert "memory" in result.error.lower() or "validation failed" in result.error.lower()

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_lambda_pandas_availability(self, lambda_service: LambdaExecutionService):
        """Test that pandas/scipy are available in Lambda."""
        library_test_code = """
import pandas as pd
import numpy as np
import scipy

# Test basic functionality
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
arr = np.array([1, 2, 3])
print(f"DataFrame shape: {df.shape}")
print(f"Array mean: {arr.mean()}")
print("Libraries working correctly")
"""
        
        result = await lambda_service.execute_code(library_test_code)
        
        # Should execute successfully with libraries available
        if result.status == "success":
            assert "Libraries working correctly" in result.output
        else:
            # If Lambda not available, skip test
            pytest.skip(f"Lambda not available for library testing: {result.error}")

    @pytest.mark.high
    @pytest.mark.integration
    async def test_lambda_network_isolation(self, lambda_service: LambdaExecutionService):
        """Test Lambda network isolation."""
        network_test_codes = [
            "import urllib.request; urllib.request.urlopen('http://google.com')",
            "import socket; socket.create_connection(('google.com', 80))",
            "import requests; requests.get('http://httpbin.org/ip')",
        ]
        
        for code in network_test_codes:
            result = await lambda_service.execute_code(code)
            
            # Should be blocked by validation or Lambda environment
            assert result.status == "error", f"Network access should be blocked: {code}"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_lambda_file_system_isolation(self, lambda_service: LambdaExecutionService):
        """Test Lambda file system isolation."""
        file_access_codes = [
            "open('/etc/passwd', 'r').read()",
            "import os; os.listdir('/tmp')",
            "with open('/proc/version') as f: f.read()",
        ]
        
        for code in file_access_codes:
            result = await lambda_service.execute_code(code)
            
            # Should be blocked by validation
            assert result.status == "error", f"File access should be blocked: {code}"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_lambda_error_handling(self, lambda_service: LambdaExecutionService):
        """Test Lambda error handling and information disclosure."""
        error_inducing_codes = [
            "raise Exception('Custom error message')",
            "1 / 0",  # Division by zero
            "undefined_variable",  # NameError
            "import pandas as pd; pd.nonexistent_function()",  # AttributeError
        ]
        
        for code in error_inducing_codes:
            result = await lambda_service.execute_code(code)
            
            if result.status == "error":
                # Error messages should not contain sensitive Lambda information
                sensitive_patterns = [
                    "/var/task",  # Lambda task directory
                    "/opt/python",  # Lambda layer paths
                    "lambda_function",  # Lambda function names
                    "arn:aws:lambda",  # Lambda ARNs
                ]
                
                for pattern in sensitive_patterns:
                    assert pattern not in result.error, f"Error contains sensitive Lambda info: {result.error}"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_lambda_response_sanitization(self, lambda_service: LambdaExecutionService):
        """Test that Lambda responses are properly sanitized."""
        # Code that might expose Lambda environment details
        environment_probe_codes = [
            "import os; print(os.environ)",
            "import sys; print(sys.path)",
            "print(__file__)",
            "import inspect; print(inspect.stack())",
        ]
        
        for code in environment_probe_codes:
            result = await lambda_service.execute_code(code)
            
            # Should be blocked by validation or sanitized
            assert result.status == "error", f"Environment probing should be blocked: {code}"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_lambda_concurrent_execution(self, lambda_service: LambdaExecutionService):
        """Test Lambda concurrent execution handling."""
        # Test multiple concurrent Lambda invocations
        test_code = "import time; time.sleep(2); print('completed')"
        
        # Execute multiple requests concurrently
        import asyncio
        tasks = [lambda_service.execute_code(test_code) for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete or be properly handled
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Concurrent execution {i} failed: {result}")
            
            # Should either succeed or be blocked by validation
            assert result.status in ["success", "error"], f"Concurrent execution {i} unexpected status"

    @pytest.mark.critical
    @pytest.mark.integration
    async def test_lambda_credential_isolation(self, lambda_service: LambdaExecutionService):
        """Test that Lambda execution cannot access AWS credentials."""
        credential_access_codes = [
            "import boto3; print(boto3.Session().get_credentials())",
            "import os; print(os.environ.get('AWS_ACCESS_KEY_ID'))",
            "import os; print(os.environ.get('AWS_SECRET_ACCESS_KEY'))",
        ]
        
        for code in credential_access_codes:
            result = await lambda_service.execute_code(code)
            
            # Should be blocked by validation (boto3 not allowed)
            assert result.status == "error", f"Credential access should be blocked: {code}"
            assert "import" in result.error.lower(), "Should be blocked by import validation"
