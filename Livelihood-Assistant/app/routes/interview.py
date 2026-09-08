"""State-light conversational livelihood interview endpoint."""

from fastapi import APIRouter, Depends, status

from app.routes.profile import get_profile_service
from app.schemas.interview import InterviewTurnRequest, InterviewTurnResponse
from app.services.ai.extractor import BaseProfileExtractionService
from app.services.interview.service import BaseLivelihoodInterviewService, LivelihoodInterviewService

router = APIRouter(prefix="/interview", tags=["Livelihood Interview"])


def get_interview_service(
    extraction_service: BaseProfileExtractionService = Depends(get_profile_service),
) -> BaseLivelihoodInterviewService:
    """Reuse the existing Phase 6 extractor; no session persistence is required."""
    return LivelihoodInterviewService(extraction_service)


@router.post(
    "/turn",
    response_model=InterviewTurnResponse,
    status_code=status.HTTP_200_OK,
    summary="Process one livelihood interview turn and choose the next question",
)
async def process_interview_turn(
    request: InterviewTurnRequest,
    service: BaseLivelihoodInterviewService = Depends(get_interview_service),
) -> InterviewTurnResponse:
    return await service.process_turn(request)
