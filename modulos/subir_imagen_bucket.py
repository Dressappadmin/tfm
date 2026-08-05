import io
import uuid
from PIL import Image
from supabase import Client

def subir_imagen_bucket(
    imagen: Image.Image, 
    supabase: Client, 
    usuario_id: str | None = None,
    bucket_name: str = "fotos_usuarios"
) -> str:
    '''
    Función que dada una imagen la sube al bucket indicado
    
    Parameters
    ----------
    imagen: la imagen
    supabase: el cliente de supabase al que se subirá la imagen
    usuario_id: el id del usuario que está subiendo la imagen (opcional)
    bucket_name: el nombre del bucket al que se subirá la imagen
    
    Precondition
    ------------
    La imagen ha sido procesada
    
    Returns
    -------
    La url de la imagen en el bucket
    '''
    
    buffer = io.BytesIO()

    # 1. Detectar si la imagen tiene transparencia (RGBA) o es normal (RGB)
    if imagen.mode in ("RGBA", "LA", "P"):
        # Guardamos en PNG para preservar el fondo transparente recortado por IA
        formato = "PNG"
        content_type = "image/png"
        extension = "png"
        imagen.save(buffer, format=formato, optimize=True)
    else:
        # Si está en modo RGB (ej. foto look completo), guardamos en JPEG ligero
        if imagen.mode != "RGB":
            imagen = imagen.convert("RGB")
        formato = "JPEG"
        content_type = "image/jpeg"
        extension = "jpg"
        imagen.save(buffer, format=formato, quality=88)

    file_bytes = buffer.getvalue()

    # 2. Generar nombre de archivo único directamente en la raíz del bucket
    nombre_archivo = f"{uuid.uuid4()}.{extension}"

    # 3. Subir al bucket de Supabase Storage
    supabase.storage.from_(bucket_name).upload(
        path=nombre_archivo,
        file=file_bytes,
        file_options={"content-type": content_type}
    )

    # 4. Obtener la URL pública para guardarla en la columna 'img_url'
    url_publica = supabase.storage.from_(bucket_name).get_public_url(nombre_archivo)
    return url_publica