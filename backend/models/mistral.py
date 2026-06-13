from collections.abc import Generator

from mistralai.client.sdk import Mistral

from backend.config import settings
from backend.models.base import LLMClient, LLMResponse, Message


class MistralClient(LLMClient):
    model_id = "mistral-large-latest"
    display_name = "Mistral Large"
    max_context_tokens = 32_000

    def __init__(self):
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)

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
        response = self.client.chat.complete(
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
        response = self.client.chat.stream(
            model=self.model_id,
            messages=self._build_messages(messages, system, attachments),
        )
        for event in response:
            delta = event.data.choices[0].delta
            if delta.content:
                yield delta.content


    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model="mistral-embed",
            inputs=[text],
        )
        return response.data[0].embedding
