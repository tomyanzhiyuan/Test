"""Submission service for database operations."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import Submission, SubmissionStatus
from app.schemas.submission import SubmissionResponse


class SubmissionService:
    """Service for managing code submissions in the database."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the submission service."""
        self.db = db

    async def create_submission(
        self,
        code: str,
        output: Optional[str] = None,
        error: Optional[str] = None,
        status: SubmissionStatus = SubmissionStatus.SUCCESS,
        execution_time: Optional[float] = None,
    ) -> SubmissionResponse:
        """Create a new code submission."""
        submission = Submission(
            code=code,
            output=output,
            error=error,
            status=status,
            execution_time=execution_time,
        )
        
        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)
        
        return SubmissionResponse.from_orm(submission)

    async def get_submission(self, submission_id: str) -> Optional[SubmissionResponse]:
        """Get a submission by ID."""
        try:
            submission_uuid = uuid.UUID(submission_id)
        except ValueError:
            return None

        stmt = select(Submission).where(Submission.id == submission_uuid)
        result = await self.db.execute(stmt)
        submission = result.scalar_one_or_none()
        
        if submission:
            return SubmissionResponse.from_orm(submission)
        return None

    async def get_submissions(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[SubmissionResponse]:
        """Get a list of submissions with pagination."""
        stmt = (
            select(Submission)
            .order_by(Submission.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        submissions = result.scalars().all()
        
        return [SubmissionResponse.from_orm(submission) for submission in submissions]

    async def delete_submission(self, submission_id: str) -> bool:
        """Delete a submission by ID."""
        try:
            submission_uuid = uuid.UUID(submission_id)
        except ValueError:
            return False

        stmt = select(Submission).where(Submission.id == submission_uuid)
        result = await self.db.execute(stmt)
        submission = result.scalar_one_or_none()
        
        if submission:
            await self.db.delete(submission)
            await self.db.commit()
            return True
        return False
