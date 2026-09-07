from pydantic import BaseModel, Field, field_validator
from typing import List
from utils.catalogos import VOCABULARIO_TAGS

class GenerarOutfitRequest(BaseModel):
    usuario_id: str
    
    prendas_input: List[str] = Field(
        default_factory=list, 
        json_schema_extra={"example": ["uuid-camiseta-123", "uuid-pantalon-456"]}
    )
    
    tags: List[str] = Field(
        default_factory=list, 
        json_schema_extra={"example": ["Casual", "Invierno"]}
    )

    # FastAPI bloqueará cualquier etiqueta inventada
    @field_validator('tags')
    def validar_tags(cls, lista_tags):
        for tag in lista_tags:
            if tag not in VOCABULARIO_TAGS:
                raise ValueError(f"Etiqueta no válida: '{tag}'. Solo se permiten: {VOCABULARIO_TAGS}")
        return lista_tags