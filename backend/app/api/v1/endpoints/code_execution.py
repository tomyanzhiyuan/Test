"""Code execution endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.schemas.submission import (
    CodeExecutionRequest,
    CodeExecutionResponse,
    SubmissionCreate,
    SubmissionResponse,
)
from app.services.code_execution import CodeExecutionService
from app.services.lambda_execution import LambdaExecutionService
from app.services.code_validator import CodeValidator
from app.services.submission import SubmissionService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/execute",
    response_model=CodeExecutionResponse,
    summary="Execute Python code",
    description="Execute Python code in a secure Docker container",
)
@limiter.limit(settings.RATE_LIMIT)
async def execute_code(
    request: Request,
    code_request: CodeExecutionRequest,
) -> CodeExecutionResponse:
    """Execute Python code without persisting to database."""
    try:
        # Choose execution service based on configuration
        if settings.USE_LAMBDA_EXECUTION:
            execution_service = LambdaExecutionService()
        else:
            execution_service = CodeExecutionService()
        
        result = await execution_service.execute_code(code_request.code)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code execution failed: {str(e)}",
        )


@router.post(
    "/submit",
    response_model=SubmissionResponse,
    summary="Submit and execute Python code",
    description="Execute Python code and persist the result to database",
)
@limiter.limit(settings.RATE_LIMIT)
async def submit_code(
    request: Request,
    submission_request: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    """Execute Python code and save submission to database."""
    try:
        # First execute the code
        if settings.USE_LAMBDA_EXECUTION:
            execution_service = LambdaExecutionService()
        else:
            execution_service = CodeExecutionService()
        
        execution_result = await execution_service.execute_code(submission_request.code)
        
        # Only persist if execution was successful
        if execution_result.status != "error":
            submission_service = SubmissionService(db)
            submission = await submission_service.create_submission(
                code=submission_request.code,
                output=execution_result.output,
                error=execution_result.error,
                status=execution_result.status,
                execution_time=execution_result.execution_time,
            )
            return submission
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Code execution failed: {execution_result.error}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Submission failed: {str(e)}",
        )


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionResponse,
    summary="Get submission by ID",
    description="Retrieve a specific code submission by its ID",
)
async def get_submission(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    """Get a specific submission by ID."""
    try:
        submission_service = SubmissionService(db)
        submission = await submission_service.get_submission(submission_id)
        if not submission:
            raise HTTPException(
                status_code=404,
                detail="Submission not found",
            )
        return submission
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve submission: {str(e)}",
        )
