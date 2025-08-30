"""Pytest configuration and fixtures for security tests."""

import sys
import os
import pytest
import httpx
from typing import AsyncGenerator

# Add backend to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.code_validator import CodeValidator
from app.services.lambda_execution import LambdaExecutionService
from app.services.code_execution import CodeExecutionService


@pytest.fixture
def code_validator() -> CodeValidator:
    """Provide a CodeValidator instance for testing."""
    return CodeValidator()


@pytest.fixture
def lambda_service() -> LambdaExecutionService:
    """Provide a LambdaExecutionService instance for testing."""
    return LambdaExecutionService()


@pytest.fixture
def docker_service() -> CodeExecutionService:
    """Provide a CodeExecutionService instance for testing."""
    return CodeExecutionService()


@pytest.fixture
async def api_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an HTTP client for API testing."""
    async with httpx.AsyncClient(
        base_url="http://localhost:8000",
        timeout=60.0
    ) as client:
        yield client


@pytest.fixture
def malicious_payloads() -> dict:
    """Provide a collection of malicious code payloads for testing."""
    return {
        "system_access": [
            "import os; os.system('ls')",
            "import subprocess; subprocess.run(['ls'])",
            "__import__('os').system('whoami')",
            "getattr(__builtins__, 'eval')('__import__(\"os\").system(\"ls\")')",
        ],
        "file_access": [
            "open('/etc/passwd', 'r').read()",
            "with open('/etc/hosts') as f: print(f.read())",
            "__builtins__['open']('/etc/passwd')",
        ],
        "network_access": [
            "import socket; socket.socket().connect(('google.com', 80))",
            "import urllib.request; urllib.request.urlopen('http://google.com')",
            "import requests; requests.get('http://google.com')",
        ],
        "code_injection": [
            "eval('__import__(\"os\").system(\"ls\")')",
            "exec('import os; os.system(\"whoami\")')",
            "compile('import os', '<string>', 'exec')",
        ],
        "comment_bypass": [
            'import os; x = "safe string" # os.system("rm -rf /")',
            'print("hello") # import subprocess; subprocess.run(["ls"])',
            '# This looks safe\nimport os  # but this is dangerous',
        ],
        "attribute_access": [
            "print.__class__.__bases__[0].__subclasses__()",
            "[].__class__.__bases__[0].__subclasses__()[104].__init__.__globals__['sys']",
            "().__class__.__bases__[0].__subclasses__()[59].__init__.__globals__['__builtins__']['eval']",
        ],
        "resource_exhaustion": [
            "while True: pass",
            "[i for i in range(10**8)]",
            "x = 'a' * (10**8)",
            "def f(): f()\nf()",
        ],
        "encoding_attacks": [
            "exec('\\x69\\x6d\\x70\\x6f\\x72\\x74\\x20\\x6f\\x73')",  # import os in hex
            "eval(chr(105)+chr(109)+chr(112)+chr(111)+chr(114)+chr(116)+chr(32)+chr(111)+chr(115))",  # import os
            "__import__(''.join([chr(111), chr(115)]))",  # os
        ],
        "unicode_attacks": [
            "＿＿ｉｍｐｏｒｔ＿＿('os')",  # Full-width characters
            "import os\u200b",  # Zero-width space
            "import\u00a0os",  # Non-breaking space
        ]
    }


@pytest.fixture
def safe_code_samples() -> list:
    """Provide safe code samples that should pass validation."""
    return [
        "print('Hello, World!')",
        "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2, 3]})\nprint(df)",
        "import numpy as np\narr = np.array([1, 2, 3])\nprint(arr.mean())",
        "import math\nprint(math.sqrt(16))",
        "x = 5\ny = 10\nprint(x + y)",
        "for i in range(5):\n    print(i)",
        "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)\nprint(factorial(5))",
    ]
