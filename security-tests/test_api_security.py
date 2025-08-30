"""Tests for API security vulnerabilities."""

import pytest
import asyncio
import time
from typing import List
import httpx


class TestAPISecurityAttacks:
    """Test API-level security vulnerabilities."""

    @pytest.mark.critical
    @pytest.mark.integration
    async def test_rate_limiting_enforcement(self, api_client: httpx.AsyncClient):
        """Test that rate limiting is properly enforced."""
        # Rate limit is 10/minute according to settings
        endpoint = "/api/v1/code/execute"
        payload = {"code": "print('test')"}
        
        # Send requests rapidly
        responses = []
        start_time = time.time()
        
        for i in range(15):  # Send more than rate limit
            try:
                response = await api_client.post(endpoint, json=payload)
                responses.append(response.status_code)
            except Exception as e:
                responses.append(f"Error: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should get rate limited (429 status codes) after 10 requests
        rate_limited_count = sum(1 for r in responses if r == 429)
        
        if duration < 60:  # If test completed within a minute
            assert rate_limited_count > 0, f"Rate limiting not enforced. Responses: {responses}"
        else:
            pytest.skip("Test took too long, rate limit window may have reset")

    @pytest.mark.high
    @pytest.mark.integration
    async def test_malicious_payload_rejection(self, api_client: httpx.AsyncClient):
        """Test that malicious payloads are rejected by API."""
        malicious_payloads = [
            {"code": "import os; os.system('ls')"},
            {"code": "eval('__import__(\"subprocess\").run([\"whoami\"])')"},
            {"code": "__import__('sys').exit()"},
            {"code": "open('/etc/passwd').read()"},
        ]
        
        for payload in malicious_payloads:
            response = await api_client.post("/api/v1/code/execute", json=payload)
            
            # Should either be blocked (400) or return error in response
            if response.status_code == 200:
                data = response.json()
                assert data.get("status") == "error", f"Malicious code should be rejected: {payload}"
                assert "validation failed" in data.get("error", "").lower()
            else:
                assert response.status_code == 400, f"Malicious code should return 400: {payload}"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_input_validation_edge_cases(self, api_client: httpx.AsyncClient):
        """Test API input validation edge cases."""
        edge_cases = [
            {},  # Empty payload
            {"code": ""},  # Empty code
            {"code": None},  # Null code
            {"invalid_field": "test"},  # Wrong field name
            {"code": "x" * 20000},  # Oversized code
            {"code": "\x00\x01\x02"},  # Binary data
        ]
        
        for payload in edge_cases:
            response = await api_client.post("/api/v1/code/execute", json=payload)
            
            # Should handle gracefully with appropriate error codes
            assert response.status_code in [400, 422], f"Edge case should be handled: {payload}"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_concurrent_request_handling(self, api_client: httpx.AsyncClient):
        """Test handling of concurrent requests."""
        payload = {"code": "import time; time.sleep(1); print('done')"}
        
        # Send multiple concurrent requests
        tasks = []
        for i in range(5):
            task = api_client.post("/api/v1/code/execute", json=payload)
            tasks.append(task)
        
        # Wait for all requests to complete
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete successfully or be rate limited
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                pytest.fail(f"Request {i} failed with exception: {response}")
            assert response.status_code in [200, 429], f"Request {i} unexpected status: {response.status_code}"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_submit_endpoint_security(self, api_client: httpx.AsyncClient):
        """Test submit endpoint specific security."""
        # Test that only successful executions are persisted
        malicious_payload = {"code": "import os; os.system('ls')"}
        
        response = await api_client.post("/api/v1/code/submit", json=malicious_payload)
        
        # Should not persist malicious code
        assert response.status_code == 400, "Malicious code should not be submitted"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_cors_headers(self, api_client: httpx.AsyncClient):
        """Test CORS header configuration."""
        response = await api_client.options("/api/v1/code/execute")
        
        # Should have appropriate CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers, "CORS headers should be present"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_error_information_disclosure(self, api_client: httpx.AsyncClient):
        """Test that errors don't disclose sensitive information."""
        # Send malformed requests to trigger errors
        malformed_requests = [
            {"code": "import os; os.system('ls')"},  # Should trigger validation error
            {"code": "syntax error ("},  # Should trigger syntax error
            {"code": "x" * 50000},  # Should trigger length error
        ]
        
        for payload in malformed_requests:
            response = await api_client.post("/api/v1/code/execute", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                error_msg = data.get("error", "")
            else:
                error_msg = response.text
            
            # Error messages should not contain sensitive information
            sensitive_patterns = [
                "/app/",  # File paths
                "/usr/",  # System paths
                "docker",  # Container info
                "lambda",  # AWS info (in error messages)
                "postgres",  # Database info
            ]
            
            for pattern in sensitive_patterns:
                assert pattern.lower() not in error_msg.lower(), f"Error message contains sensitive info '{pattern}': {error_msg}"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_request_size_limits(self, api_client: httpx.AsyncClient):
        """Test request size limits."""
        # Test very large request
        huge_code = "print('x')\n" * 10000  # Large but valid code
        payload = {"code": huge_code}
        
        response = await api_client.post("/api/v1/code/execute", json=payload)
        
        # Should be rejected due to size limits
        assert response.status_code in [400, 413, 422], "Large request should be rejected"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_timeout_handling(self, api_client: httpx.AsyncClient):
        """Test API timeout handling."""
        # Code that would take a long time (if not blocked)
        slow_code = "import time; time.sleep(60)"  # Would sleep for 60 seconds
        payload = {"code": slow_code}
        
        start_time = time.time()
        response = await api_client.post("/api/v1/code/execute", json=payload)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Should complete quickly due to validation or timeout
        assert duration < 35, f"Request should timeout or be blocked quickly, took {duration}s"
        
        if response.status_code == 200:
            data = response.json()
            # Should be blocked by validation or return timeout status
            assert data.get("status") in ["error", "timeout"], "Slow code should be handled appropriately"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_content_type_validation(self, api_client: httpx.AsyncClient):
        """Test content type validation."""
        # Test with wrong content type
        response = await api_client.post(
            "/api/v1/code/execute",
            data="code=print('test')",  # Form data instead of JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Should reject non-JSON requests
        assert response.status_code in [400, 415, 422], "Non-JSON request should be rejected"
