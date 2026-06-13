from collections.abc import Generator

import anthropic
import openai

from backend.config import settings
from backend.models.base import LLMClient, LLMResponse, Message


class ClaudeClient(LLMClient):
    model_id = "claude-sonnet-4-20250514"
    display_name = "Claude Sonnet"
    max_context_tokens = 200_000

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        # Anthropic has no embedding API; delegate to OpenAI.
        self._embed_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def _prepare_messages(
        self, messages: list[Message], attachments: list[dict] | None = None
    ) -> list[dict]:
        prepared = []
        for i, m in enumerate(messages):
            if m.role == "system":
                continue

            if i == len(messages) - 1 and m.role == "user" and attachments:
                content_list = [{"type": "text", "text": m.content}]
                for att in attachments:
                    if att["type"] == "image":
                        content_list.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": att.get("media_type") or "image/jpeg",
                                "data": att["content"],
                            }
                        })
                    elif att["type"] == "text":
                        content_list.append({
                            "type": "text",
                            "text": f"\n\n[Attachment: {att['filename']}]\n{att['content']}",
                        })
                prepared.append({"role": m.role, "content": content_list})
            else:
                prepared.append({"role": m.role, "content": m.content})
        return prepared

    def chat(
        self,
        messages: list[Message],
        system: str = "",
        attachments: list[dict] | None = None,
    ) -> LLMResponse:
        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=4096,
            system=system or anthropic.NOT_GIVEN,
            messages=self._prepare_messages(messages, attachments),
        )
        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def stream(
        self,
        messages: list[Message],
        system: str = "",
        attachments: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        with self.client.messages.stream(
            model=self.model_id,
            max_tokens=4096,
            system=system or anthropic.NOT_GIVEN,
            messages=self._prepare_messages(messages, attachments),
        ) as stream:
            for text in stream.text_stream:
                yield text


    def embed(self, text: str) -> list[float]:
        response = self._embed_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
