from typing import Any
import numpy as np

def buscar_prendas_similares(
    embedding: np.ndarray | list[float],
    catalog: list[dict[str, Any]],
    top_k: int = 3,
    familia_filtro: str | None = None
) -> list[dict[str, Any]]:
    '''
    Dado el embedding de una imagen busca en la bd el top_k de prendas similares a ella.
    
    Parameters
    ----------
    embedding: el embedding de la imagen
    catalog: la lista de prendas en bd
    top_k: el top de prendas a mostrar
    familia_filtro: la familia de la prenda
    
    Precondition
    ------------
    -
    
    Returns
    -------
    los ids de las imágenes que son más similares
    '''
    if not catalog:
        return []

    # 1. Convertir, aplanar y normalizar el vector del usuario (u)
    u = np.asarray(embedding, dtype=np.float32).flatten()
    norma_u = np.linalg.norm(u)
    if norma_u == 0:
        return []
    u_normalizado = u / norma_u

    candidatas_evaluadas = []

    # 2. Recorrer el catálogo y calcular similitud
    for prenda in catalog:

        # Filtro opcional por familia o categoría
        if familia_filtro and prenda.get("family") != familia_filtro:
            continue

        vec_prenda = prenda.get("embedding")
        if vec_prenda is None:
            continue

        # Convertir a numpy array si viene como lista desde Supabase
        v = np.asarray(vec_prenda, dtype=np.float32).flatten()
        norma_v = np.linalg.norm(v)
        if norma_v == 0:
            continue

        v_normalizado = v / norma_v

        # Producto escalar = Similitud Coseno (entre -1.0 y 1.0)
        similitud = float(np.dot(u_normalizado, v_normalizado))

        # Creamos una copia del dict con la puntuación añadida
        prenda_con_score = dict(prenda)
        prenda_con_score["similitud"] = round(similitud, 4)
        candidatas_evaluadas.append(prenda_con_score)

    # 3. Ordenar de mayor a menor similitud y devolver el Top K
    candidatas_evaluadas.sort(key=lambda x: x["similitud"], reverse=True)
    return candidatas_evaluadas[:top_k]