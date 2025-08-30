"""Comprehensive penetration testing for production readiness."""

import pytest
import asyncio
import time
from typing import List, Dict, Any
import httpx


class TestPenetrationTesting:
    """Comprehensive penetration testing suite."""

    @pytest.mark.critical
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_comprehensive_attack_simulation(self, api_client: httpx.AsyncClient):
        """Simulate a comprehensive attack against the platform."""
        print("\n🎯 COMPREHENSIVE ATTACK SIMULATION")
        print("=" * 50)
        
        attack_vectors = {
            "Code Injection": [
                "eval('__import__(\"os\").system(\"ls\")')",
                "exec('import subprocess; subprocess.run([\"whoami\"])')",
                "getattr(__builtins__, 'eval')('malicious_code')",
            ],
            "Import Bypass": [
                "__import__('os').system('ls')",
                "getattr(__builtins__, '__import__')('sys')",
                "import importlib; importlib.import_module('os')",
            ],
            "Comment Bypass": [
                'import os; x = "safe" # os.system("rm -rf /")',
                'print("hello") # import subprocess',
            ],
            "Resource Exhaustion": [
                "while True: pass",
                "x = 'a' * (10**8)",
                "[i for i in range(10**7)]",
            ],
            "Encoding Attacks": [
                "exec('\\x69\\x6d\\x70\\x6f\\x72\\x74\\x20\\x6f\\x73')",
                "eval(chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116))",
            ]
        }
        
        total_attacks = 0
        blocked_attacks = 0
        successful_attacks = []
        
        for category, attacks in attack_vectors.items():
            print(f"\n🔍 Testing {category}:")
            
            for attack in attacks:
                total_attacks += 1
                
                try:
                    response = await api_client.post(
                        "/api/v1/code/execute",
                        json={"code": attack},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "error":
                            blocked_attacks += 1
                            print(f"   ✅ Blocked: {attack[:50]}...")
                        else:
                            successful_attacks.append({
                                "category": category,
                                "attack": attack,
                                "response": data
                            })
                            print(f"   ❌ SUCCESS: {attack[:50]}...")
                    else:
                        blocked_attacks += 1
                        print(f"   ✅ Rejected: {attack[:50]}...")
                        
                except Exception as e:
                    blocked_attacks += 1
                    print(f"   ✅ Failed: {attack[:50]}... ({e})")
        
        # Generate attack simulation report
        print(f"\n📊 ATTACK SIMULATION RESULTS:")
        print(f"   Total Attacks: {total_attacks}")
        print(f"   Blocked: {blocked_attacks}")
        print(f"   Successful: {len(successful_attacks)}")
        print(f"   Block Rate: {(blocked_attacks/total_attacks)*100:.1f}%")
        
        if successful_attacks:
            print(f"\n🚨 SUCCESSFUL ATTACKS:")
            for attack in successful_attacks:
                print(f"   ❌ {attack['category']}: {attack['attack'][:50]}...")
        
        # Test should pass only if all attacks are blocked
        assert len(successful_attacks) == 0, f"Security vulnerabilities found: {len(successful_attacks)} attacks succeeded"

    @pytest.mark.high
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_rate_limit_stress_test(self, api_client: httpx.AsyncClient):
        """Stress test the rate limiting mechanism."""
        print("\n🔥 RATE LIMIT STRESS TEST")
        
        # Send burst of requests
        payload = {"code": "print('stress test')"}
        responses = []
        
        # Send 50 requests as fast as possible
        tasks = []
        for i in range(50):
            task = api_client.post("/api/v1/code/execute", json=payload)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Analyze responses
        status_codes = []
        for result in results:
            if isinstance(result, Exception):
                status_codes.append("Exception")
            else:
                status_codes.append(result.status_code)
        
        rate_limited = sum(1 for code in status_codes if code == 429)
        successful = sum(1 for code in status_codes if code == 200)
        
        print(f"   Duration: {end_time - start_time:.2f}s")
        print(f"   Successful: {successful}")
        print(f"   Rate Limited: {rate_limited}")
        print(f"   Errors: {sum(1 for code in status_codes if isinstance(code, str) and 'Exception' in code)}")
        
        # Should have significant rate limiting
        assert rate_limited > 0, "Rate limiting should be enforced under stress"
        assert rate_limited > successful * 0.5, "Rate limiting should be aggressive under stress"

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_payload_fuzzing(self, api_client: httpx.AsyncClient):
        """Fuzz test API payloads."""
        print("\n🎲 PAYLOAD FUZZING TEST")
        
        # Generate various malformed payloads
        fuzz_payloads = [
            {"code": None},
            {"code": 123},
            {"code": []},
            {"code": {}},
            {"code": "\x00\x01\x02\x03"},  # Binary data
            {"code": "A" * 100000},  # Very large payload
            {"invalid": "test"},
            {},
            {"code": "print('test')", "extra": "field"},
        ]
        
        vulnerable_responses = []
        
        for payload in fuzz_payloads:
            try:
                response = await api_client.post("/api/v1/code/execute", json=payload)
                
                # Should handle gracefully
                if response.status_code not in [400, 422, 413]:
                    vulnerable_responses.append({
                        "payload": payload,
                        "status": response.status_code,
                        "response": response.text[:200]
                    })
                    
            except Exception as e:
                # Exceptions are acceptable for malformed data
                pass
        
        if vulnerable_responses:
            print(f"   ⚠️ Unexpected responses: {len(vulnerable_responses)}")
            for resp in vulnerable_responses:
                print(f"      {resp['payload']} -> {resp['status']}")
        
        # Should handle all fuzz inputs gracefully
        assert len(vulnerable_responses) == 0, f"Fuzzing found {len(vulnerable_responses)} unexpected responses"

    @pytest.mark.high
    @pytest.mark.integration
    async def test_timing_attack_resistance(self, api_client: httpx.AsyncClient):
        """Test resistance to timing attacks."""
        print("\n⏱️ TIMING ATTACK RESISTANCE TEST")
        
        # Test if validation timing reveals information
        test_cases = [
            {"code": "print('safe')"},  # Safe code
            {"code": "import os"},  # Blocked import
            {"code": "eval('test')"},  # Blocked function
            {"code": "x" * 10000},  # Long code
        ]
        
        timings = []
        
        for test_case in test_cases:
            times = []
            
            # Measure multiple times for accuracy
            for _ in range(5):
                start = time.time()
                await api_client.post("/api/v1/code/execute", json=test_case)
                end = time.time()
                times.append(end - start)
            
            avg_time = sum(times) / len(times)
            timings.append(avg_time)
        
        # Check for significant timing differences
        max_time = max(timings)
        min_time = min(timings)
        time_variance = max_time - min_time
        
        print(f"   Timing variance: {time_variance:.3f}s")
        print(f"   Max time: {max_time:.3f}s")
        print(f"   Min time: {min_time:.3f}s")
        
        # Large timing differences could indicate information leakage
        if time_variance > 1.0:  # More than 1 second difference
            pytest.fail(f"Significant timing variance detected: {time_variance:.3f}s")

    @pytest.mark.critical
    @pytest.mark.integration
    async def test_end_to_end_security_workflow(self, api_client: httpx.AsyncClient):
        """Test complete security workflow from frontend to backend."""
        print("\n🔄 END-TO-END SECURITY WORKFLOW TEST")
        
        # Simulate complete user workflow with malicious intent
        workflow_steps = [
            # Step 1: Try to execute malicious code
            {
                "step": "Execute malicious code",
                "endpoint": "/api/v1/code/execute",
                "payload": {"code": "import os; os.system('whoami')"}
            },
            # Step 2: Try to submit malicious code
            {
                "step": "Submit malicious code",
                "endpoint": "/api/v1/code/submit",
                "payload": {"code": "__import__('sys').exit()"}
            },
            # Step 3: Try payload injection
            {
                "step": "Payload injection",
                "endpoint": "/api/v1/code/execute",
                "payload": {"code": "eval(input())"}
            },
        ]
        
        for step_info in workflow_steps:
            print(f"   Testing: {step_info['step']}")
            
            response = await api_client.post(
                step_info['endpoint'],
                json=step_info['payload']
            )
            
            # All malicious attempts should be blocked
            if response.status_code == 200:
                data = response.json()
                assert data.get("status") == "error", f"Step '{step_info['step']}' should be blocked"
            else:
                assert response.status_code in [400, 422], f"Step '{step_info['step']}' should return error status"
        
        print("   ✅ All malicious workflow steps blocked")

    @pytest.mark.medium
    @pytest.mark.integration
    async def test_error_message_consistency(self, api_client: httpx.AsyncClient):
        """Test that error messages don't leak information."""
        print("\n🔍 ERROR MESSAGE CONSISTENCY TEST")
        
        # Different types of malicious code should return similar error patterns
        malicious_codes = [
            "import os",
            "import sys", 
            "import subprocess",
            "eval('test')",
            "exec('test')",
            "__import__('os')",
        ]
        
        error_messages = []
        
        for code in malicious_codes:
            response = await api_client.post(
                "/api/v1/code/execute",
                json={"code": code}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "error":
                    error_messages.append(data.get("error", ""))
        
        # Error messages should be consistent and not reveal internal details
        for msg in error_messages:
            # Should not contain file paths, internal module names, etc.
            sensitive_info = ["/app/", "/usr/", "docker", "lambda", "container"]
            for info in sensitive_info:
                assert info.lower() not in msg.lower(), f"Error message contains sensitive info: {msg}"
        
        print(f"   ✅ Analyzed {len(error_messages)} error messages")
