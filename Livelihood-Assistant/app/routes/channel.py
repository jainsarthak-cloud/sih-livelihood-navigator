"""Channel-agnostic external interaction endpoint; no vendor integration is included."""

from fastapi import APIRouter, Depends, status

from app.routes.interview import get_interview_service
from app.routes.livelihood import get_livelihood_assessment_service
from app.routes.speech import get_speech_service
from app.schemas.channel import ChannelInteractRequest, ChannelInteractResponse
from app.services.channel.interaction import BaseChannelInteractionService, ChannelInteractionService
from app.services.interview.service import BaseLivelihoodInterviewService
from app.services.livelihood.assessment import LivelihoodAssessmentService
from app.services.speech.transcriber import BaseSpeechTranscriptionService

router = APIRouter(prefix="/channel", tags=["External Channel Boundary"])


def get_channel_interaction_service(
    speech_service: BaseSpeechTranscriptionService = Depends(get_speech_service),
    interview_service: BaseLivelihoodInterviewService = Depends(get_interview_service),
    assessment_service: LivelihoodAssessmentService = Depends(get_livelihood_assessment_service),
) -> BaseChannelInteractionService:
    return ChannelInteractionService(speech_service, interview_service, assessment_service)


@router.post("/interact", response_model=ChannelInteractResponse, status_code=status.HTTP_200_OK,
             summary="Process a channel-neutral text or voice livelihood interaction")
async def interact(
    request: ChannelInteractRequest,
    service: BaseChannelInteractionService = Depends(get_channel_interaction_service),
) -> ChannelInteractResponse:
    return await service.interact(request)
