import io
import httpx
from PIL import Image
from core.config import supabase_client, PRENDAS_BUCKET

async def cargar_imagen_bucket(nombre_archivo: str, bucket_name: str = PRENDAS_BUCKET) -> Image.Image:
    """
    Descarga una imagen desde el Storage de Supabase usando su nombre de archivo
    y la convierte en un objeto PIL Image listo para los modelos de IA.
    """
    try:
        # 1. Supabase nos genera la URL pública correcta automáticamente
        url_imagen = supabase_client.storage.from_(bucket_name).get_public_url(nombre_archivo)
        
        # 2. Descargamos la imagen asíncronamente
        async with httpx.AsyncClient(timeout=15.0) as client:
            respuesta = await client.get(url_imagen)
            respuesta.raise_for_status()
            
        # 3. Procesamos los bytes y forzamos RGB (vital para FashionCLIP)
        imagen_bytes = io.BytesIO(respuesta.content)
        imagen_pil = Image.open(imagen_bytes).convert("RGB")
        
        return imagen_pil

    except httpx.HTTPError as e:
        raise ValueError(f"Error de red al descargar la imagen {nombre_archivo}: {str(e)}")
    except Exception as e:
        raise ValueError(f"El archivo descargado no es una imagen válida o no se encontró: {str(e)}")