"""Channel-neutral adapter that delegates to established pipeline services."""

from abc import ABC, abstractmethod

from app.schemas.channel import ChannelInteractRequest, ChannelInteractResponse
from app.schemas.interview import InterviewTurnRequest
from app.schemas.livelihood import LivelihoodAssessRequest
from app.schemas.speech import SpeechTranscribeRequest
from app.services.interview.service import BaseLivelihoodInterviewService
from app.services.livelihood.assessment import LivelihoodAssessmentService
from app.services.speech.transcriber import BaseSpeechTranscriptionService


class BaseChannelInteractionService(ABC):
    @abstractmethod
    async def interact(self, request: ChannelInteractRequest) -> ChannelInteractResponse:
        """Process one channel interaction without channel-specific business logic."""


class ChannelInteractionService(BaseChannelInteractionService):
    """Adapt text/audio at the edge; all profile and livelihood logic stays downstream."""

    def __init__(
        self,
        speech_service: BaseSpeechTranscriptionService,
        interview_service: BaseLivelihoodInterviewService,
        assessment_service: LivelihoodAssessmentService,
    ):
        self._speech = speech_service
        self._interview = interview_service
        self._assessment = assessment_service

    async def interact(self, request: ChannelInteractRequest) -> ChannelInteractResponse:
        transcript = None
        speech_metadata = None
        text = request.text
        if request.audio is not None:
            speech = await self._speech.transcribe(SpeechTranscribeRequest(
                audio_content_base64=request.audio.audio_content_base64,
                audio_format=request.audio.audio_format,
                language_code=request.language,
            ))
            transcript = speech.transcript
            speech_metadata = speech.processing_metadata
            if speech.status == "no_speech_detected":
                return ChannelInteractResponse(
                    channel=request.channel, external_user_reference=request.external_user_reference,
                    session_id=request.session_id, language=request.language, transcript=transcript,
                    speech_metadata=speech_metadata, status="no_speech_detected",
                )
            text = transcript

        interview = await self._interview.process_turn(InterviewTurnRequest(
            user_text=text or "", language=request.language, session_id=request.session_id,
            profile=request.profile, unknown_slots=request.unknown_slots,
        ))
        assessment = await self._assessment.assess(LivelihoodAssessRequest(profile=interview.profile))
        return ChannelInteractResponse(
            channel=request.channel, external_user_reference=request.external_user_reference,
            session_id=request.session_id, language=request.language, transcript=transcript,
            speech_metadata=speech_metadata, interview=interview, assessment=assessment,
            status="completed",
        )
