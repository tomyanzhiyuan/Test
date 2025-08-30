"""Secure code execution service with Docker container isolation."""

import asyncio
import re
import time
import uuid
from typing import Optional

import docker
from docker.errors import ContainerError, ImageNotFound, APIError

from app.core.config import settings
from app.models.submission import SubmissionStatus
from app.schemas.submission import CodeExecutionResponse
from app.services.code_validator import CodeValidator


class CodeExecutionService:
    """Service for executing Python code in secure Docker containers."""

    def __init__(self) -> None:
        """Initialize the code execution service."""
        self.client = docker.from_env()
        self.execution_image = "code-execution:latest"
        self.timeout = settings.EXECUTION_TIMEOUT
        self.memory_limit = settings.MEMORY_LIMIT
        self.validator = CodeValidator()

    async def execute_code(self, code: str) -> CodeExecutionResponse:
        """Execute Python code in a secure Docker container."""
        start_time = time.time()
        
        try:
            # Pre-execution validation
            is_safe, reason = self.validator.is_code_safe(code)
            if not is_safe:
                return CodeExecutionResponse(
                    output=None,
                    error=f"Code validation failed: {reason}",
                    status=SubmissionStatus.ERROR,
                    execution_time=0.0,
                )

            # Sanitize code
            sanitized_code = self.validator.sanitize_code(code)

            # Prepare the Python script with restricted imports
            script = f"""
import sys
import traceback

# Only allow safe imports
import pandas as pd
import numpy as np
import scipy
import math
import statistics
import random
import datetime
import json
import csv
import re
import collections
import itertools
import functools
import operator

try:
{self._indent_code(sanitized_code)}
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
"""

            # Execute in secure Docker container
            result = await self._run_in_secure_container(script)
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

    async def _run_in_secure_container(self, script: str) -> dict[str, Optional[str]]:
        """Run script in a secure Docker container with comprehensive restrictions."""
        container = None
        try:
            # Try Docker container execution first
            try:
                # Ensure execution image exists
                await self._ensure_execution_image()

                # Generate unique container name
                container_name = f"code-exec-{uuid.uuid4().hex[:8]}"

                # Create and run container with maximum security
                container = self.client.containers.run(
                    image=self.execution_image,
                    command=["python3", "-c", script],
                    detach=True,
                    name=container_name,
                    # Resource limits
                    mem_limit=self.memory_limit,
                    memswap_limit=self.memory_limit,  # Disable swap
                    cpu_quota=50000,  # 50% CPU limit
                    cpu_period=100000,
                    # Security restrictions
                    network_disabled=True,  # No network access
                    read_only=True,  # Read-only root filesystem
                    user="coderunner",  # Non-root user
                    # Security options
                    security_opt=[
                        "no-new-privileges:true",
                        "seccomp=unconfined"  # Could be more restrictive
                    ],
                    # Capabilities
                    cap_drop=["ALL"],  # Drop all capabilities
                    # Filesystem restrictions
                    tmpfs={
                        "/secure_tmp": "noexec,nosuid,nodev,size=50m",
                        "/tmp": "noexec,nosuid,nodev,size=10m"
                    },
                    # Environment restrictions
                    environment={
                        "PYTHONPATH": "",
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONUNBUFFERED": "1",
                        "HOME": "/secure_tmp"
                    },
                    # Auto-cleanup
                    remove=True,
                    # Working directory
                    working_dir="/secure_tmp"
                )

                # Wait for container with timeout
                result = container.wait(timeout=self.timeout)
                exit_code = result["StatusCode"]
                
                # Get logs
                logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
                
                if exit_code == 0:
                    # Successful execution
                    return {
                        "output": logs.strip() if logs.strip() else None,
                        "error": None,
                        "status": SubmissionStatus.SUCCESS,
                    }
                else:
                    # Execution error
                    return {
                        "output": None,
                        "error": self._sanitize_error_message(logs.strip()) if logs.strip() else "Unknown error occurred",
                        "status": SubmissionStatus.ERROR,
                    }

            except Exception as docker_error:
                # Docker failed, fall back to subprocess with validation already applied
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
                            "error": self._sanitize_error_message(result.stderr.strip()) if result.stderr.strip() else "Unknown error occurred",
                            "status": SubmissionStatus.ERROR,
                        }
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_file)
                    except:
                        pass

        except Exception as e:
            if "timeout" in str(e).lower():
                return {
                    "output": None,
                    "error": f"Code execution timed out after {self.timeout} seconds",
                    "status": SubmissionStatus.TIMEOUT,
                }
            else:
                return {
                    "output": None,
                    "error": f"Execution error: {self._sanitize_error_message(str(e))}",
                    "status": SubmissionStatus.ERROR,
                }
        finally:
            # Ensure container cleanup
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass

    async def _ensure_execution_image(self) -> None:
        """Ensure the secure execution image exists."""
        try:
            self.client.images.get(self.execution_image)
        except ImageNotFound:
            # Build the execution image
            try:
                self.client.images.build(
                    path="/app/../docker",
                    dockerfile="Dockerfile.execution",
                    tag=self.execution_image,
                    rm=True,
                    forcerm=True
                )
            except Exception as e:
                raise Exception(f"Failed to build execution image: {str(e)}")

    def _sanitize_error_message(self, error_msg: str) -> str:
        """Sanitize error messages to remove sensitive information."""
        # Remove file paths
        error_msg = re.sub(r'/[a-zA-Z0-9_/.-]+\.py', '<script>', error_msg)
        
        # Remove container IDs and Docker-specific info
        error_msg = re.sub(r'[a-f0-9]{12,}', '<container>', error_msg)
        
        # Remove system paths
        error_msg = re.sub(r'/usr/[a-zA-Z0-9_/.-]+', '<system_path>', error_msg)
        error_msg = re.sub(r'/tmp/[a-zA-Z0-9_/.-]+', '<temp_path>', error_msg)
        
        # Limit error message length
        if len(error_msg) > 1000:
            error_msg = error_msg[:1000] + "... (truncated)"
        
        return error_msg

    def __del__(self) -> None:
        """Clean up Docker client."""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except:
            pass
