from utils.catalogos import SLOTS, MAPA_PRENDAS

def validar_reglas_outfit(tipos_prendas: list[str]) -> tuple[bool, str]:
    '''
    Evalúa una lista de tipos de prendas y comprueba si forman un conjunto de ropa con sentido.
    
    Aplica reglas de negocio estrictas de moda, verificando que el outfit tenga 
    una base lógica completa (top y bottom, o prenda de cuerpo entero), que no haya 
    excesos incoherentes (ej. múltiples calzados o pantalones) y que las capas 
    principales no entren en conflicto. Utiliza el mapeo de SLOTS del catálogo.

    Parameters
    ----------
    tipos_prendas : list[str]
        Lista de cadenas de texto con las categorías (SLOT_PRENDA) o tipos de prendas 
        subidas por el usuario (ej. ["SUPERIOR", "INFERIOR", "CALZADO"] o ["camiseta", "falda"]).

    Returns
    -------
    tuple[bool, str]
        Una tupla donde el primer elemento (bool) indica si el outfit es válido (True) 
        o incumple alguna regla (False). El segundo elemento (str) es un mensaje 
        descriptivo del estado o del error exacto.
    '''

    conteos = {slot: 0 for slot in SLOTS.keys()}

    for item in tipos_prendas:
        item_norm = item.strip().lower()
        item_upper = item.strip().upper()

        if item_upper in conteos:
            conteos[item_upper] += 1
        elif item_norm in MAPA_PRENDAS:
            slot = MAPA_PRENDAS[item_norm]
            conteos[slot] += 1

    if conteos['CALZADO'] == 0:
        return False, "Todo outfit debe llevar calzado."
    if conteos['CALZADO'] > 1:
        return False, "¡Ups! No puedes incluir más de un par de calzado en un mismo outfit."

    if conteos['CUERPO_COMPLETO'] > 0 and (conteos['SUPERIOR'] > 0 or conteos['INFERIOR'] > 0):
        return False, "Si has elegido una prenda de cuerpo entero, no debes añadir partes superiores ni inferiores extra."

    tiene_base_valida = (conteos['SUPERIOR'] >= 1 and conteos['INFERIOR'] >= 1) or (conteos['CUERPO_COMPLETO'] == 1)
    
    if not tiene_base_valida:
        if conteos['CUERPO_COMPLETO'] == 0:
            if conteos['SUPERIOR'] >= 1 and conteos['INFERIOR'] == 0:
                return False, "Te falta añadir una parte inferior (pantalón, falda...) para acompañar a tu parte superior."
            elif conteos['INFERIOR'] >= 1 and conteos['SUPERIOR'] == 0:
                return False, "Te falta añadir una parte superior (camiseta, jersey...) para acompañar a tu parte inferior."
            else:
                return False, "El outfit está incompleto. Necesitas al menos una combinación de SUPERIOR + INFERIOR o un CUERPO COMPLETO."

    if conteos['INFERIOR'] > 1:
        return False, "Has seleccionado demasiadas partes inferiores. Un outfit normal solo lleva una."
    
    if conteos['SUPERIOR'] > 3:
        return False, "Has seleccionado demasiadas partes superiores (máximo permitido para capas: 3)."

    return True, "¡Outfit validado correctamente!"

def determinar_slot_faltante(tipos_prendas: list[str]) -> str | None:
    '''
    Evalúa una lista de categorías de prendas actuales para determinar cuál es el siguiente slot o categoría más urgente que falta para completar un outfit básico.

    Parameters
    ----------
    tipos_prendas : list[str]
        Lista de cadenas de texto que representan las categorías o slots de las prendas que ya conforman el outfit actual.

    Returns
    ----------
    str or None
        Cadena de texto con el nombre de la categoría faltante (como "SUPERIOR", "INFERIOR" o "CALZADO"), o None si el outfit ya cuenta con todas las prendas básicas necesarias.
    '''

    tiene_cuerpo_completo = "CUERPO_COMPLETO" in tipos_prendas
    tiene_superior = "SUPERIOR" in tipos_prendas
    tiene_inferior = "INFERIOR" in tipos_prendas
    
    if not tiene_cuerpo_completo:
        if tiene_superior and not tiene_inferior:
            return "INFERIOR"
        elif tiene_inferior and not tiene_superior:
            return "SUPERIOR"
        elif not tiene_superior and not tiene_inferior:
            return "SUPERIOR" 
            
    if "CALZADO" not in tipos_prendas:
        return "CALZADO"
        
    return None