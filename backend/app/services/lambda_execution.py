"""AWS Lambda code execution service."""

import json
import time
import base64
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import settings
from app.models.submission import SubmissionStatus
from app.schemas.submission import CodeExecutionResponse
from app.services.code_validator import CodeValidator


class LambdaExecutionService:
    """Service for executing Python code using AWS Lambda."""

    def __init__(self) -> None:
        """Initialize the Lambda execution service."""
        self.validator = CodeValidator()
        self.lambda_client = None
        self.lambda_available = False
        self.lambda_error_message = None
        self._initialize_lambda_client()

    def _initialize_lambda_client(self) -> None:
        """Initialize AWS Lambda client."""
        try:
            # Check if AWS credentials are configured
            if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
                self.lambda_available = False
                self.lambda_error_message = "AWS credentials not configured"
                print("🚨 AWS Lambda unavailable: No credentials configured")
                return

            # Clean and validate credentials
            access_key = str(settings.AWS_ACCESS_KEY_ID).strip()
            secret_key_raw = str(settings.AWS_SECRET_ACCESS_KEY).strip()
            region = str(settings.AWS_REGION).strip()
            
            # Try to decode if it's base64 encoded, otherwise use as-is
            try:
                if secret_key_raw.endswith('=') and len(secret_key_raw) > 40:
                    secret_key = base64.b64decode(secret_key_raw).decode('utf-8').strip()
                    print("🔓 Decoded base64 secret key")
                else:
                    secret_key = secret_key_raw
            except Exception:
                secret_key = secret_key_raw
            
            print(f"🔑 Initializing Lambda client with:")
            print(f"   Access Key: {access_key}")
            print(f"   Secret Key length: {len(secret_key)} chars")
            print(f"   Secret Key starts with: {secret_key[:8]}...")
            print(f"   Region: {region}")

            # Create Lambda client with explicit credentials
            self.lambda_client = boto3.client(
                'lambda',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )

            # Skip GetFunction check since we only have InvokeFunction permission
            # Just assume the function exists and test during actual invocation
            self.lambda_available = True
            print(f"✅ AWS Lambda client initialized successfully for function: {settings.LAMBDA_FUNCTION_NAME}")
            print(f"   Region: {region}")
            print(f"   Note: Skipping GetFunction check (requires additional IAM permissions)")

        except Exception as e:
            self.lambda_available = False
            self.lambda_error_message = f"Failed to initialize AWS Lambda client: {str(e)}"
            print(f"🚨 AWS Lambda initialization failed: {e}")

    def get_service_health(self) -> Dict[str, Any]:
        """Get the health status of the Lambda execution service."""
        if not self.lambda_available:
            return {
                "status": "unhealthy",
                "lambda_available": False,
                "error": self.lambda_error_message,
                "execution_available": False
            }

        # Since we only have InvokeFunction permission, we can't call GetFunction
        # Just return healthy status if the client was initialized successfully
        return {
            "status": "healthy",
            "lambda_available": True,
            "execution_available": True,
            "function_name": settings.LAMBDA_FUNCTION_NAME,
            "region": settings.AWS_REGION,
            "note": "Health check limited by IAM permissions (InvokeFunction only)"
        }

    async def execute_code(self, code: str) -> CodeExecutionResponse:
        """Execute Python code using AWS Lambda."""
        start_time = time.time()

        # Check if Lambda is available
        if not self.lambda_available:
            return CodeExecutionResponse(
                output=None,
                error=f"Code execution service unavailable: {self.lambda_error_message}",
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

            # Prepare Lambda payload
            payload = {
                "code": sanitized_code,
                "timeout": settings.EXECUTION_TIMEOUT
            }

            # Invoke Lambda function
            response = self.lambda_client.invoke(
                FunctionName=settings.LAMBDA_FUNCTION_NAME,
                InvocationType='RequestResponse',  # Synchronous execution
                Payload=json.dumps(payload)
            )

            # Parse Lambda response
            response_payload = json.loads(response['Payload'].read())
            execution_time = time.time() - start_time

            # Check if Lambda execution was successful
            if response['StatusCode'] == 200:
                # Handle the actual Lambda response format: {"statusCode": 200, "body": "output"}
                if 'body' in response_payload:
                    body_content = response_payload['body']
                    
                    # If body_content is a JSON string, try to parse it
                    try:
                        if isinstance(body_content, str) and body_content.startswith('"') and body_content.endswith('"'):
                            # Remove outer quotes and unescape
                            output = json.loads(body_content)
                        else:
                            output = body_content
                    except:
                        output = str(body_content)
                    
                    return CodeExecutionResponse(
                        output=output if output else None,
                        error=None,
                        status=SubmissionStatus.SUCCESS,
                        execution_time=execution_time,
                    )
                else:
                    # Fallback: treat entire response as output
                    return CodeExecutionResponse(
                        output=str(response_payload) if response_payload else None,
                        error=None,
                        status=SubmissionStatus.SUCCESS,
                        execution_time=execution_time,
                    )
            else:
                return CodeExecutionResponse(
                    output=None,
                    error=f"Lambda execution failed with status code: {response['StatusCode']}",
                    status=SubmissionStatus.ERROR,
                    execution_time=execution_time,
                )

        except ClientError as e:
            execution_time = time.time() - start_time
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'TooManyRequestsException':
                return CodeExecutionResponse(
                    output=None,
                    error="Code execution service is currently busy. Please try again later.",
                    status=SubmissionStatus.ERROR,
                    execution_time=execution_time,
                )
            else:
                return CodeExecutionResponse(
                    output=None,
                    error=f"AWS Lambda error: {error_message}",
                    status=SubmissionStatus.ERROR,
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
