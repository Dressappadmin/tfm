from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class MensajeChat(BaseModel):
    role: str # 'user', 'assistant' o 'system'
    content: str

class ChatRequest(BaseModel):
    usuario_id: str
    mensajes: List[MensajeChat]
    # Opcional: Si el usuario ya está viendo una prenda en la app y dice "combíname esto"
    contexto_prenda_id: Optional[Dict[str, str]] = None