from collections.abc import Generator

from google import genai
from google.genai import types

from backend.config import settings
from backend.models.base import LLMClient, LLMResponse, Message


class GeminiClient(LLMClient):
    model_id = "gemini-2.0-flash"
    display_name = "Gemini 2.0 Flash"
    max_context_tokens = 1_000_000

    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    def _to_contents(
        self, messages: list[Message], attachments: list[dict] | None = None
    ) -> list[types.Content]:
        import base64
        contents = []
        for i, m in enumerate(messages):
            if m.role == "system":
                continue
            role = "user" if m.role == "user" else "model"
            parts = [types.Part(text=m.content)]

            if i == len(messages) - 1 and m.role == "user" and attachments:
                for att in attachments:
                    if att["type"] == "image":
                        img_bytes = base64.b64decode(att["content"])
                        parts.append(
                            types.Part.from_bytes(
                                data=img_bytes,
                                mime_type=att.get("media_type") or "image/jpeg",
                            )
                        )
                    elif att["type"] == "text":
                        parts.append(
                            types.Part(text=f"\n\n[Attachment: {att['filename']}]\n{att['content']}")
                        )

            contents.append(types.Content(role=role, parts=parts))
        return contents

    def chat(
        self,
        messages: list[Message],
        system: str = "",
        attachments: list[dict] | None = None,
    ) -> LLMResponse:
        config = types.GenerateContentConfig(system_instruction=system) if system else None
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=self._to_contents(messages, attachments),
            config=config,
        )
        usage = response.usage_metadata
        return LLMResponse(
            content=response.text or "",
            model=self.model_id,
            input_tokens=usage.prompt_token_count or 0,
            output_tokens=usage.candidates_token_count or 0,
        )

    def stream(
        self,
        messages: list[Message],
        system: str = "",
        attachments: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        config = types.GenerateContentConfig(system_instruction=system) if system else None
        for chunk in self.client.models.generate_content_stream(
            model=self.model_id,
            contents=self._to_contents(messages, attachments),
            config=config,
        ):
            if chunk.text:
                yield chunk.text


    def embed(self, text: str) -> list[float]:
        embedding_response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        return embedding_response.embeddings[0].values
