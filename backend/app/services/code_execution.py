"""Code execution service with subprocess isolation."""

import subprocess
import tempfile
import time
import os
from typing import Optional

from app.core.config import settings
from app.models.submission import SubmissionStatus
from app.schemas.submission import CodeExecutionResponse


class CodeExecutionService:
    """Service for executing Python code using subprocess."""

    def __init__(self) -> None:
        """Initialize the code execution service."""
        self.timeout = settings.EXECUTION_TIMEOUT

    async def execute_code(self, code: str) -> CodeExecutionResponse:
        """Execute Python code using subprocess."""
        start_time = time.time()
        
        try:
            # Validate code length
            if len(code) > settings.MAX_CODE_LENGTH:
                return CodeExecutionResponse(
                    output=None,
                    error="Code exceeds maximum length limit",
                    status=SubmissionStatus.ERROR,
                    execution_time=0.0,
                )

            # Prepare the Python script with pandas and scipy imports available
            script = f"""
import sys
import traceback
import pandas as pd
import scipy
import numpy as np

try:
{self._indent_code(code)}
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
"""

            # Run code using subprocess
            result = await self._run_with_subprocess(script)
            execution_time = time.time() - start_time

            return CodeExecutionResponse(
                output=result.get("output"),
                error=result.get("error"),
                status=result.get("status", SubmissionStatus.SUCCESS),
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return CodeExecutionResponse(
                output=None,
                error=f"Execution service error: {str(e)}",
                status=SubmissionStatus.ERROR,
                execution_time=execution_time,
            )

    def _indent_code(self, code: str) -> str:
        """Indent user code for proper execution within try block."""
        lines = code.split('\n')
        indented_lines = ['    ' + line for line in lines]
        return '\n'.join(indented_lines)

    async def _run_with_subprocess(self, script: str) -> dict[str, Optional[str]]:
        """Run script using subprocess with security restrictions."""
        try:
            # Create a temporary file with the script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script)
                temp_file = f.name
            
            try:
                # Run the script with timeout
                result = subprocess.run(
                    ["python3", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd="/tmp"
                )
                
                if result.returncode == 0:
                    return {
                        "output": result.stdout.strip() if result.stdout.strip() else None,
                        "error": None,
                        "status": SubmissionStatus.SUCCESS,
                    }
                else:
                    return {
                        "output": None,
                        "error": result.stderr.strip() if result.stderr.strip() else "Unknown error occurred",
                        "status": SubmissionStatus.ERROR,
                    }
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass

        except subprocess.TimeoutExpired:
            return {
                "output": None,
                "error": f"Code execution timed out after {self.timeout} seconds",
                "status": SubmissionStatus.TIMEOUT,
            }
        except Exception as e:
            return {
                "output": None,
                "error": f"Execution error: {str(e)}",
                "status": SubmissionStatus.ERROR,
            }
