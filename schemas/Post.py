# schemas/post.py
from pydantic import BaseModel
from typing import Optional

class PostResponse(BaseModel):
    id: str
    id_imagen_portada: str
    outfit_id: str
    usuario_id: str
    pie_de_foto: Optional[str] = ""
    likes_count: int = 0
    
    class Config:
        from_attributes = True