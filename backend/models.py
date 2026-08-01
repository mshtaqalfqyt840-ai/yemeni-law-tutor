from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = []
    prompt: str


class SourceDocument(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}


class RagStats(BaseModel):
    retrieved_count: int
    response_time: str
    source_verified: bool = True
    engine: str = "ChromaDB + Gemini Flash"
    status: str = "موثّق بسجل القانون المدني (2002م)"


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument] = []
    rag_stats: Optional[RagStats] = None


class SuggestionItem(BaseModel):
    id: str
    category: str
    title: str
    subtext: str
    prompt: str
    btn_label: str
    svg_icon: str
    accent_class: str


class SystemStats(BaseModel):
    total_docs: int
    status: str
    accuracy: str = "100%"
    verification_status: Optional[str] = "موثّق بسجل القانون المدني"
    response_time: str
    engine: str


class APIKeyRequest(BaseModel):
    api_key: str


class APIKeyResponse(BaseModel):
    success: bool
    message: str
