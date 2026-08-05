from config import PRENDAS_BUCKET
from .cargar_bd import supabase

def eliminar_imagen_bucket(url_imagen: str) -> bool:
    try:
        # Extraemos el nombre/ruta del archivo a partir de la URL pública
        nombre_archivo = url_imagen.split("/")[-1]
        
        res = supabase.storage.from_(PRENDAS_BUCKET).remove([nombre_archivo])
        return True
    except Exception as e:
        print(f"Error borrando del bucket: {e}")
        return False