from pydantic import BaseModel, EmailStr


class RegisterBody(BaseModel):
    email: str
    password: str
    display_name: str = ""


class LoginBody(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    display_name: str


class ChatBody(BaseModel):
    message: str
    conversation_id: str | None = None
    model: str = "openai"
    messages: list[dict] | None = None


class RenameBody(BaseModel):
    title: str


class SpeakBody(BaseModel):
    text: str
    voice: str = "alloy"


class UploadResult(BaseModel):
    type: str
    content: str | None = None
    filename: str
    media_type: str | None = None
