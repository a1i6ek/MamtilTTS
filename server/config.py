"""Server settings, overridable through environment variables."""
import os
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = Path(os.getenv("MATCHA_ASSETS_DIR", ROOT / "assets"))

# Voice id -> display name and checkpoint. Keep in sync with VOICES in web/src/lib/api.ts.
VOICES = {
    "man": {"name": "Man", "checkpoint": ASSETS_DIR / "checkpoint_epoch=279.ckpt"},
    "woman": {"name": "Woman", "checkpoint": ASSETS_DIR / "checkpoint_epoch=479.ckpt"},
}

VOCODER_NAME = os.getenv("MATCHA_VOCODER", "hifigan_univ_v1")
DEVICE = torch.device(os.getenv("MATCHA_DEVICE", "cuda" if torch.cuda.is_available() else "cpu"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

SAMPLE_RATE = 22050
MAX_TEXT_LENGTH = 1000
