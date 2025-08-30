# Security Testing Suite

This directory contains comprehensive security tests for the Code Execution Platform. These tests are designed to identify vulnerabilities and ensure the platform is production-ready.

## Test Categories

1. **Code Injection Tests** - Test various code injection techniques
2. **Import Bypass Tests** - Test sophisticated import bypasses
3. **Resource Exhaustion Tests** - Test memory/CPU exhaustion attacks
4. **Validation Bypass Tests** - Test comment sanitization and AST analysis bypasses
5. **API Security Tests** - Test rate limiting and endpoint security
6. **Lambda Security Tests** - Test AWS Lambda isolation
7. **Docker Security Tests** - Test container escape attempts

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all security tests
python -m pytest security-tests/ -v

# Run specific test category
python -m pytest security-tests/test_code_injection.py -v

# Run with detailed output
python -m pytest security-tests/ -v -s
```

## Test Results

All tests should PASS for production deployment. Any FAILED test indicates a security vulnerability that must be addressed.

## Adding New Tests

When adding new attack vectors or security concerns:

1. Create test in appropriate category file
2. Document the attack vector being tested
3. Ensure test fails when vulnerability exists
4. Verify test passes when vulnerability is fixed
