import numpy as np
import json
import colorsys
from typing import Any
from schemas.OutfitMetadataAI import OutfitMetadataAI
from config import PESOS_COMPATIBILIDAD, COLOR_PRENDA, TIPO_PRENDA, EMBEDDING_PRENDA, INSPIRACION_PRENDA, OCASION_PRENDA, TEMPORADA_PRENDA
from utils.detectar_slot import detectar_slot
from utils.slots_compatibles import slots_compatibles

def hex_to_hsv(hex_color: str) -> tuple[float, float, float]: 
    '''
    Convierte un color en formato hexadecimal a modelo de color HSV (Hue, Saturation, Value).
    
    Parameters
    ----------
    hex_color : str
        Un string representando un color en hexadecimal (ej. '#FF5733' o 'FF5733').
    
    Returns
    -------
    tuple[float, float, float]
        Tupla con los valores (H, S, V) donde cada valor está normalizado entre 0.0 y 1.0.
    '''
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(x for x in colorsys.rgb_to_hsv(r, g, b)) 

def es_neutro(s: float, v: float) -> bool:
    '''
    Determina si un color se considera neutro (blanco, negro o gris) 
    basándose en su saturación y brillo.
    
    Parameters
    ----------
    s : float
        Nivel de saturación del color (0.0 a 1.0).
    v : float
        Nivel de brillo/valor del color (0.0 a 1.0).
    
    Returns
    -------
    bool
        True si el color se considera blanco, negro o gris, False en caso contrario.
    '''
    if v < 0.15:
        return True
    if v > 0.92 and s < 0.15:
        return True
    if s < 0.12:
        return True
    return False

def color_compatibility_score(hex_a: str, hex_b: str) -> float:
    '''
    Calcula una puntuación de compatibilidad armónica entre dos colores.
    
    Evalúa según las reglas de teoría del color:
        - Neutro (blanco/negro/gris) -> combina con todo (0.95)
        - Complementarios (~180°) y análogos (<=25°) -> muy recomendado (0.85 - 0.90)
        - Triádicos (~120°) -> aceptable (0.65)
        - Resto -> choque de color (0.35)
    
    Parameters
    ----------
    hex_a : str
        El primer color en formato hexadecimal.
    hex_b : str
        El segundo color en formato hexadecimal.
    
    Returns
    -------
    float
        Una puntuación de compatibilidad entre 0.0 y 1.0.
    '''
    if not hex_a or not hex_b:
        return 0.5
        
    h1, s1, v1 = hex_to_hsv(hex_a)
    h2, s2, v2 = hex_to_hsv(hex_b)
    
    if es_neutro(s1, v1) or es_neutro(s2, v2):
        return 0.95
        
    diff = abs(h1 - h2) * 360
    diff = min(diff, 360 - diff)
    
    if diff <= 25:
        return 0.85
    if 150 <= diff <= 210:
        return 0.90
    if 100 <= diff <= 140:
        return 0.65
        
    return 0.35

def score_prenda_candidata(
    color_usuario_hex: str, 
    candidata: dict[str, Any], 
    style_emb: np.ndarray | None = None
) -> float:
    '''
    Calcula una puntuación híbrida ponderada de una prenda candidata frente a 
    la prenda del usuario, combinando compatibilidad de color y similitud de estilo.

    Parameters
    ----------
    color_usuario_hex : str
        El color predominante de la imagen subida por el usuario en HEX.
    candidata : dict[str, Any]
        Diccionario (fila de BD) con los datos de la prenda a evaluar.
    style_emb : np.ndarray | None, opcional
        Vector de embedding de la imagen subida por el usuario para calcular
        la similitud coseno visual. Por defecto es None.

    Precondition
    ------------
    Las constantes COL_COLOR y PESOS_COMPATIBILIDAD deben estar definidas en config.
    
    Returns
    -------
    float
        Puntuación ponderada combinada (score) de 0.0 a 1.0.
    '''
    color_cat = candidata.get(COLOR_PRENDA)
    color_score = color_compatibility_score(color_usuario_hex, color_cat)

    style_score = 0.5
    emb_raw = candidata.get(EMBEDDING_PRENDA)

    if style_emb is not None and emb_raw is not None:
        emb = np.array(json.loads(emb_raw) if isinstance(emb_raw, str) else emb_raw, dtype=np.float32).flatten()
        emb = emb / (np.linalg.norm(emb) + 1e-8)

        # Asegurar que el embedding del usuario también es 1D y unitario
        u_emb = np.array(style_emb, dtype=np.float32).flatten()
        u_emb = u_emb / (np.linalg.norm(u_emb) + 1e-8)

        cos = float(np.dot(u_emb, emb))
        style_score = (cos + 1) / 2

    return PESOS_COMPATIBILIDAD['color'] * color_score + PESOS_COMPATIBILIDAD['estilo'] * style_score

def score_prenda_candidata_con_texto(
    prenda: dict[str, Any], 
    etiquetas: OutfitMetadataAI, 
    embedding_texto: np.ndarray | None = None
) -> float:
    '''
    Calcula una puntuación de compatibilidad (score) para una prenda candidata combinando 
    etiquetas estructuradas (LLM) y similitud semántica/visual (FashionCLIP).

    Parameters
    ----------
    prenda : dict[str, Any]
        Diccionario que representa la fila de la prenda en la base de datos (catálogo).
    etiquetas : OutfitMetadataAI
        Objeto Pydantic con las características extraídas del texto del usuario 
        mediante el modelo de lenguaje (ocasiones, temporada, colores, inspiración).
    embedding_texto : np.ndarray | None, opcional
        Vector numérico (ej. 512 dimensiones) generado por el codificador de texto 
        de FashionCLIP a partir de la consulta del usuario.

    Returns
    -------
    float
        Puntuación final normalizada entre 0.0 y 1.0, donde valores más cercanos 
        a 1.0 indican una mayor afinidad de la prenda con el texto del usuario.
    '''
    score = 0.5  # Base neutra inicial
    
    # 1. BONIFICACIÓN POR OCASIÓN (Hard Constraint del LLM)
    # Suponiendo que la prenda tiene una lista de ocasiones bajo la clave 'ocasion'
    ocasiones_prenda = prenda.get(OCASION_PRENDA, [])
    if any(o.lower() in [op.lower() for op in ocasiones_prenda] for o in etiquetas.ocasiones):
        score += 0.20

    # 2. BONIFICACIÓN POR TEMPORALIDAD (Hard Constraint del LLM)
    temporada_prenda = prenda.get(TEMPORADA_PRENDA, "").lower()
    if any(t.lower() == temporada_prenda for t in etiquetas.temporalidad):
        score += 0.15

    # 3. BONIFICACIÓN POR INSPIRACIÓN/ESTILO (Hard Constraint del LLM)
    inspiracion_prenda = prenda.get(INSPIRACION_PRENDA, [])
    if any(i.lower() in [ip.lower() for ip in inspiracion_prenda] for i in etiquetas.inspiracion):
        score += 0.10

    # (El filtrado por color exacto se podría delegar a tu función color_compatibility_score
    # o aplicarse aquí como una bonificación adicional si dispones del texto del color).

    # 4. SIMILITUD COSENO VISUAL/SEMÁNTICA (Soft Constraint vectorial)
    if embedding_texto is not None and prenda.get(EMBEDDING_PRENDA):
        # Aseguramos que el embedding de la BD sea un array NumPy
        emb_prenda = np.array(prenda[EMBEDDING_PRENDA], dtype=np.float32)
        
        # Evitar división por cero
        norm_prenda = np.linalg.norm(emb_prenda)
        if norm_prenda > 0:
            emb_prenda = emb_prenda / norm_prenda
            
            # El embedding del texto ya debería venir normalizado de la función calcular_embedding_texto
            similitud_clip = float(np.dot(embedding_texto, emb_prenda))
            
            # Bonificamos escalando la similitud vectorial (max 0.0 evita restar puntos por vectores opuestos)
            score += 0.35 * max(0.0, similitud_clip)
        
    # Asegurar que la puntuación nunca se salga del rango lógico [0, 1]
    return min(1.0, max(0.0, score))

def elegir_una_candidata(
    candidatas_con_score: list[tuple[float, dict[str, Any]]], 
    top_n: int, 
    temperatura: float
) -> tuple[float, dict[str, Any]]:
    '''
    Selecciona una prenda candidata con un muestreo pseudo-aleatorio basado en softmax.
    
    Escoge entre el top N de candidatas con una probabilidad proporcional a 
    exp(score / temperatura). Las que tienen mayor score tienen más probabilidad, 
    pero no de forma determinista para favorecer la variedad (Exploración).
    
    Parameters
    ----------
    candidatas_con_score : list[tuple[float, dict[str, Any]]]
        Lista de tuplas (score, diccionario_prenda) a evaluar.
    top_n : int
        Número máximo de prendas a considerar para la selección (recorte superior).
    temperatura : float
        Parámetro que controla la aleatoriedad (T > 1 hace que sea más equiprobable, 
        T cercano a 0 la hace determinista/codiciosa).
    
    Precondition
    ------------
    La lista 'candidatas_con_score' debe estar ordenada de forma descendiente 
    según el score previamente a la llamada.

    Returns
    -------
    tuple[float, dict[str, Any]]
        Tupla con el score original y el diccionario de la prenda seleccionada.
    '''
    top = candidatas_con_score[:top_n]
    scores = np.array([float(s) for s, _ in top], dtype=float)
    pesos = np.exp(scores / temperatura)
    pesos = pesos / pesos.sum()
    idx = np.random.choice(len(top), p=pesos)

    return top[idx]

def completar_outfit(
    tipo_prenda: str, 
    top_n: int, 
    temperatura: float, 
    color_hex: str, 
    query_emb: np.ndarray, 
    catalog: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    '''
    Genera un outfit completo y armónico a partir de una prenda base proporcionada.
    
    Busca los tipos de prendas (slots) faltantes y selecciona de forma semi-aleatoria 
    la mejor opción para cada slot evaluando tanto la teoría del color como la 
    afinidad visual (embeddings).
    
    Parameters
    ----------
    tipo_prenda : str
        Categoría o familia de la prenda inicial (ej. "pantalón", "camiseta").
    top_n : int
        Límite de prendas top a considerar para el componente aleatorio.
    temperatura : float
        Grado de creatividad o entropía en la selección de prendas afines.
    color_hex : str
        Color predominante de la prenda inicial en formato hexadecimal.
    query_emb : np.ndarray
        Vector visual extraído mediante IA de la prenda inicial.
    catalog : list[dict[str, Any]]
        Tabla de la base de datos de prendas cargada en memoria.
    
    Raises
    ------
    ValueError
        Si para algún slot requerido no hay prendas suficientes en el catálogo.
    
    Returns
    -------
    list[dict[str, Any]]
        Lista de diccionarios que conforman las prendas seleccionadas para el look final.
    '''
    prendas = slots_compatibles(tipo_prenda)
    print(prendas)

    matches = []
    for slot in prendas:
        candidatas = [
            p for p in catalog
            if detectar_slot(p.get(TIPO_PRENDA, '')) == slot
        ]
        if not candidatas:
            raise ValueError(f'  ⚠️  {slot}: sin prendas en catálogo')

        # Calculamos el score de TODAS las candidatas del slot una sola vez
        candidatas_con_score = [
            (score_prenda_candidata(color_hex, c, query_emb), c)
            for c in candidatas
        ]
        candidatas_con_score.sort(key=lambda x: x[0], reverse=True)

        _, elegida = elegir_una_candidata(candidatas_con_score, top_n, temperatura)
        matches.append(elegida)

    return matches

def completar_outfit_con_texto(
    tipo_prenda: str, 
    top_n: int, 
    temperatura: float, 
    color_hex: str, 
    query_emb: np.ndarray, 
    catalog: list[dict[str, Any]],
    etiquetas: OutfitMetadataAI | None = None,
    embedding_texto: np.ndarray | None = None
) -> list[dict[str, Any]]:
    '''
    Genera un outfit completo y armónico a partir de una prenda base proporcionada y opcionalmente
    las restricciones o preferencias de texto expresadas por el usuario.
    
    Busca los tipos de prendas (slots) faltantes y selecciona de forma semi-aleatoria 
    la mejor opción para cada slot evaluando la teoría del color, la afinidad visual (embeddings)
    y la coincidencia de metadatos/texto (si se proporcionan).
    
    Parameters
    ----------
    tipo_prenda : str
        Categoría o familia de la prenda inicial (ej. "pantalón", "camiseta").
    top_n : int
        Límite de prendas top a considerar para la selección pseudo-aleatoria (softmax).
    temperatura : float
        Grado de creatividad o entropía en la selección de prendas afines.
    color_hex : str
        Color predominante de la prenda inicial en formato hexadecimal.
    query_emb : np.ndarray
        Vector visual extraído mediante IA de la prenda inicial.
    catalog : list[dict[str, Any]]
        Tabla de la base de datos de prendas cargada en memoria.
    etiquetas : OutfitMetadataAI | None, opcional
        Metadatos estructurados extraídos de la consulta de texto mediante el LLM, por defecto None.
    embedding_texto : np.ndarray | None, opcional
        Vector de embedding generado por FashionCLIP para la consulta de texto del usuario, por defecto None.
    
    Raises
    ------
    ValueError
        Si para algún slot requerido no hay prendas suficientes en el catálogo.
    
    Returns
    -------
    list[dict[str, Any]]
        Lista de diccionarios que conforman las prendas seleccionadas para el look final.
    '''
    prendas = slots_compatibles(tipo_prenda)
    print(f"Slot base: {detectar_slot(tipo_prenda)} | Slots a completar: {prendas}")

    matches = []
    for slot in prendas:
        candidatas = [
            p for p in catalog
            if detectar_slot(p.get(TIPO_PRENDA, '')) == slot
        ]
        if not candidatas:
            raise ValueError(f'  ⚠️  {slot}: sin prendas en catálogo')

        # Calculamos el score de TODAS las candidatas del slot
        candidatas_con_score = []
        for c in candidatas:
            if etiquetas is not None or embedding_texto is not None:
                # Búsqueda/Scoring Híbrido con soporte para etiquetas LLM y embedding de texto
                score = score_prenda_candidata_con_texto(
                    prenda=c,
                    etiquetas=etiquetas,
                    embedding_texto=embedding_texto
                )
            else:
                # Scoring puramente visual y por color
                score = score_prenda_candidata(color_hex, c, query_emb)
                
            candidatas_con_score.append((score, c))

        candidatas_con_score.sort(key=lambda x: x[0], reverse=True)

        _, elegida = elegir_una_candidata(candidatas_con_score, top_n, temperatura)
        matches.append(elegida)

    return matches