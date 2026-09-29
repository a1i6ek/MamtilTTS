from typing import Literal

from pydantic import BaseModel, Field

from server.config import MAX_TEXT_LENGTH

Voice = Literal["man", "woman"]


class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    voice: Voice = "man"
    temperature: float = Field(default=0.667, ge=0, le=2)
    speaking_rate: float = Field(default=1.0, gt=0, le=3, description="Length scale: higher is slower")
    steps: int = Field(default=10, ge=1, le=100, description="Number of ODE steps")


class SynthesisResponse(BaseModel):
    audio: str = Field(description="Base64-encoded WAV (16-bit PCM)")
    voice: Voice
    format: str = "wav"
    sample_rate: int
    duration: float = Field(description="Audio length in seconds")
    processing_time: float = Field(description="Synthesis time in seconds")


class VoiceInfo(BaseModel):
    id: Voice
    name: str
