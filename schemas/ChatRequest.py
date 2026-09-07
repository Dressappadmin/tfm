from pydantic import BaseModel
from typing import List, Optional, Literal

class MensajeChat(BaseModel):
    # Restringimos estrictamente los roles permitidos desde el cliente
    role: Literal["user", "assistant"] 
    content: str

class ChatRequest(BaseModel):
    usuario_id: str
    mensajes: List[MensajeChat]
    # Lo cambiamos a List[str] para que encaje con el cambio anterior
    contexto_prenda_id: Optional[List[str]] = None