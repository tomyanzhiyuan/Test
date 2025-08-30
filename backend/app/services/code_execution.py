"""Secure code execution service with Docker container isolation."""

import asyncio
import re
import time
import uuid
from typing import Optional, Dict, Any

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
        # Configure Docker client with proper connection handling
        self.client = None
        self.docker_available = False
        self.docker_error_message = None
        self._initialize_docker_client()
        
        self.execution_image = "code-execution:latest"
        self.timeout = settings.EXECUTION_TIMEOUT
        self.memory_limit = settings.MEMORY_LIMIT
        self.validator = CodeValidator()

    def _initialize_docker_client(self) -> None:
        """Initialize Docker client with comprehensive error handling."""
        import os
        
        # Clear any problematic environment variables first
        if 'DOCKER_HOST' in os.environ:
            del os.environ['DOCKER_HOST']
        
        # Try different Docker connection methods with proper URL handling
        connection_methods = [
            # Method 1: Direct socket connection with explicit API client
            ("Direct socket API", lambda: self._create_direct_socket_client()),
            # Method 2: Unix socket with explicit base_url
            ("Unix socket", lambda: docker.DockerClient(base_url='unix:///var/run/docker.sock')),
            # Method 3: TCP connection (for Docker Desktop on macOS/Windows)
            ("TCP localhost:2375", lambda: docker.DockerClient(base_url='tcp://localhost:2375')),
            # Method 4: Docker Desktop default
            ("TCP localhost:2376", lambda: docker.DockerClient(base_url='tcp://localhost:2376', tls=False)),
        ]
        
        for method_name, method in connection_methods:
            try:
                client = method()
                # Test the connection
                client.ping()
                self.client = client
                self.docker_available = True
                print(f"✅ Docker client initialized successfully using {method_name}")
                return
            except Exception as e:
                print(f"❌ Docker connection via {method_name} failed: {e}")
                continue
        
        # If all methods fail, set detailed error message
        self.docker_available = False
        self.docker_error_message = self._generate_docker_error_message()
        print(f"🚨 Docker unavailable: {self.docker_error_message}")

    def _create_direct_socket_client(self):
        """Create Docker client with direct socket access."""
        import docker.api
        import docker.client
        
        # Create API client directly with socket
        api_client = docker.api.APIClient(base_url='unix:///var/run/docker.sock')
        
        # Create high-level client using the API client
        return docker.client.DockerClient(api=api_client)

    def _generate_docker_error_message(self) -> str:
        """Generate a helpful error message for Docker connection failures."""
        return (
            "Docker service is not available. Please ensure:\n"
            "1. Docker is installed and running\n"
            "2. Docker daemon is accessible (check 'docker ps' in terminal)\n"
            "3. Current user has Docker permissions\n"
            "4. Docker socket is accessible at /var/run/docker.sock\n"
            "Code execution requires Docker for security isolation."
        )

    def get_service_health(self) -> Dict[str, Any]:
        """Get the health status of the code execution service."""
        if not self.docker_available:
            return {
                "status": "unhealthy",
                "docker_available": False,
                "error": self.docker_error_message,
                "execution_available": False
            }
        
        try:
            # Test Docker connection
            self.client.ping()
            
            # Check if execution image exists
            image_available = False
            try:
                self.client.images.get(self.execution_image)
                image_available = True
            except ImageNotFound:
                pass
            
            return {
                "status": "healthy" if image_available else "degraded",
                "docker_available": True,
                "execution_image_available": image_available,
                "execution_available": True,
                "image_name": self.execution_image
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "docker_available": False,
                "error": f"Docker connection lost: {str(e)}",
                "execution_available": False
            }

    async def execute_code(self, code: str) -> CodeExecutionResponse:
        """Execute Python code in a secure Docker container."""
        start_time = time.time()
        
        # Check if Docker is available
        if not self.docker_available:
            return CodeExecutionResponse(
                output=None,
                error=f"Code execution service unavailable: {self.docker_error_message}",
                status=SubmissionStatus.ERROR,
                execution_time=0.0,
            )
        
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

    async def _run_in_secure_container(self, script: str) -> Dict[str, Optional[str]]:
        """Run script in a secure Docker container with comprehensive restrictions."""
        container = None
        
        # Double-check Docker availability
        if not self.docker_available or self.client is None:
            return {
                "output": None,
                "error": "Docker service is not available for secure code execution",
                "status": SubmissionStatus.ERROR,
            }
        
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

        except Exception as e:
            if "timeout" in str(e).lower():
                return {
                    "output": None,
                    "error": f"Code execution timed out after {self.timeout} seconds",
                    "status": SubmissionStatus.TIMEOUT,
                }
            elif "image" in str(e).lower() and "not found" in str(e).lower():
                return {
                    "output": None,
                    "error": "Code execution environment is not properly configured. Please contact administrator.",
                    "status": SubmissionStatus.ERROR,
                }
            else:
                return {
                    "output": None,
                    "error": f"Docker execution error: {self._sanitize_error_message(str(e))}",
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
        if not self.client:
            raise Exception("Docker client not available")
            
        try:
            self.client.images.get(self.execution_image)
        except ImageNotFound:
            # Build the execution image
            try:
                print(f"Building execution image: {self.execution_image}")
                self.client.images.build(
                    path="/app/../docker",
                    dockerfile="Dockerfile.execution",
                    tag=self.execution_image,
                    rm=True,
                    forcerm=True
                )
                print(f"✅ Successfully built execution image: {self.execution_image}")
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
            if hasattr(self, 'client') and self.client:
                self.client.close()
        except:
            pass
