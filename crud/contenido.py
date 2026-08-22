import httpx
from PIL import Image

from core.api_client import cliente_api
# Importamos la función de subida de tu nuevo módulo de storage
from crud.storage import subir_imagen_bucket 

async def registrar_post_bd(
    outfit_id: str,
    usuario_id: str,
    imagen_cuerpo_entero: Image.Image | None = None,
    pie_de_foto: str | None = None,
    bucket_name: str = "posts-looks"
) -> str | None:
    """
    Crea una nueva publicación (Post) asociada a un Outfit existente mediante la API externa.

    Flujo:
      1. Sube la foto de cuerpo entero al Storage (si existe).
      2. Crea el registro en la tabla 'posts' enlazando el 'outfit_id'.
      3. Inicializa 'looks_usuarios' con la foto del autor.

    Parameters
    ----------
    outfit_id : str
        ID del outfit que se está publicando.
    usuario_id : str
        ID del usuario autor del post.
    imagen_cuerpo_entero : Image.Image | None, opcional
        Imagen (objeto PIL) del look puesto.
    pie_de_foto : str | None, opcional
        Texto de la publicación.
    bucket_name : str, opcional
        Nombre del contenedor de archivos en la nube.

    Returns
    -------
    str | None
        El ID del post creado si fue exitoso, o lanza una excepción en caso de error.
    """
    try:
        foto_url = None
        
        # 1. Subir la imagen de cuerpo entero al Storage (Si hay imagen)
        if imagen_cuerpo_entero is not None:
            # Esta función de storage también debe ser asíncrona ('await')
            foto_url = await subir_imagen_bucket(
                imagen_pil=imagen_cuerpo_entero, 
                usuario_id=usuario_id, 
                bucket_name=bucket_name
            )

        # Inicializamos la lista de prueba social (solo incluimos la foto si existe)
        looks_usuarios = [foto_url] if foto_url else []

        # 2. Preparar los datos del post para la API
        datos_post = {
            "outfit_id": outfit_id,
            "usuario_id": usuario_id,
            "foto_look_url": foto_url,
            "looks_usuarios": looks_usuarios, 
            "pie_de_foto": pie_de_foto or "",
            "likes_count": 0,
            "comentarios_count": 0
        }

        # 3. Insertar a través de la API externa (Endpoint POST /posts)
        url_endpoint = "/posts" # Ajustar si la API tiene otra ruta
        respuesta = await cliente_api.post(url_endpoint, json=datos_post)
        
        # Comprobar si hubo error de red o de base de datos
        respuesta.raise_for_status()

        # Extraer el ID de la respuesta
        post_creado = respuesta.json()
        
        # Extraemos el ID dependiendo de si la API devuelve una lista o un diccionario
        if isinstance(post_creado, list) and len(post_creado) > 0:
            post_id = post_creado[0].get('id')
        elif isinstance(post_creado, dict):
            post_id = post_creado.get('id')
        else:
            post_id = None

        if not post_id:
            raise RuntimeError("La API no devolvió un ID válido al crear el post.")

        print(f"✅ Post creado con éxito: ID {post_id}")
        return post_id

    except httpx.HTTPError as e:
        print(f"❌ Error de red/API al crear el post del outfit {outfit_id}: {str(e)}")
        raise e
    except Exception as e:
        print(f"❌ Error interno al crear el post: {str(e)}")
        raise e