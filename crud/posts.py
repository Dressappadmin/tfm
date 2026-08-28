import httpx
from PIL import Image
from typing import Any
from core.config import supabase_client, FOTOS_REALES_BUCKET, POSTS_TABLA, ID_POST
from core.api_client import cliente_api
from crud.storage import subir_imagen_bucket 

# SUBIRLO A POSTS_LUCIA
async def registrar_post_bd(
    outfit_id: str,
    usuario_id: str,
    imagen_cuerpo_entero = None, # Aquí iría el tipado Image.Image
    pie_de_foto: str | None = None,
    bucket_name: str = FOTOS_REALES_BUCKET # Cambiado al bucket que me has pedido
) -> str | None:
    """
    Crea una nueva publicación asociada a un Outfit directamente en Supabase.

    Flujo:
      1. Sube la foto al Storage en el bucket FOTOS_REALES_BUCKET (si existe).
      2. Crea el registro en la tabla 'posts_lucia'.
      3. Devuelve el ID del nuevo post.
    """
    try:
        foto_url = None
        
        # 1. Subir la imagen de cuerpo entero al Storage
        if imagen_cuerpo_entero is not None:
            # Asumo que esta función devuelve directamente la URL pública
            foto_url = await subir_imagen_bucket(
                imagen_pil=imagen_cuerpo_entero, 
                usuario_id=usuario_id, 
                bucket_name=bucket_name
            )

        # 2. Preparar los datos del post
        # IMPORTANTE: No incluimos el 'id' en el diccionario porque 
        # Supabase (PostgreSQL) lo genera automáticamente como UUID.
        datos_post = {
            "outfit_id": outfit_id,
            "usuario_id": usuario_id,
            "foto_look_url": foto_url,
            "pie_de_foto": pie_de_foto or "",
            "likes_count": 0
        }

        # 3. Insertar en la tabla 'posts'
        # Usamos el cliente asíncrono que configuraste antes
        respuesta = await supabase_client.table(POSTS_TABLA).insert(datos_post).execute()
        
        if not respuesta.data:
            raise RuntimeError("La base de datos no devolvió los datos al crear el post.")

        # 4. Extraer el ID generado de la respuesta de Supabase
        post_creado = respuesta.data[0]
        post_id = post_creado.get(ID_POST)

        print(f"✅ Post creado con éxito en posts: ID {post_id}")
        return post_id

    except Exception as e:
        print(f"❌ Error interno al crear el post en posts: {str(e)}")
        raise e

async def obtener_posts_recomendados(
    usuario_id: str, 
    limite: int = 10, 
    pagina: int = 1
) -> list[dict[str, Any]]:
    """
    Obtiene un feed de posts personalizados para el usuario.
    
    Llama a una función SQL interna (RPC) en Supabase que utiliza pgvector 
    para comparar el 'embedding' del usuario con el de los outfits publicados.
    Si el usuario es nuevo (Cold Start), la función devuelve los más populares.

    Parameters
    ----------
    usuario_id : str
        ID del usuario que está solicitando ver su feed.
    limite : int, opcional
        Número máximo de posts a devolver por petición.
    pagina : int, opcional
        Número de página actual para la paginación.

    Returns
    -------
    list[dict[str, Any]]
        Lista de diccionarios con la información de los posts recomendados.
    """
    try:
        # 1. Transformamos la página en un 'offset' (filas a saltar)
        offset = (pagina - 1) * limite
        
        # 2. Preparamos los parámetros exactos que espera la función SQL en Supabase
        parametros = {
            "p_usuario_id": usuario_id,
            "p_limite": limite,
            "p_offset": offset
        }
        
        # 3. Llamada ASÍNCRONA al Stored Procedure (RPC)
        # Nota: Asegúrate de que "recomendar_feed_outfits" coincida con el nombre en tu BD
        respuesta = await supabase_client.rpc("recomendar_feed_outfits", parametros).execute()
        
        posts_recomendados = respuesta.data
        
        return posts_recomendados if isinstance(posts_recomendados, list) else []

    except Exception as e:
        print(f"❌ Error interno al procesar el feed para el usuario {usuario_id}: {str(e)}")
        return []