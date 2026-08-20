from config import SLOTS

def detectar_slot(prenda: str, dic: dict[str, list[str]] = SLOTS) -> str:
    '''
    Detecta a qué parte del cuerpo (slot) corresponde un tipo de prenda dado.
    
    Parameters
    ----------
    prenda : str
        Nombre o categoría de la prenda (ej. "Camiseta", "Pantalón").
    dic : dict[str, list[str]], opcional
        Diccionario que mapea cada slot con una lista de categorías de prendas.
        Por defecto utiliza la constante global SLOTS de config.
    
    Precondition
    ------------
    La constante SLOTS debe estar bien definida en config con listas de strings en minúsculas.
    
    Returns
    -------
    str
        El slot al que pertenece la prenda (ej. 'SUPERIOR', 'INFERIOR'). 
        Devuelve 'OTRO' si la prenda no se encuentra en el diccionario.
    '''
    prenda = prenda.lower().strip()
    for slot, items in dic.items():
        if prenda in items:
            return slot 
    
    return 'OTRO'