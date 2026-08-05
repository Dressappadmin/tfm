import io
import uuid
from PIL import Image
from supabase import Client





def crear_post_outfit(
    supabase: Client,
    outfit_id: str,
    usuario_id: str,
    imagen_cuerpo_entero: Image.Image,
    pie_de_foto: str | None = None,
    bucket_name: str = "posts-looks"
) -> dict:
    """
    Crea una nueva publicación (Post) asociada a un Outfit existente.
    
    Flujo:
      1. Sube la foto de cuerpo entero al Storage.
      2. Crea el registro en la tabla 'posts' enlazando el 'outfit_id'.
      3. Inicializa 'looks_usuarios' con la foto del autor.
    """
    try:
        # 1. Subir la imagen de cuerpo entero al Storage
        foto_url = subir_imagen_storage(
            supabase=supabase,
            imagen=imagen_cuerpo_entero,
            usuario_id=usuario_id,
            bucket_name=bucket_name
        )

        # 2. Preparar los datos del post para insertar en base de datos
        datos_post = {
            "outfit_id": outfit_id,
            "usuario_id": usuario_id,
            "foto_look_url": foto_url,
            # Inicializamos la lista de prueba social con la foto del autor
            "looks_usuarios": [foto_url], 
            "pie_de_foto": pie_de_foto or "",
            "likes_count": 0,
            "comentarios_count": 0
        }

        # 3. Insertar en la tabla 'posts' y devolver la fila creada
        respuesta = supabase.table("posts").insert(datos_post).execute()

        if not respuesta.data:
            raise RuntimeError("No se pudo crear el registro en la tabla posts.")

        print(f"✅ Post creado con éxito: ID {respuesta.data[0]['id']}")
        return respuesta.data[0]

    except Exception as e:
        print(f"❌ Error al crear el post del outfit {outfit_id}: {str(e)}")
        raise e