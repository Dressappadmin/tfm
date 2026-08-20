from datetime import datetime, timezone
import numpy as np
from typing import Any

def similitud_coseno(vec_a: list[float] | None, vec_b: list[float] | None) -> float:
    '''
    Calcula la similitud matemática (coseno) entre dos vectores de características.
    
    Parameters
    ----------
    vec_a : list[float] | None
        Primer vector (ej. embedding del perfil de estilo del usuario).
    vec_b : list[float] | None
        Segundo vector (ej. embedding del outfit de un post candidato).
        
    Returns
    -------
    float
        Valor de similitud. Mayor a 0 indica similitud, 0 si falta algún vector.
    '''
    if not vec_a or not vec_b:
        return 0.0
    return float(np.dot(vec_a, vec_b))

def calcular_viralidad_temporal(
    likes: int, 
    reposts: int, 
    comentarios: int, 
    created_at_iso: str,
    gravedad: float = 1.5
) -> float:
    '''
    Calcula el éxito viral de un post penalizando el tiempo transcurrido (Time Decay).
    
    Utiliza una fórmula inspirada en el algoritmo de Hacker News, donde las 
    interacciones recientes valen más que las antiguas para garantizar un feed fresco.
    
    Parameters
    ----------
    likes : int
        Número de "me gusta" del post.
    reposts : int
        Número de veces que el post ha sido guardado/compartido (peso x2.0).
    comentarios : int
        Cantidad de comentarios en el post (peso x1.5).
    created_at_iso : str
        Fecha de creación del post en formato ISO 8601 (ej. "2024-05-12T14:30:00Z").
    gravedad : float, opcional
        Exponente de decaimiento temporal. A mayor gravedad, más rápido pierden 
        relevancia los posts antiguos. Por defecto 1.5.
        
    Returns
    -------
    float
        Puntuación de viralidad ajustada por frescura temporal.
    '''
    fecha_post = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
    ahora = datetime.now(timezone.utc)
    horas = max(0.0, (ahora - fecha_post).total_seconds() / 3600.0)
    
    interacciones = likes + (reposts * 2.0) + (comentarios * 1.5)
    return float(interacciones / ((horas + 2.0) ** gravedad))

def calcular_afinidad_social(
    autor_id: str,
    seguidos_directos: set[str],
    amigos_segundo_grado: set[str],
    autores_guardados: set[str]
) -> float:
    '''
    Asigna un peso social a un post según la proximidad del autor en el grafo de red.
    
    Parameters
    ----------
    autor_id : str
        ID del creador del post candidato.
    seguidos_directos : set[str]
        Conjunto de IDs de usuarios a los que el usuario actual sigue directamente.
    amigos_segundo_grado : set[str]
        Conjunto de IDs de usuarios que son seguidos por los contactos del usuario.
    autores_guardados : set[str]
        Conjunto de IDs de autores con los que el usuario ha interactuado antes.
        
    Returns
    -------
    float
        Puntuación social: 1.0 (Directo), 0.6 (2º grado), 0.3 (Histórico), o 0.0 (Desconocido).
    '''
    if autor_id in seguidos_directos:
        return 1.0
    elif autor_id in amigos_segundo_grado:
        return 0.6
    elif autor_id in autores_guardados:
        return 0.3
    return 0.0

def aplicar_deduplicacion_y_exploracion(
    candidatos_explotacion: list[dict[str, Any]],
    candidatos_exploracion: list[dict[str, Any]],
    tamano_feed: int = 20
) -> list[dict[str, Any]]:
    '''
    Construye el feed final aplicando reglas de negocio y el algoritmo ε-Greedy.
    
    Garantiza diversidad limitando los autores y reserva slots fijos para introducir
    contenido nuevo (exploración) que rompa la burbuja de filtro (Filter Bubble).
    
    Parameters
    ----------
    candidatos_explotacion : list[dict[str, Any]]
        Posts ordenados por la mayor puntuación de recomendación (afinidad + viralidad).
    candidatos_exploracion : list[dict[str, Any]]
        Posts muy virales de autores desconocidos para el usuario.
    tamano_feed : int, opcional
        Número total de posts a devolver, por defecto 20.
        
    Returns
    -------
    list[dict[str, Any]]
        Lista de posts seleccionados para el feed, cumpliendo con la deduplicación 
        (máx. 2 posts del mismo autor, nunca consecutivos) y con inyección exploratoria.
    '''
    feed_final: list[dict[str, Any]] = []
    conteo_autores: dict[str, int] = {}
    slots_exploracion = {4, 14}  # Posiciones 5 y 15 (índices 0-based)
    
    idx_explotacion = 0
    idx_exploracion = 0
    
    while len(feed_final) < tamano_feed:
        posicion_actual = len(feed_final)
        candidato_seleccionado = None
        
        # 1. INYECCIÓN