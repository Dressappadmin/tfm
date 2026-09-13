import io
import httpx
from PIL import Image
from core.config import supabase_client, PRENDAS_BUCKET

async def cargar_imagen_bucket(nombre_archivo: str, bucket_name: str = PRENDAS_BUCKET) -> Image.Image:
    '''
    Descarga una imagen desde un bucket de almacenamiento o mediante una URL pública y la convierte a formato PIL Image con modo RGB, asegurando su compatibilidad con los modelos de procesamiento visual.

    Parameters
    ----------
    nombre_archivo : str
        Nombre del archivo de la imagen o URL pública completa desde la que se realizará la descarga.
    bucket_name : str, optional
        Nombre del bucket de almacenamiento en Supabase desde donde se obtendrá el archivo si no se proporciona una URL (por defecto es PRENDAS_BUCKET).

    Returns
    ----------
    Image.Image
        Objeto de imagen en formato PIL con el modo RGB aplicado.
    '''
    try:
        if nombre_archivo.startswith("http://") or nombre_archivo.startswith("https://"):
            url_imagen = nombre_archivo
        else:
            url_imagen = await supabase_client.storage.from_(bucket_name).get_public_url(nombre_archivo)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            respuesta = await client.get(url_imagen)
            respuesta.raise_for_status()

        imagen_bytes = io.BytesIO(respuesta.content)
        imagen_pil = Image.open(imagen_bytes).convert("RGB")
        
        return imagen_pil

    except httpx.HTTPError as e:
        raise ValueError(f"Error de red al descargar la imagen {nombre_archivo}: {str(e)}")
    except Exception as e:
        raise ValueError(f"El archivo descargado no es una imagen válida o no se encontró: {str(e)}")