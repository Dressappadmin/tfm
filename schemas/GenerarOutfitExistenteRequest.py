# schemas/outfits.py
from pydantic import BaseModel, Field

class GenerarOutfitExistenteRequest(BaseModel):
    prenda_id: int | str = Field(..., description="ID de la prenda seleccionada del perfil")
    texto: str | None = Field(None, description="Instrucción adicional opcional (ej: 'para una boda')")