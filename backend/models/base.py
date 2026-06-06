from abc import ABC, abstractmethod
from collections.abc import Generator
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMClient(ABC):
    model_id: str
    display_name: str
    max_context_tokens: int

    @abstractmethod
    def chat(self, messages: list[Message], system: str = "") -> LLMResponse:
        ...

    @abstractmethod
    def stream(self, messages: list[Message], system: str = "") -> Generator[str, None, None]:
        ...

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        ...
