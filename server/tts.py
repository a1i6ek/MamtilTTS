"""Loads the Matcha voices and vocoder once and synthesizes WAV audio."""
import io
import threading
import time

import soundfile as sf
import torch

from matcha.cli import VOCODER_URLS, load_matcha, load_vocoder, process_text, to_waveform
from matcha.utils.utils import assert_model_downloaded, get_user_data_dir
from server.config import DEVICE, SAMPLE_RATE, VOCODER_NAME, VOICES


class TTSEngine:
    def __init__(self):
        self.voices = {}
        self.vocoder = None
        self.denoiser = None
        # The models are not safe to run concurrently; serialize inference.
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return bool(self.voices)

    def load(self):
        vocoder_path = get_user_data_dir() / VOCODER_NAME
        assert_model_downloaded(vocoder_path, VOCODER_URLS[VOCODER_NAME])
        for voice_id, voice in VOICES.items():
            self.voices[voice_id] = load_matcha(voice_id, voice["checkpoint"], DEVICE)
        self.vocoder, self.denoiser = load_vocoder(VOCODER_NAME, vocoder_path, DEVICE)

    def unload(self):
        self.voices.clear()
        self.vocoder = self.denoiser = None

    def synthesize(self, text: str, voice: str, temperature: float, speaking_rate: float, steps: int):
        """Returns (wav_bytes, duration_seconds, processing_seconds)."""
        start = time.perf_counter()
        with self._lock, torch.inference_mode():
            processed = process_text(0, text, DEVICE)
            output = self.voices[voice].synthesise(
                processed["x"],
                processed["x_lengths"],
                n_timesteps=steps,
                temperature=temperature,
                spks=None,
                length_scale=speaking_rate,
            )
            waveform = to_waveform(output["mel"], self.vocoder, self.denoiser).numpy()
        processing_time = time.perf_counter() - start

        buffer = io.BytesIO()
        sf.write(buffer, waveform, SAMPLE_RATE, format="WAV", subtype="PCM_16")
        return buffer.getvalue(), len(waveform) / SAMPLE_RATE, processing_time


engine = TTSEngine()
