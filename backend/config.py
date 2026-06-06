import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    VECTOR_STORE: str = os.getenv("VECTOR_STORE", "chroma")
    CHROMA_STORE_PATH: str = os.getenv("CHROMA_STORE_PATH", ".chroma_store")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "change_this_in_production")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")

    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "claude")

    PROVIDER_KEYS: dict[str, str] = {}

    def __init__(self):
        self.PROVIDER_KEYS = {
            "Anthropic (Claude)": self.ANTHROPIC_API_KEY,
            "OpenAI (GPT-4o)": self.OPENAI_API_KEY,
            "Google (Gemini)": self.GOOGLE_API_KEY,
            "Mistral": self.MISTRAL_API_KEY,
            "Groq": self.GROQ_API_KEY,
        }


MODEL_REGISTRY: dict[str, type] = {}


def get_model(name: str):
    if name not in MODEL_REGISTRY:
        available = list(MODEL_REGISTRY.keys()) or ["(none registered)"]
        raise ValueError(f"Unknown model: {name}. Available: {available}")
    return MODEL_REGISTRY[name]()


settings = Settings()
