import io
import httpx
from PIL import Image

async def cargar_imagen_url_bucket(url_imagen: str) -> Image.Image:
    """
    Descarga una imagen desde una URL (pública o privada del bucket)
    y la convierte en un objeto PIL Image listo para los modelos de IA.
    """
    try:
        # Usamos un cliente nuevo y limpio (sin base_url ni tokens de la API)
        # Esto es importante por seguridad: no queremos enviar las credenciales 
        # de nuestra API a un servidor de almacenamiento externo.
        async with httpx.AsyncClient(timeout=15.0) as client:
            respuesta = await client.get(url_imagen)
            
            # Si el bucket devuelve un 404 (no existe) o 403 (prohibido), lanzamos error
            respuesta.raise_for_status()
            
        # respuesta.content contiene los 'bytes' crudos de la imagen
        imagen_bytes = io.BytesIO(respuesta.content)
        
        # Abrimos la imagen con PIL y forzamos el formato RGB 
        # (vital para evitar errores con imágenes PNG transparentes (RGBA) en FashionCLIP)
        imagen_pil = Image.open(imagen_bytes).convert("RGB")
        
        return imagen_pil

    except httpx.HTTPError as e:
        # Error de red o descarga (ej. URL caída)
        raise ValueError(f"Error de red al descargar la imagen: {e}")
    except Exception as e:
        # Error al procesar los bytes (ej. la URL no era realmente una imagen)
        raise ValueError(f"El archivo descargado no es una imagen válida: {e}")