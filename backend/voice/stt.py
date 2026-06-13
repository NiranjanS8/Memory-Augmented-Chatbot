import openai

from backend.config import settings


class SpeechToText:
    def __init__(self):
        self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        response = self._client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_bytes),
        )
        return response.text
