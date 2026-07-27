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

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument] = []

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
    accuracy: str
    response_time: str
    engine: str
