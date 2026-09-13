from typing import Any
from core.config import supabase_client

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
        offset = (pagina - 1) * limite
        
        parametros = {
            "p_usuario_id": usuario_id,
            "p_limite": limite,
            "p_offset": offset
        }
        
        respuesta = await supabase_client.rpc("recomendar_feed_outfits", parametros).execute()
        
        posts_recomendados = respuesta.data
        
        return posts_recomendados if isinstance(posts_recomendados, list) else []

    except Exception as e:
        print(f"❌ Error interno al procesar el feed para el usuario {usuario_id}: {str(e)}")
        return []