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

    temperatura: float = Field(
        default=0.5, 
        ge=0.1, 
        le=2.0, 
        description="Controla la creatividad del outfit. 0.1 es muy conservador, 1.0+ es muy creativo.",
        json_schema_extra={"example": 0.7}
    )

    @field_validator('tags')
    def validar_tags(cls, lista_tags):
        for tag in lista_tags:
            if tag not in VOCABULARIO_TAGS:
                raise ValueError(f"Etiqueta no válida: '{tag}'. Solo se permiten: {VOCABULARIO_TAGS}")
        return lista_tags