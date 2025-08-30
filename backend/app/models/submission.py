"""Submission database model."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class SubmissionStatus(str, Enum):
    """Submission status enumeration."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    MEMORY_LIMIT = "memory_limit"


class Submission(Base):
    """Code submission model."""

    __tablename__ = "submissions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    code = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    status = Column(
        SQLEnum(SubmissionStatus),
        nullable=False,
        default=SubmissionStatus.SUCCESS,
    )
    execution_time = Column(Float, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        """String representation of submission."""
        return f"<Submission(id={self.id}, status={self.status})>"
