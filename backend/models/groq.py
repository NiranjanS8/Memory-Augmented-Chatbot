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

    def _build_messages(
        self,
        messages: list[Message],
        system: str,
        attachments: list[dict] | None = None,
    ) -> list[dict]:
        out = []
        if system:
            out.append({"role": "system", "content": system})

        for i, m in enumerate(messages):
            if i == len(messages) - 1 and m.role == "user" and attachments:
                content_list = [{"type": "text", "text": m.content}]
                for att in attachments:
                    if att["type"] == "image":
                        content_list.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{att.get('media_type') or 'image/jpeg'};base64,{att['content']}"
                            }
                        })
                    elif att["type"] == "text":
                        content_list.append({
                            "type": "text",
                            "text": f"\n\n[Attachment: {att['filename']}]\n{att['content']}"
                        })
                out.append({"role": m.role, "content": content_list})
            else:
                out.append({"role": m.role, "content": m.content})
        return out

    def chat(
        self,
        messages: list[Message],
        system: str = "",
        attachments: list[dict] | None = None,
    ) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=self._build_messages(messages, system, attachments),
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )

    def stream(
        self,
        messages: list[Message],
        system: str = "",
        attachments: list[dict] | None = None,
    ) -> Generator[str, None, None]:
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=self._build_messages(messages, system, attachments),
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
