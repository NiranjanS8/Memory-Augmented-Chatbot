from collections.abc import Generator

import openai
from groq import Groq

from backend.config import settings
from backend.models.base import LLMClient, LLMResponse, Message


class GroqClient(LLMClient):
    model_id = "llama-3.1-70b-versatile"
    display_name = "Groq (Llama 3.1 70B)"
    max_context_tokens = 32_000

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        # Groq has no embedding API; delegate to OpenAI.
        self._embed_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def _build_messages(self, messages: list[Message], system: str) -> list[dict]:
        out = []
        if system:
            out.append({"role": "system", "content": system})
        out.extend({"role": m.role, "content": m.content} for m in messages)
        return out

    def chat(self, messages: list[Message], system: str = "") -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=self._build_messages(messages, system),
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content,
            model=response.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

    def stream(self, messages: list[Message], system: str = "") -> Generator[str, None, None]:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=self._build_messages(messages, system),
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def embed(self, text: str) -> list[float]:
        response = self._embed_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
