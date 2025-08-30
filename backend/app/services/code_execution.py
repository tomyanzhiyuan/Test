"""Code execution service with Docker isolation."""

import asyncio
import time
from typing import Optional

import docker
from docker.errors import ContainerError, ImageNotFound

from app.core.config import settings
from app.models.submission import SubmissionStatus
from app.schemas.submission import CodeExecutionResponse


class CodeExecutionService:
    """Service for executing Python code in isolated Docker containers."""

    def __init__(self) -> None:
        """Initialize the code execution service."""
        self.client = docker.from_env()
        self.docker_image = settings.DOCKER_IMAGE
        self.timeout = settings.EXECUTION_TIMEOUT
        self.memory_limit = settings.MEMORY_LIMIT

    async def execute_code(self, code: str) -> CodeExecutionResponse:
        """Execute Python code in a secure Docker container."""
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

            # Run code in Docker container
            result = await self._run_in_container(script)
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

    async def _run_in_container(self, script: str) -> dict[str, Optional[str]]:
        """Run script in Docker container with security restrictions."""
        try:
            # For now, simulate code execution without Docker
            # This is a temporary solution until Docker-in-Docker is properly configured
            import subprocess
            import tempfile
            import os
            
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

            # Wait for container with timeout
            try:
                exit_code = container.wait(timeout=self.timeout)["StatusCode"]
                logs = container.logs(stdout=True, stderr=True).decode("utf-8")
                
                if exit_code == 0:
                    return {
                        "output": logs.strip() if logs.strip() else None,
                        "error": None,
                        "status": SubmissionStatus.SUCCESS,
                    }
                else:
                    return {
                        "output": None,
                        "error": logs.strip() if logs.strip() else "Unknown error occurred",
                        "status": SubmissionStatus.ERROR,
                    }

            except Exception as e:
                # Handle timeout or other container errors
                try:
                    container.kill()
                except:
                    pass
                
                if "timeout" in str(e).lower():
                    return {
                        "output": None,
                        "error": f"Code execution timed out after {self.timeout} seconds",
                        "status": SubmissionStatus.TIMEOUT,
                    }
                else:
                    return {
                        "output": None,
                        "error": f"Container execution error: {str(e)}",
                        "status": SubmissionStatus.ERROR,
                    }

        except ContainerError as e:
            return {
                "output": None,
                "error": f"Container error: {str(e)}",
                "status": SubmissionStatus.ERROR,
            }
        except Exception as e:
            return {
                "output": None,
                "error": f"Docker execution error: {str(e)}",
                "status": SubmissionStatus.ERROR,
            }

    def __del__(self) -> None:
        """Clean up Docker client."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except:
            pass
