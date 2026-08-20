from pydantic import BaseModel, Field

class ConfirmarGuardadoRequest(BaseModel):
    '''
    Esquema que recibe la decisión del usuario sobre el outfit generado.
    '''
    guardar: bool = Field(
        ..., 
        description="True si el usuario quiere guardar el outfit. False si no le gusta y lo descarta."
    )
    ids_outfit: list[int | str] = Field(
        ..., 
        description="La lista completa de IDs (incluyendo la prenda subida) que componen el outfit."
    )
    usuario_id: str | None = Field(
        default=None, 
        description="ID del usuario propietario del outfit en la base de datos."
    )