"""REST API for Matcha-TTS: text in, base64-encoded WAV out.

Run with: uvicorn server.main:app --reload
"""
import base64
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from server.config import CORS_ORIGINS, DEVICE, SAMPLE_RATE, VOICES
from server.schemas import SynthesisRequest, SynthesisResponse, VoiceInfo
from server.tts import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    engine.load()
    yield
    engine.unload()


app = FastAPI(title="Mamtil TTS API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok" if engine.loaded else "loading", "device": str(DEVICE)}


@app.get("/api/voices", response_model=list[VoiceInfo])
def list_voices():
    return [VoiceInfo(id=voice_id, name=voice["name"]) for voice_id, voice in VOICES.items()]


@app.post("/api/tts", response_model=SynthesisResponse)
def synthesize(request: SynthesisRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Text must not be blank")

    audio, duration, processing_time = engine.synthesize(
        text,
        voice=request.voice,
        temperature=request.temperature,
        speaking_rate=request.speaking_rate,
        steps=request.steps,
    )
    return SynthesisResponse(
        audio=base64.b64encode(audio).decode("ascii"),
        voice=request.voice,
        sample_rate=SAMPLE_RATE,
        duration=round(duration, 3),
        processing_time=round(processing_time, 3),
    )
