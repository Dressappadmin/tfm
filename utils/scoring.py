from PIL import Image
import numpy as np
import json
import colorsys
from sklearn.cluster import KMeans
from config import COL_COLOR, COL_FAMILY, COL_NAME
from utils.compatibles import slot_de
from config import PESOS_COMPATIBILIDAD

def hex_to_hsv(hex_color: str):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(x for x in colorsys.rgb_to_hsv(r, g, b))  # (h[0-1], s, v)

def es_neutro(s: float, v: float) -> bool:
    """Blanco, negro y grises se consideran neutros: combinan con todo."""
    if v < 0.15:
        return True
    if v > 0.92 and s < 0.15:
        return True
    if s < 0.12:
        return True
    return False

def color_compatibility_score(hex_a: str, hex_b: str) -> float:
    """
    0-1 según el círculo cromático:
      - Neutro (blanco/negro/gris) en cualquiera de los dos -> combina con todo
      - Complementarios (~180°) y análogos (<=25°) -> muy recomendado
      - Triádicos (~120°) -> aceptable
      - Resto -> choque de color
    """
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

def detectar_color_prenda(img_clean: Image.Image, bg_color=(255, 255, 255), tol=18) -> dict:
    """
    Detecta el color dominante de la prenda sobre la imagen YA SIN FONDO:
      1. Descarta píxeles de fondo (blancos).
      2. Agrupa el resto en 3 clusters (K-means) para ignorar sombras/reflejos.
      3. Se queda con el cluster más grande = color dominante real.
    """
    arr = np.array(img_clean.convert('RGB'))
    pixels = arr.reshape(-1, 3)
    dist_to_bg = np.sqrt(((pixels.astype(int) - np.array(bg_color)) ** 2).sum(axis=1))
    fg_pixels = pixels[dist_to_bg > tol]
    if len(fg_pixels) < 10:
        fg_pixels = pixels
    k = min(3, len(fg_pixels))
    km = KMeans(n_clusters=k, n_init=4, random_state=0).fit(fg_pixels)
    counts = np.bincount(km.labels_)
    dominante = km.cluster_centers_[counts.argmax()].astype(int)
    hex_color = '#{:02X}{:02X}{:02X}'.format(*dominante)
    return {'hex': hex_color, 'rgb': tuple(int(x) for x in dominante)}

def score_prenda_candidata(color_usuario_hex: str, candidata: dict, style_emb: np.ndarray = None) -> float:
    print('\nDEBUG: CALCULANDO SCORE_PRENDA_CANDIDATA')
    print(f'\n style_emb = {style_emb}')
    color_cat = candidata.get(COL_COLOR)
    color_score = color_compatibility_score(color_usuario_hex, color_cat)

    style_score = 0.5
    emb_raw = candidata.get('embedding')
    print(f'\n emb_raw = {emb_raw}')
    if style_emb is not None and emb_raw is not None:
        emb = np.array(json.loads(emb_raw) if isinstance(emb_raw, str) else emb_raw, dtype=np.float32)
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        cos = float(np.dot(style_emb, emb))
        style_score = (cos + 1) / 2

    return PESOS_COMPATIBILIDAD['color'] * color_score + PESOS_COMPATIBILIDAD['estilo'] * style_score

def choose(candidatas_con_score, top_n, temperatura):
    # candidatas_con_score: lista de tuplas (score, item), ya ordenada desc.
    # Devuelve (score, item) elegido al azar entre las top_n mejores, con
    # probabilidad proporcional a exp(score/temperatura): las de mejor score
    # tienen mas probabilidad, pero no el 100%.
    top = candidatas_con_score[:top_n]
    print(f"DEBUG CHOOSE - len(top): {len(top)}, scores: {[s for s, _ in top]}") # <-- Añade esto
    scores = np.array([float(s) for s, _ in top], dtype=float)
    pesos = np.exp(scores / temperatura)
    pesos = pesos / pesos.sum()
    idx = np.random.choice(len(top), p=pesos)
    return top[idx]

def selection(prendas: list, top_n: int, temperatura: float, color: dict, query_emb, catalog: list[dict]):
    matches = []
    for slot in prendas:
        candidatas = [
            p for p in catalog
            if slot_de(p.get(COL_FAMILY, '')) == slot
        ]
        if not candidatas:
            print(f'  ⚠️  {slot}: sin prendas en catálogo')
            continue

        # Calculamos el score de TODAS las candidatas del slot una sola vez
        candidatas_con_score = [
            (score_prenda_candidata(color['hex'], c, query_emb), c)
            for c in candidatas
        ]
        candidatas_con_score.sort(key=lambda x: x[0], reverse=True)

        mejor_score, elegida = choose(candidatas_con_score, top_n, temperatura)
        matches.append(elegida)
        print(f"  ✅ {slot}: {elegida.get(COL_NAME)}  (score={mejor_score:.2f})")
    return matches