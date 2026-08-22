import numpy as np
import httpx
from typing import Any
from core.api_client import cliente_api
from core.config import PRENDAS_TABLA


async def buscar_prendas_similares_pgvector(
    embedding_usuario: list[float], 
    top_n: int = 3
) -> list[dict[str, Any]] | None:
    '''
    Busca las N prendas del catálogo más similares a un vector de embedding.
    
    Llama al endpoint de la API externa que se encarga de calcular la similitud 
    visual mediante pgvector en la base de datos subyacente.

    Parameters
    ----------
    embedding_usuario : list[float]
        Vector flotante numérico que representa las características visuales.
    top_n : int, opcional
        Número de prendas más afines estéticamente a retornar, por defecto 3.

    Returns
    -------
    list[dict[str, Any]] | None
        Lista de diccionarios con la información de las prendas similares encontradas y su 
        grado de similitud/distancia, o None si ocurre un fallo de red o servidor.
    '''
    try:
        # 1. Definimos la URL de la API que hace la búsqueda vectorial.
        # NOTA: Pregunta al creador de la API cuál es la ruta exacta. 
        # Podría ser "/rpc/buscar_prendas_similares_db" o "/prendas/buscar-similares"
        url_endpoint = "/rpc/buscar_prendas_similares_db" 
        
        # 2. Preparamos el cuerpo (payload) de la petición con los mismos parámetros
        payload = {
            "vector_usuario": embedding_usuario,
            "top_n": top_n
        }
        
        # 3. Hacemos el POST asíncrono
        respuesta = await cliente_api.post(url_endpoint, json=payload)

        # 4. Comprobamos si la API devolvió un error (ej. 500 Internal Server Error)
        respuesta.raise_for_status()

        # 5. Devolvemos el JSON extraído
        return respuesta.json()

    except httpx.HTTPError as e:
        # httpx.HTTPError captura tanto errores de conexión como errores de estado HTTP
        print(f"❌ Error al realizar la búsqueda vectorial mediante la API: {e}")
        return None

async def obtener_prenda_por_id(prenda_id: str):
    """Hace un GET a la API externa para traer los datos de la prenda."""
    url = f"/{PRENDAS_TABLA}/{prenda_id}"
    respuesta = await cliente_api.get(url)
    respuesta.raise_for_status()
    return respuesta.json()

async def actualizar_prenda_por_id(prenda_id: str, datos_a_actualizar: dict):
    """Hace un PATCH a la API externa para actualizar columnas."""
    url = f"/{PRENDAS_TABLA}/{prenda_id}"
    respuesta = await cliente_api.patch(url, json=datos_a_actualizar)
    respuesta.raise_for_status()
    return respuesta.json()

############### BORRAR EN EL FUTURO
def buscar_prendas_similares(
    embedding: list[float] | np.ndarray,
    top_n: int = 3
) -> list[dict[str, Any]]:
    '''
    Busca las N prendas del catálogo en memoria más similares estéticamente a un vector dado.
    
    Utiliza el producto escalar (dot product) vectorizado con NumPy sobre los 
    embeddings precargados en RAM para lograr latencias inferiores a 2 milisegundos.

    Parameters
    ----------
    embedding_usuario : list[float] | np.ndarray
        Vector numérico (ej. de 512 dimensiones) extraído con el modelo de IA 
        que representa las características de la imagen consultada.
    top_n : int, opcional
        Número de resultados más similares a devolver, por defecto 3.

    Precondition
    ------------
    La función `cargar_tabla_memoria` debe haber devuelto exitosamente la lista del 
    catálogo y la matriz bidimensional de embeddings (N x 512). Si no, devuelve una lista vacía.

    Returns
    -------
    list[dict[str, Any]]
        Lista de diccionarios. Cada diccionario es una copia exacta del registro de 
        la prenda original en el catálogo, añadiendo una nueva clave 'similitud' 
        (float) que indica el grado de coincidencia matemática.
    '''
    if not catalogo or matriz_embeddings is None:
        return []

    # 1. Asegurar que el vector del usuario sea un array unitario float32 de 1x512
    vec_usr = np.array(embedding, dtype=np.float32)
    norma_usr = np.linalg.norm(vec_usr)
    if norma_usr > 0:
        vec_usr = vec_usr / norma_usr

    # 2. CÁLCULO VECTORIZADO INSTANTÁNEO (< 2 milisegundos):
    # Multiplicamos la matriz (N x 512) por el vector del usuario (512,)
    similitudes = np.dot(matriz_embeddings, vec_usr)

    # 3. Obtener los índices con mayores puntuaciones (Top N)
    # np.argsort ordena de menor a mayor, tomamos los últimos top_n y los invertimos
    top_indices = np.argsort(similitudes)[-top_n:][::-1]

    # 4. Construir la respuesta con los diccionarios del catálogo original
    resultados = []
    for idx in top_indices:
        prenda_copia = dict(catalogo[idx])
        prenda_copia["similitud"] = float(similitudes[idx])
        resultados.append(prenda_copia)

    return resultados