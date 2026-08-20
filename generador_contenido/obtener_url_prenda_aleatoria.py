import random
from typing import Any
from config import IMG_URL_PRENDA

def obtener_url_prenda_aleatoria(catalog: list[dict[str, Any]]) -> str | None:
    """
    Selecciona una prenda aleatoria del catálogo y devuelve únicamente su URL de imagen.
    
    Args:
        catalog: Lista de diccionarios de prendas devuelta por Supabase.
        
    Returns:
        Un string con la URL de la imagen o None si el catálogo está vacío.
    """
    if not catalog:
        return None
        
    prenda_elegida = random.choice(catalog)
    
    # Extraemos solo la URL (compatible con 'url_imagen' o 'img_url' según tu tabla)
    return prenda_elegida.get(IMG_URL_PRENDA)