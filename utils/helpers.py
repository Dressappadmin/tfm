from utils.catalogos import SLOTS, TODOS_LOS_SLOTS

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

def slots_compatibles(prenda: str, dic: dict[str, list[str]] = SLOTS) -> list[str]:
    '''
    Calcula los slots complementarios necesarios para armar un look dada una prenda inicial.
    
    Parameters
    ----------
    prenda : str
        Nombre o categoría de la prenda base.
    dic : dict[str, list[str]], opcional
        Diccionario que contiene a qué slot pertenece cada prenda, por defecto SLOTS.
    
    Precondition
    ------------
    La constante SLOTS debe estar bien definida en config.
    
    Returns
    -------
    list[str]
        Una lista con los nombres de los slots que complementan a la prenda para 
        completar el outfit (excluyendo el slot de la prenda misma).
    '''
    slot = detectar_slot(prenda, dic)

    if slot == 'SUPERIOR':
        return ['INFERIOR', 'ABRIGO', 'CALZADO', 'ACCESORIO']
    if slot == 'INFERIOR':
        return ['SUPERIOR', 'ABRIGO', 'CALZADO', 'ACCESORIO']
    if slot == 'CUERPO_COMPLETO':
        return ['ABRIGO', 'CALZADO', 'ACCESORIO']
    if slot in ('ABRIGO', 'CALZADO', 'ACCESORIO'):
        return [s for s in TODOS_LOS_SLOTS if s != slot]
    return []