import numpy as np
from typing import Any
from .supabase import supabase

def cargar_tabla_memoria(tabla: str, embedding: str = None) -> tuple[list[dict[str, Any]], np.ndarray | None]:
    """
    Descarga el catálogo desde Supabase de forma controlada en el arranque
    y construye la matriz NumPy para búsqueda vectorial en < 2 ms.
    Cargamos el catálogo en memoria.

    Parameters
    ----------
    tabla : str
        El nombre de la tabla a cargar en memoria

    Returns
    -------
    tuple[list[dict[str, Any]], np.ndarray | None]
        Una tupla donde el primer elemento es la lista de diccionarios del catálogo,
        y el segundo es la matriz de embeddings en formato NumPy.
    """

    try:
        print(f"📦 Descargando catálogo desde la tabla '{tabla}'...")
        respuesta = supabase.table(tabla).select('*').execute()
        catalogo = respuesta.data
        
        if not catalogo:
            print("⚠️ La tabla está vacío.")
            return [], None

        # Construcción de la matriz NumPy (N x 512)
        if embedding:
            embeddings_list = [
                item.get(embedding) if (item.get(embedding) and len(item.get(embedding)) == 512)
                else [0.0] * 512
                for item in catalogo
            ]
            matriz_embeddings = np.array(embeddings_list, dtype=np.float32)

        else:
            print('No hay matriz de embeddings')
            embeddings_list = [[np.nan] * 512 for _ in catalogo]

            matriz_embeddings = np.array(embeddings_list, dtype=np.float32)
        
        print(f"✅ Tabla en RAM: {len(catalogo)} filas | Matriz: {matriz_embeddings.shape}")
        return catalogo, matriz_embeddings

    except Exception as e:
        print(f"❌ Error al cargar la tabla: {str(e)}")
        return [], None