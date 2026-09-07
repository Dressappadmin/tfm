from utils.catalogos import SLOTS

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

    Precondition
    ------------
    Los tipos de prendas deben provenir de la extracción de características previa 
    o de la selección del usuario. La función mapea los inputs contra el diccionario SLOTS.

    Returns
    -------
    tuple[bool, str]
        Una tupla donde el primer elemento (bool) indica si el outfit es válido (True) 
        o incumple alguna regla (False). El segundo elemento (str) es un mensaje 
        descriptivo del estado o del error exacto.
    '''

    # Invertimos el diccionario para mapear rápidamente cualquier prenda a su SLOT (O(1))
    mapa_prendas = {prenda: slot for slot, prendas in SLOTS.items() for prenda in prendas}

    # Inicializamos los contadores basados en tus SLOTS
    conteos = {slot: 0 for slot in SLOTS.keys()}

    # Procesamos la lista de entrada
    for item in tipos_prendas:
        item_norm = item.strip().lower()
        item_upper = item.strip().upper()

        if item_upper in conteos:
            # Si el input ya es un SLOT_PRENDA (ej. 'SUPERIOR')
            conteos[item_upper] += 1
        elif item_norm in mapa_prendas:
            # Si el input es una prenda específica (ej. 'camiseta'), buscamos su SLOT
            slot = mapa_prendas[item_norm]
            conteos[slot] += 1

    # --- APLICACIÓN DE REGLAS DE MODA ---

    # Regla A: Lógica de pies
    if conteos['CALZADO'] == 0:
        return False, "Todo outfit debe llevar calzado."
    if conteos['CALZADO'] > 1:
        return False, "¡Ups! No puedes incluir más de un par de calzado en un mismo outfit."

    # Regla B: Lógica de capas principales
    if conteos['CUERPO_COMPLETO'] > 0 and (conteos['SUPERIOR'] > 0 or conteos['INFERIOR'] > 0):
        return False, "Si has elegido una prenda de cuerpo entero, no debes añadir partes superiores ni inferiores extra."

    # Regla C: Completitud de la base
    tiene_base_valida = (conteos['SUPERIOR'] >= 1 and conteos['INFERIOR'] >= 1) or (conteos['CUERPO_COMPLETO'] == 1)
    
    if not tiene_base_valida:
        if conteos['CUERPO_COMPLETO'] == 0:
            if conteos['SUPERIOR'] >= 1 and conteos['INFERIOR'] == 0:
                return False, "Te falta añadir una parte inferior (pantalón, falda...) para acompañar a tu parte superior."
            elif conteos['INFERIOR'] >= 1 and conteos['SUPERIOR'] == 0:
                return False, "Te falta añadir una parte superior (camiseta, jersey...) para acompañar a tu parte inferior."
            else:
                return False, "El outfit está incompleto. Necesitas al menos una combinación de SUPERIOR + INFERIOR o un CUERPO COMPLETO."

    # Regla D: Evitar excesos absurdos
    if conteos['INFERIOR'] > 1:
        return False, "Has seleccionado demasiadas partes inferiores. Un outfit normal solo lleva una."
    
    if conteos['SUPERIOR'] > 3:
        return False, "Has seleccionado demasiadas partes superiores (máximo permitido para capas: 3)."

    # Si pasa todas las validaciones
    return True, "¡Outfit validado correctamente!"