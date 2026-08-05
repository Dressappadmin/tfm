import numpy as np
import json
import colorsys
from config import COL_COLOR, COL_FAMILY, PESOS_COMPATIBILIDAD, SLOTS

def detectar_slot(prenda: str, dic: dict = SLOTS) -> str:

    '''
    Dado un tipo de prenda, detecta su correspondiente slot
    
    Parameters
    ----------
    prenda: tipo de prenda
    dic: el diccionario que contiene a que slot pertenece cada prenda
    
    Precondition
    ------------
    SLOTS bien definido en config
    
    Returns
    -------
    El slot de la prenda si esta registrada en el diccionario SLOTS, 
    en caso contrario lanza un error
    '''

    prenda = prenda.lower().strip()
    for slot, items in dic.items():
        if prenda in items:
            return slot 
    
    return 'OTRO'

def slots_compatibles(prenda: str, dic: dict = SLOTS) -> list:
    
    '''
    Dado un tipo de prenda calcula los slots complementarios, es decir,
    lo que falta para hacer un outfit
    
    Parameters
    ----------
    prenda: tipo de prenda
    dic: el diccionario que contiene a que slot pertenece cada prenda
    
    Precondition
    ------------
    SLOTS bien definido en config
    
    Returns
    -------
    Una lista de los slots que NO son los de la prenda.
    '''
        
    """Dada la prenda detectada, qué slots corporales puede llevar el resto del outfit."""

    slot_prenda = detectar_slot(prenda, dic)

    slots = [s for s in dic.keys() if s != slot_prenda]
        
    return slots

def hex_to_hsv(hex_color: str) -> tuple: 

    '''
    Traduce los colores hex a hsv
    
    Parameters
    ----------
    hex_color: un color en formato hex
    
    Precondition
    ------------
    -
    
    Returns
    -------
    El color en formato hsv
    '''
        
    hex_color = hex_color.lstrip('#')

    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))

    return tuple(x for x in colorsys.rgb_to_hsv(r, g, b)) 

def es_neutro(s: float, v: float) -> bool:

    '''
    Dados unos valores s y v de un color formato hsv decide si el color es blanco/negro/gris
    
    Parameters
    ----------
    s: saturacion del color
    v: brillo del color
    
    Precondition
    ------------
    -
    
    Returns
    -------
    LTrue si se trata de negro, blanco o gris, False en caso contrario
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
    Dados dos colores calcula una puntuación según si esos colores son compatibles.
    A mayor comatibilidad, mayor puntuación.
        - Neutro (blanco/negro/gris) en cualquiera de los dos -> combina con todo
        - Complementarios (~180°) y análogos (<=25°) -> muy recomendado
        - Triádicos (~120°) -> aceptable
        - Resto -> choque de color
    
    Parameters
    ----------
    hex_a: el primer color
    hex_b: el segundo
    
    Precondition
    ------------
    -
    
    Returns
    -------
    Una puntuación entre 0 y 1
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

def score_prenda_candidata(color_usuario_hex: str, candidata: dict, style_emb: np.ndarray = None) -> float:

    '''
    Dada una imagen 'candidata' calcula una puntuación en base a la compatibilidad de su color dominante 
    frente al color dominante de la imagen subida por el usuario

    
    Parameters
    ----------
    color_usuario_hex: el color predominante de la imagen que subió el usuario
    candidata: la fila de bd correspondiente a esta prenda
    style_emb: -

    Precondition
    ------------
    -
    
    Returns
    -------
    Una puntuación entre 0 y 1
    '''

    color_cat = candidata.get(COL_COLOR)
    color_score = color_compatibility_score(color_usuario_hex, color_cat)

    style_score = 0.5
    emb_raw = candidata.get('embedding')

    if style_emb is not None and emb_raw is not None:
        emb = np.array(json.loads(emb_raw) if isinstance(emb_raw, str) else emb_raw, dtype=np.float32).flatten()
        emb = emb / (np.linalg.norm(emb) + 1e-8)

        # Asegurar que el embedding del usuario también es 1D y unitario
        u_emb = np.array(style_emb, dtype=np.float32).flatten()
        u_emb = u_emb / (np.linalg.norm(u_emb) + 1e-8)

        cos = float(np.dot(u_emb, emb))
        style_score = (cos + 1) / 2

    return PESOS_COMPATIBILIDAD['color'] * color_score + PESOS_COMPATIBILIDAD['estilo'] * style_score

def elegir_una_candidata(candidatas_con_score: list, top_n: int, temperatura: float) -> tuple:

    '''
    Dadas unas imágenes y sus respectivas puntuaciones elegimos una candidata aleatoria de entre el top_n
    con probabilidad proporcional a exp(score/temperatura): las de mejor score tienen mejor probabilidad,
    pero nunca es 1
    
    Parameters
    ----------
    candidatas_con_score: lista de las candidatas y sus puntuaciones
    top_n: el color del fondo, blanco puro
    tol: tolerancia de distancia de color para descartar píxeles cercanos a bg_color.
    
    Precondition
    ------------
    candidatas_con_score debe estar ordenada de forma descendiente según score

    Returns
    -------
    Una candidata, (score, item)
    '''

    top = candidatas_con_score[:top_n]
    scores = np.array([float(s) for s, _ in top], dtype=float)
    pesos = np.exp(scores / temperatura)
    pesos = pesos / pesos.sum()
    idx = np.random.choice(len(top), p=pesos)

    return top[idx]

def completar_outfit(tipo_prenda: str, top_n: int, temperatura: float, color: dict, query_emb: np.ndarray, catalog: list[dict]):
    '''
    Dada un tipo de prenda busca los tipos de prendas restantes para completar un outfit y selecciona 
    una de cada tipo según los criterios de las funciones anteriores
    
    Parameters
    ----------
    prendas: la lista de tipos de prenda
    top_n: para la función choose
    tol: para la función que detecta el color
    color: el color de la prenda que subió el usuario
    query_emb: el embedding de la prenda que subió el usuario
    catalog: la base de datos de prendas
    
    Precondition
    ------------
    -
    
    Returns
    -------
    Una lista con los items seleccionados
    '''

    prendas = slots_compatibles(tipo_prenda)

    matches = []
    for slot in prendas:
        candidatas = [
            p for p in catalog
            if detectar_slot(p.get(COL_FAMILY, '')) == slot
        ]
        if not candidatas:
            raise ValueError(f'  ⚠️  {slot}: sin prendas en catálogo')

        # Calculamos el score de TODAS las candidatas del slot una sola vez
        candidatas_con_score = [
            (score_prenda_candidata(color['hex'], c, query_emb), c)
            for c in candidatas
        ]
        candidatas_con_score.sort(key=lambda x: x[0], reverse=True)

        _, elegida = elegir_una_candidata(candidatas_con_score, top_n, temperatura)

        matches.append(elegida)

    return matches