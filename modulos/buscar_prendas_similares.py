from typing import Any
import numpy as np
from data.catalogos import prendas as catalogo, embeddings_prendas as matriz_embeddings

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