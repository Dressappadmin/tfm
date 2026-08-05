from datetime import datetime, timezone
import numpy as np
from typing import List, Dict, Any, Optional, Set

def similitud_coseno(vec_a: Optional[List[float]], vec_b: Optional[List[float]]) -> float:
    """Calcula la similitud coseno entre dos vectores."""
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
    """Calcula el éxito viral penalizando el tiempo transcurrido (Time Decay)."""
    fecha_post = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
    ahora = datetime.now(timezone.utc)
    horas = max(0.0, (ahora - fecha_post).total_seconds() / 3600.0)
    
    interacciones = likes + (reposts * 2.0) + (comentarios * 1.5)
    return float(interacciones / ((horas + 2.0) ** gravedad))

def calcular_afinidad_social(
    autor_id: str,
    seguidos_directos: Set[str],
    amigos_segundo_grado: Set[str],
    autores_guardados: Set[str]
) -> float:
    """Asigna el peso social según el nivel de proximidad en el grafo."""
    if autor_id in seguidos_directos:
        return 1.0
    elif autor_id in amigos_segundo_grado:
        return 0.6
    elif autor_id in autores_guardados:
        return 0.3
    return 0.0

def aplicar_deduplicacion_y_exploracion(
    candidatos_explotacion: List[Dict[str, Any]],
    candidatos_exploracion: List[Dict[str, Any]],
    tamano_feed: int = 20
) -> List[Dict[str, Any]]:
    """
    Construye el feed final aplicando:
    1. Deduplicación de autores (máx 2 por feed, nunca consecutivos).
    2. Inyección e-Greedy en los slots 4 y 14 (posiciones 5 y 15).
    """
    feed_final: List[Dict[str, Any]] = []
    conteo_autores: Dict[str, int] = {}
    slots_exploracion = {4, 14}
    
    idx_explotacion = 0
    idx_exploracion = 0
    
    while len(feed_final) < tamano_feed:
        posicion_actual = len(feed_final)
        candidato_seleccionado = None
        
        # 1. INYECCIÓN DE EXPLORACIÓN (Slots 5 y 15)
        if posicion_actual in slots_exploracion and idx_exploracion < len(candidatos_exploracion):
            candidato_seleccionado = candidatos_exploracion[idx_exploracion]
            idx_exploracion += 1
        
        # 2. SELECCIÓN DE EXPLOTACIÓN (Resto de slots)
        if not candidato_seleccionado and idx_explotacion < len(candidatos_explotacion):
            # Buscamos el siguiente candidato que cumpla la deduplicación
            while idx_explotacion < len(candidatos_explotacion):
                cand = candidatos_explotacion[idx_explotacion]
                autor = cand.get("autor_id", "")
                
                # Regla: Máximo 2 posts por autor en el feed
                supera_maximo = conteo_autores.get(autor, 0) >= 2
                # Regla: No permitir el mismo autor que la posición inmediatamente anterior
                es_consecutivo = (len(feed_final) > 0 and feed_final[-1].get("autor_id") == autor)
                
                idx_explotacion += 1
                
                if not supera_maximo and not es_consecutivo:
                    candidato_seleccionado = cand
                    break
        
        # Si no quedan candidatos válidos, rompemos el bucle
        if not candidato_seleccionado:
            break
            
        autor_sel = candidato_seleccionado.get("autor_id", "")
        conteo_autores[autor_sel] = conteo_autores.get(autor_sel, 0) + 1
        feed_final.append(candidato_seleccionado)
        
    return feed_final

def generar_feed_personalizado(
    candidatos: List[Dict[str, Any]], 
    embedding_usuario: Optional[List[float]],
    seguidos_directos: Set[str],
    amigos_segundo_grado: Set[str],
    autores_guardados: Set[str],
    temporada_actual: str,
    pesos: Dict[str, float] = {"w1": 0.40, "w2": 0.30, "w3": 0.20, "w4": 0.10}
) -> List[Dict[str, Any]]:
    """
    Pipeline principal: puntúa candidatos, separa en explotación vs exploración
    y construye el feed optimizado.
    """
    if not embedding_usuario:
        pesos = {"w1": 0.00, "w2": 0.60, "w3": 0.20, "w4": 0.20}

    # Normalización del score viral
    scores_virales = [
        calcular_viralidad_temporal(
            p.get("likes_count", 0),
            p.get("reposts_count", 0),
            p.get("comentarios_count", 0),
            p.get("created_at", datetime.now(timezone.utc).isoformat())
        )
        for p in candidatos
    ]
    max_viral = max(scores_virales) if scores_virales and max(scores_virales) > 0 else 1.0

    candidatos_puntuados = []
    
    for i, post in enumerate(candidatos):
        score_visual = similitud_coseno(embedding_usuario, post.get("outfit_embedding"))
        score_viral_norm = scores_virales[i] / max_viral
        score_social = calcular_afinidad_social(
            post.get("autor_id", ""),
            seguidos_directos,
            amigos_segundo_grado,
            autores_guardados
        )
        score_contexto = 1.0 if temporada_actual in post.get("temporalidades", []) else 0.0

        score_total = (
            pesos["w1"] * score_visual +
            pesos["w2"] * score_viral_norm +
            pesos["w3"] * score_social +
            pesos["w4"] * score_contexto
        )

        post_data = post.copy()
        post_data["score_recomendacion"] = round(float(score_total), 4)
        post_data["score_viral_norm"] = round(float(score_viral_norm), 4)
        post_data["score_social"] = score_social
        candidatos_puntuados.append(post_data)

    # SEPARACIÓN: Explotación (mayor puntuación general) vs Exploración (alta viralidad, sin afinidad social ni visual alta)
    candidatos_explotacion = sorted(
        candidatos_puntuados, key=lambda x: x["score_recomendacion"], reverse=True
    )
    
    candidatos_exploracion = sorted(
        [
            p for p in candidatos_puntuados 
            if p["score_social"] == 0.0 and p.get("autor_id") not in seguidos_directos
        ],
        key=lambda x: x["score_viral_norm"],
        reverse=True
    )

    return aplicar_deduplicacion_y_exploracion(candidatos_explotacion, candidatos_exploracion, tamano_feed=20)