from config import SLOTS
from utils.detectar_slot import detectar_slot

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

    todos = ['SUPERIOR', 'INFERIOR', 'CUERPO_COMPLETO', 'ABRIGO', 'CALZADO', 'ACCESORIO']
    
    if slot == 'SUPERIOR':
        return ['INFERIOR', 'ABRIGO', 'CALZADO', 'ACCESORIO']
    if slot == 'INFERIOR':
        return ['SUPERIOR', 'ABRIGO', 'CALZADO', 'ACCESORIO']
    if slot == 'CUERPO_COMPLETO':
        return ['ABRIGO', 'CALZADO', 'ACCESORIO']
    if slot in ('ABRIGO', 'CALZADO', 'ACCESORIO'):
        return [s for s in todos if s != slot]
    return []