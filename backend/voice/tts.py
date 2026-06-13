import httpx

from backend.config import settings

VOICE_MAP = {
    "aria": "9BWtsMINqrJLrRacOk9x",
    "roger": "CwhRBWXzGAHq8TQ4Fs17",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
}

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


class TextToSpeech:
    def __init__(self):
        self._api_key = settings.ELEVENLABS_API_KEY
        if not self._api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not configured")

    def synthesize(self, text: str, voice: str = "aria") -> bytes:
        voice_id = VOICE_MAP.get(voice)
        if not voice_id:
            raise ValueError(f"Unknown voice '{voice}'. Available: {list(VOICE_MAP)}")

        response = httpx.post(
            ELEVENLABS_TTS_URL.format(voice_id=voice_id),
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.content
