"""Submission schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.submission import SubmissionStatus


class CodeExecutionRequest(BaseModel):
    """Request schema for code execution."""

    code: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Python code to execute",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate code input."""
        if not v.strip():
            raise ValueError("Code cannot be empty")
        return v.strip()


class CodeExecutionResponse(BaseModel):
    """Response schema for code execution."""

    output: Optional[str] = Field(None, description="Execution output")
    error: Optional[str] = Field(None, description="Execution error")
    status: SubmissionStatus = Field(..., description="Execution status")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")


class SubmissionCreate(BaseModel):
    """Schema for creating a submission."""

    code: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Python code to submit",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate code input."""
        if not v.strip():
            raise ValueError("Code cannot be empty")
        return v.strip()


class SubmissionResponse(BaseModel):
    """Response schema for submission."""

    id: uuid.UUID = Field(..., description="Submission ID")
    code: str = Field(..., description="Submitted code")
    output: Optional[str] = Field(None, description="Execution output")
    error: Optional[str] = Field(None, description="Execution error")
    status: SubmissionStatus = Field(..., description="Execution status")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v),
        }
