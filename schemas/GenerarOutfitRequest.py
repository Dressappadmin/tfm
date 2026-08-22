# schemas/GenerarOutfitRedRequest.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class GenerarOutfitRequest(BaseModel):
    # Diccionario donde la key es el SLOT ('SUPERIOR', 'INFERIOR', etc.) 
    # y el value es el ID de la prenda en la base de datos
    prendas_input: Dict[str, str] = Field(
        ..., example={"SUPERIOR": "uuid-camiseta-123", "INFERIOR": "uuid-pantalon-456"}
    )
    # IDs de las prendas con las que el usuario interactuó últimamente (likes/guardados)
    historial_usuario_ids: List[str] = Field(default=[])
    # El prompt libre del usuario
    texto: Optional[str] = None