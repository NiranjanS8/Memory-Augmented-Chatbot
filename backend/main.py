import asyncio
import base64
import json
import logging

from fastapi import FastAPI, Depends, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from backend.auth.jwt import create_jwt, get_current_user
from backend.auth.users import AuthStore, User
from backend.config import settings, get_model
from backend.conversations.store import ConversationStore
from backend.memory.manager import MemoryManager
from backend.models.base import Message
from backend.prompts.system import build_system_prompt
from backend.schemas import (
    ChatBody,
    LoginBody,
    RegisterBody,
    RenameBody,
    TokenResponse,
    UploadResult,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Memory-Augmented Chatbot",
    description="A multi-model chatbot with persistent cross-session memory",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_auth_store = AuthStore()
_conv_store = ConversationStore()
_memory_managers: dict[str, MemoryManager] = {}


def _get_memory_manager(user_id: str) -> MemoryManager:
    if user_id not in _memory_managers:
        _memory_managers[user_id] = MemoryManager(user_id)
    return _memory_managers[user_id]




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




@app.post("/api/auth/register", response_model=TokenResponse)
async def register(body: RegisterBody):
    try:
        user = _auth_store.register(body.email, body.password, body.display_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = create_jwt(user)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
    )


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(body: LoginBody):
    try:
        user = _auth_store.login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    token = create_jwt(user)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
    )




@app.get("/api/conversations")
async def list_conversations(user: User = Depends(get_current_user)):
    convs = _conv_store.list_conversations(user.id)
    return [c.model_dump() for c in convs]


@app.post("/api/conversations")
async def create_conversation(user: User = Depends(get_current_user)):
    conv = _conv_store.create_conversation(user.id, "New conversation", settings.DEFAULT_MODEL)
    return conv.model_dump()


@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str, user: User = Depends(get_current_user)):
    conv = _conv_store.get_conversation(conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv.model_dump()


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user: User = Depends(get_current_user)):
    conv = _conv_store.get_conversation(conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    _conv_store.delete_conversation(conv_id)
    return {"deleted": conv_id}


@app.patch("/api/conversations/{conv_id}")
async def rename_conversation(
    conv_id: str, body: RenameBody, user: User = Depends(get_current_user),
):
    conv = _conv_store.get_conversation(conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    _conv_store.rename_conversation(conv_id, body.title)
    return {"id": conv_id, "title": body.title}


@app.get("/api/conversations/{conv_id}/messages")
async def get_messages(conv_id: str, user: User = Depends(get_current_user)):
    conv = _conv_store.get_conversation(conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conv_store.load_messages(conv_id)




@app.post("/api/chat/stream")
async def chat_stream(body: ChatBody, user: User = Depends(get_current_user)):
    memory_mgr = _get_memory_manager(user.id)

    conv_id = body.conversation_id
    if not conv_id:
        conv = _conv_store.create_conversation(user.id, body.message, body.model)
        conv_id = conv.id
        asyncio.create_task(_conv_store.auto_title(conv_id, body.message))

    if body.messages:
        chat_messages = [Message(role=m["role"], content=m["content"]) for m in body.messages]
    else:
        stored = _conv_store.load_messages(conv_id)
        chat_messages = [Message(role=m["role"], content=m["content"]) for m in stored]

    chat_messages.append(Message(role="user", content=body.message))

    async def generate():
        memories = []
        try:
            memories = memory_mgr.get_context(body.message)
        except Exception as e:
            logger.warning("Memory retrieval failed: %s", e)

        serialized_memories = [
            {"content": m.content, "type": m.memory_type.value}
            for m in memories
        ]
        yield json.dumps({"type": "memory", "data": serialized_memories, "conversation_id": conv_id})

        system_prompt = build_system_prompt(memories, body.model)

        try:
            llm = get_model(body.model)
        except ValueError as e:
            yield json.dumps({"type": "error", "data": str(e)})
            return

        full_response = ""
        try:
            for chunk in llm.stream(chat_messages, system=system_prompt):
                full_response += chunk
                yield json.dumps({"type": "chunk", "data": chunk})
        except Exception as e:
            logger.error("LLM stream error (%s): %s", body.model, e)
            yield json.dumps({"type": "error", "data": f"Model error: {e}"})
            return

        yield json.dumps({"type": "done", "data": ""})

        _conv_store.append_message(conv_id, "user", body.message)
        _conv_store.append_message(conv_id, "assistant", full_response)

        asyncio.create_task(
            memory_mgr.save_turn(body.message, full_response, source_session=conv_id)
        )

    return EventSourceResponse(generate())




@app.get("/api/memory")
async def list_memories(user: User = Depends(get_current_user)):
    mgr = _get_memory_manager(user.id)
    records = mgr.list_memories()
    return [
        {
            "id": r.id,
            "content": r.content,
            "type": r.memory_type.value,
            "confidence": r.confidence,
            "access_count": r.access_count,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@app.delete("/api/memory")
async def clear_memories(user: User = Depends(get_current_user)):
    mgr = _get_memory_manager(user.id)
    mgr.clear_memories()
    return {"cleared": True}




@app.post("/api/upload", response_model=UploadResult)
async def upload_file(file: UploadFile, user: User = Depends(get_current_user)):
    content_bytes = await file.read()
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("png", "jpg", "jpeg", "gif", "webp"):
        encoded = base64.b64encode(content_bytes).decode()
        return UploadResult(
            type="image",
            content=encoded,
            filename=filename,
            media_type=f"image/{ext}",
        )

    if ext == "pdf":
        try:
            import pypdf
            import io
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            text = f"[PDF parsing failed: {e}]"
        return UploadResult(type="text", content=f"[PDF: {filename}]\n{text}", filename=filename)

    if ext == "csv":
        try:
            import pandas as pd
            import io
            df = pd.read_csv(io.BytesIO(content_bytes))
            text = df.to_markdown(index=False)
        except Exception as e:
            text = f"[CSV parsing failed: {e}]"
        return UploadResult(type="text", content=f"[CSV: {filename}]\n{text}", filename=filename)

    try:
        text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = f"[Binary file: {filename}, {len(content_bytes)} bytes]"
    return UploadResult(type="text", content=f"[File: {filename}]\n{text}", filename=filename)
