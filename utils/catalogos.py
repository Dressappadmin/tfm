import numpy as np
from typing import Any

from supabase import create_client, Client

# Importamos las constantes limpias de config.py
from config import SUPABASE_URL, SUPABASE_KEY

# 1. Creamos el cliente centralizado aquí (en minúsculas, como estándar)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

from config import PRENDAS_TABLA, EMBEDDING_PRENDA
from data.cargar_tabla_memoria import cargar_tabla_memoria

print("Inicializando catálogo en memoria global...")

prendas, embeddings_prendas = cargar_tabla_memoria(PRENDAS_TABLA, embedding=EMBEDDING_PRENDA)


############################

PESOS_COMPATIBILIDAD = {'color': 0.6, 'estilo': 0.4}

CATEGORIAS = [
    'abrigo', 'anorak', 'bambas', 'bañador', 'bermuda', 'bisuteria',
    'blazer', 'body', 'bolso', 'bota plana', 'bota tacon', 'botin plano',
    'botin tacon', 'camisa', 'camiseta', 'cazadora', 'chaleco', 'chaqueta',
    'cinturon', 'falda', 'gabardina', 'impermeable', 'jersey', 'leggings',
    'mono', 'pantalon', 'pañuelo', 'peto', 'running', 'sandalia plana',
    'sandalia tacon', 'short', 'sudadera', 'top', 'vestido',
    'zapato plano', 'zapato tacon'
]

SLOTS = { 
    'SUPERIOR':        ['camiseta', 'camisa', 'top', 'jersey', 'sudadera', 'body', 'chaleco'],
    'INFERIOR':        ['pantalon', 'falda', 'short', 'bermuda', 'leggings'],
    'CUERPO_COMPLETO': ['vestido', 'mono', 'peto', 'bañador'],
    'ABRIGO':          ['abrigo', 'anorak', 'chaqueta', 'cazadora', 'gabardina', 'impermeable', 'blazer'],
    'CALZADO':         ['bambas', 'bota plana', 'bota tacon', 'botin plano', 'botin tacon', 'zapato tacon'],
    'ACCESORIO':       ['bisuteria', 'bolso', 'cinturon', 'pañuelo', 'sombrero'],
}

TODOS_LOS_SLOTS = list(SLOTS.keys())

SLOT_INDEX = {slot: indice for indice, slot in enumerate(TODOS_LOS_SLOTS)}

TOP_K = 5

# ==========================================
# DRESSCHAT
# ==========================================
# Definimos el vocabulario global de tu red. 
# Si tu LLM devuelve etiquetas, DEBEN coincidir con estas (puedes ajustar el prompt del LLM para forzarlo).
VOCABULARIO_TAGS = [
    # Ocasión
    'casual', 'formal', 'fiesta', 'deporte',
    # Temporalidad
    'verano', 'invierno', 'entretiempo',
    # Inspiración
    'minimalista', 'urbano', 'boho', 'y2k',
    # Materiales
    'algodon', 'denim', 'cuero', 'lino',
    # Precio Máximo
    'barato', 'medio', 'caro'
]

# En este ejemplo tenemos 18 etiquetas, por lo que num_tags=18 en tu red neuronal.
NUM_TAGS = len(VOCABULARIO_TAGS)