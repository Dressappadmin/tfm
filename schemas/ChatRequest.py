from pydantic import BaseModel
from typing import List, Optional, Literal

class MensajeChat(BaseModel):
    role: Literal["user", "assistant"] 
    content: str

class ChatRequest(BaseModel):
    usuario_id: str
    mensajes: List[MensajeChat]
    contexto_prenda_id: Optional[List[str]] = None