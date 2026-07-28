from config import SLOTS

def slot_de(prenda: str, dic: dict =SLOTS) -> str:
    print(f'\nEstoy en slot_de con {prenda}')
    prenda = prenda.lower().strip()
    for slot, items in dic.items():
        if prenda in items:
            return slot
    return 'OTRO'

def slots_compatibles(prenda_detectada: str, dic: dict =SLOTS) -> list:
    """Dada la prenda detectada, qué slots corporales puede llevar el resto del outfit."""
    slot = slot_de(prenda_detectada, dic)
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

def get_families_compatibles(prenda_detectada: str, dic: dict =SLOTS) -> list:
    """Mantiene compatibilidad con el nombre usado en el resto del notebook."""
    return slots_compatibles(prenda_detectada, dic)