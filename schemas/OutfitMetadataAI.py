from pydantic import BaseModel, Field

class OutfitMetadataAI(BaseModel):
    # --- Atributos Core (Usados tanto en Búsqueda como en Posts) ---
    ocasiones: list[str] = Field(
        default_factory=list, 
        description="1 o 2 ocasiones ideales: casual, business, party, sport, boda, etc."
    )
    temporalidad: list[str] = Field(
        default_factory=list, 
        description="Época del año: verano, invierno, entretiempo, primavera, otoño"
    )
    inspiracion: list[str] = Field(
        default_factory=list, 
        description="Estilo estético: minimal, old money, y2k, streetwear, chic, boho, etc."
    )
    
    # --- Atributos de Búsqueda (Principalmente para el motor híbrido) ---
    colores: list[str] = Field(
        default_factory=list, 
        description="Colores o tonos explícitamente mencionados (ej. azul, negro, claro, pastel)"
    )
    prenda_mencionada: str | None = Field(
        default=None, 
        description="Si el usuario menciona una prenda base inicial (ej. 'pantalon vaquero', 'vestido')"
    )

    # --- Atributos de Presentación (Exclusivos para generar Posts) ---
    titulo: str | None = Field(
        default=None, 
        description="Título corto de 3 a 5 palabras, elegante y comercial"
    )
    descripcion_catchy: str | None = Field(
        default=None, 
        description="Copy para redes sociales de 15-20 palabras con un emoji al final"
    )
