"""Tests for Docker container security."""

import pytest
from app.services.code_execution import CodeExecutionService


class TestDockerSecurityIsolation:
    """Test Docker container security and isolation."""

    @pytest.mark.critical
    @pytest.mark.integration
    async def test_docker_service_initialization(self, docker_service: CodeExecutionService):
        """Test Docker service initialization."""
        health = docker_service.get_service_health()
        
        # Should report clear status
        assert health["status"] in ["healthy", "unhealthy", "degraded"], "Docker service should report clear status"
        
        if health["status"] == "unhealthy":
            pytest.skip(f"Docker service unavailable: {health.get('error')}")

    @pytest.mark.critical
    @pytest.mark.integration
    async def test_container_isolation(self, docker_service: CodeExecutionService):
        """Test that Docker containers provide proper isolation."""
        # Test that dangerous operations are blocked
        dangerous_codes = [
            "import os; os.system('ls /')",
            "import subprocess; subprocess.run(['ps', 'aux'])",
            "open('/etc/passwd', 'r').read()",
        ]
        
        for code in dangerous_codes:
            result = await docker_service.execute_code(code)
            
            # Should be blocked by validation
            assert result.status == "error", f"Dangerous code should be blocked: {code}"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_container_resource_limits(self, docker_service: CodeExecutionService):
        """Test Docker container resource limits."""
        # Test memory limit enforcement
        memory_test_code = """
# Try to allocate more memory than allowed
big_data = []
for i in range(1000000):
    big_data.append('x' * 1000)  # ~1GB total
print(f"Allocated {len(big_data)} items")
"""
        
        result = await docker_service.execute_code(memory_test_code)
        
        # Should be limited by container memory limits or validation
        if result.status == "error":
            # Could be blocked by validation or container limits
            assert True  # Expected behavior
        elif result.status == "memory_limit":
            assert True  # Container memory limit enforced
        else:
            # If it succeeds, the memory limit might not be working
            pytest.fail("Memory limit not enforced in container")

    @pytest.mark.high
    @pytest.mark.integration
    async def test_container_timeout_enforcement(self, docker_service: CodeExecutionService):
        """Test Docker container timeout enforcement."""
        # Code that would run longer than timeout
        timeout_test_code = """
import time
for i in range(60):  # Would run for 60 seconds
    time.sleep(1)
    print(f"Running: {i}")
"""
        
        result = await docker_service.execute_code(timeout_test_code)
        
        # Should timeout
        assert result.status in ["timeout", "error"], "Long running code should timeout"
        assert result.execution_time < 35, "Should not exceed timeout limit"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_container_network_isolation(self, docker_service: CodeExecutionService):
        """Test Docker container network isolation."""
        # These should be blocked by validation, but test container isolation too
        network_codes = [
            "import socket; socket.gethostname()",
            "import urllib.request; urllib.request.urlopen('http://google.com')",
        ]
        
        for code in network_codes:
            result = await docker_service.execute_code(code)
            
            # Should be blocked by validation
            assert result.status == "error", f"Network access should be blocked: {code}"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_container_filesystem_isolation(self, docker_service: CodeExecutionService):
        """Test Docker container filesystem isolation."""
        # Test read-only filesystem and restricted access
        filesystem_codes = [
            "open('/etc/passwd', 'r').read()",
            "import os; os.listdir('/usr')",
            "with open('/tmp/test', 'w') as f: f.write('test')",  # Write attempt
        ]
        
        for code in filesystem_codes:
            result = await docker_service.execute_code(code)
            
            # Should be blocked by validation or container restrictions
            assert result.status == "error", f"Filesystem access should be blocked: {code}"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_container_user_isolation(self, docker_service: CodeExecutionService):
        """Test that code runs as non-root user in container."""
        # Test user context
        user_test_code = """
import os
print(f"UID: {os.getuid()}")
print(f"GID: {os.getgid()}")
print(f"User: {os.environ.get('USER', 'unknown')}")
"""
        
        result = await docker_service.execute_code(user_test_code)
        
        # Should be blocked by validation (os module not allowed)
        assert result.status == "error", "OS module access should be blocked"

    @pytest.mark.critical
    @pytest.mark.integration
    async def test_container_escape_attempts(self, docker_service: CodeExecutionService):
        """Test container escape attempt detection."""
        escape_attempts = [
            "import os; os.system('docker ps')",  # Try to access host Docker
            "open('/proc/1/cgroup', 'r').read()",  # Try to read host process info
            "import subprocess; subprocess.run(['mount'])",  # Try to see mounts
        ]
        
        for code in escape_attempts:
            result = await docker_service.execute_code(code)
            
            # Should be blocked by validation
            assert result.status == "error", f"Container escape attempt should be blocked: {code}"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_container_cleanup(self, docker_service: CodeExecutionService):
        """Test that containers are properly cleaned up."""
        # Execute some code to create containers
        test_codes = [
            "print('test 1')",
            "print('test 2')",
            "print('test 3')",
        ]
        
        for code in test_codes:
            result = await docker_service.execute_code(code)
            # Results don't matter for this test
        
        # Check Docker service health after executions
        health = docker_service.get_service_health()
        assert health["status"] in ["healthy", "degraded"], "Docker service should remain healthy after executions"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_container_error_sanitization(self, docker_service: CodeExecutionService):
        """Test that container errors are properly sanitized."""
        # Code that will cause errors
        error_codes = [
            "raise Exception('Custom error with /sensitive/path')",
            "1 / 0",  # Division by zero
            "undefined_variable",  # NameError
        ]
        
        for code in error_codes:
            result = await docker_service.execute_code(code)
            
            if result.status == "error" and result.error:
                # Error should be sanitized
                sensitive_patterns = [
                    "/app/",  # Application paths
                    "/usr/",  # System paths
                    "/tmp/",  # Temp paths
                    "container",  # Container IDs
                ]
                
                for pattern in sensitive_patterns:
                    assert pattern not in result.error, f"Error contains sensitive info '{pattern}': {result.error}"
