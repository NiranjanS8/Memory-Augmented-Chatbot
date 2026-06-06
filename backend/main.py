from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings

app = FastAPI(
    title="Memory-Augmented Chatbot",
    description="A multi-model chatbot with persistent cross-session memory",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "default_model": settings.DEFAULT_MODEL}


@app.get("/")
async def root():
    return {
        "message": "Memory-Augmented Chatbot API",
        "docs": "/docs",
        "health": "/health",
    }
