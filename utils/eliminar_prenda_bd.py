from data.supabase import supabase
from config import PRENDAS_BUCKET, PRENDAS_TABLA, COL_IMG_URL

def eliminar_imagen_bucket(url_imagen: str, bucket: str = PRENDAS_BUCKET) -> bool:

    '''
    Elimina una imagen del bucket de prendas de supabase

    Parameters
    ----------
    url _imagen: str
        La URL del bucket donde está almacenada la imagen.

    Returns
    -------
    Bool
        True si la operación se ha completado con éxito, false en caso contrario.
    '''
    try:
        # Extraemos el nombre/ruta del archivo a partir de la URL pública
        nombre_archivo = url_imagen.split("/")[-1]
        
        # En la API de Supabase, remove puede no lanzar excepción pero devolver un error en la respuesta
        res = supabase.storage.from_(bucket).remove([nombre_archivo])
        
        # Aseguramos que la respuesta indique éxito (el array de respuesta no debe estar vacío)
        if isinstance(res, list) and len(res) > 0:
            return True
        return False
        
    except Exception as e:
        print(f"Error borrando del bucket: {e}")
        return False

def eliminar_prenda_bd(url_imagen: str, tabla: str = PRENDAS_TABLA, bucket: str = PRENDAS_BUCKET) -> bool:

    '''
    Elimina una prenda de la tabla y su correspondiente imagen del bucket de supabase.
    Si no se puede realizar el borrado de ambas, no se realiza nada.
    Usamos los parámetros tabla y bucket para poder reutilizar la función en un futuro.

    Parameters
    ----------
    url_imagen : str
        La URL web o del bucket donde está almacenada la imagen.

    Returns
    -------
    Bool
        True si la operación se ha completado con éxito, false en caso contrario.
    '''
    try:
        # PASO 1: Obtener la fila original ANTES de borrarla (necesario para el rollback)
        res_select = supabase.table(tabla).select("*").eq(COL_IMG_URL, url_imagen).execute()
        
        if not res_select.data:
            print("Error: La prenda no existe en la base de datos.")
            return False
            
        fila_original = res_select.data[0]

        # PASO 2: Borrar de la Base de Datos
        res_delete = supabase.table(tabla).delete().eq(COL_IMG_URL, url_imagen).execute()
        
        # PASO 3: Borrar del Bucket
        exito_bucket = eliminar_imagen_bucket(url_imagen, bucket=bucket)

        # PASO 4: ROLLBACK si el bucket falló
        if not exito_bucket:
            print("Fallo en el Storage. Revirtiendo (re-insertando) en la base de datos...")
            # Volvemos a guardar la fila exactamente como estaba (mismo ID y datos)
            supabase.table(tabla).insert(fila_original).execute()
            return False

        print("Transacción exitosa: Prenda e imagen eliminadas.")
        return True

    except Exception as e:
        print(f"Error crítico en la transacción: {e}")
        return False