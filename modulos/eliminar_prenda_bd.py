from config import PRENDAS_TABLA
from .cargar_bd import supabase

def eliminar_prenda_bd(url_imagen: str) -> bool:
    try:
        # Borramos la fila cuya columna url coincida
        res = supabase.table(PRENDAS_TABLA).delete().eq("url_imagen", url_imagen).execute()
        return True
    except Exception as e:
        print(f"Error borrando de la BD: {e}")
        return False 