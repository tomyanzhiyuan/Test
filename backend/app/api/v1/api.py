"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import code_execution

api_router = APIRouter()

api_router.include_router(
    code_execution.router,
    prefix="/code",
    tags=["code-execution"],
)
