# AND (lower((storage.foldername(name))[1]) = 'public'::text)
import io
import uuid
from typing import Any
from PIL import Image
from supabase import Client
from config import PRENDAS_TABLA
from modulos.procesar_imagen import procesar_imagen
from utils.calcular_embedding import calcular_embedding

def registrar_prenda_bucket(
    imagen: Image.Image, 
    supabase: Client, 
    usuario_id: str | None = None,
    bucket_name: str = "fotos_usuarios"
) -> str:
    '''
    Sube una imagen al bucket indicado en Supabase y devuelve su URL pública.
    
    Parameters
    ----------
    imagen : Image.Image
        La imagen en formato PIL a subir.
    supabase : Client
        El cliente inicializado de Supabase al que se subirá la imagen.
    usuario_id : str | None, opcional
        El ID del usuario que está subiendo la imagen, por defecto None.
    bucket_name : str, opcional
        El nombre del bucket de Supabase, por defecto "fotos_usuarios".
    
    Precondition
    ------------
    La imagen ha sido cargada (y opcionalmente procesada) en memoria como objeto PIL.Image.
    
    Returns
    -------
    str
        La URL pública de la imagen almacenada en el bucket.
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

def registrar_prenda_bd(
    supabase: Client,
    imagen: Image.Image,
    nombre: str,
    precio: float | int,
    marca: str,
    año_venta: int,
    temporada: str,
    seccion: str,  # "WOMAN", "MAN", "OTHERS"
    family: str,   # "CAZADORA VAQUERA", "CAMISETA", "BAMBAS", "EAU DE TOILET"
    processor: Any,
    model: Any,
    ocasion: list[str] | None = None,
    estilo_estetico: list[str] | None = None,
    bucket_name: str = "fotos_usuarios",
    usuario_id: str | None = None
) -> dict[str, Any]:
    '''
    Añade una prenda nueva a la base de datos y su imagen al bucket como una transacción única.
    
    Parameters
    ----------
    supabase : Client
        Cliente inicializado de Supabase.
    imagen : Image.Image
        Imagen de la prenda en formato PIL.
    nombre : str
        Nombre comercial de la prenda.
    precio : float | int
        Precio de venta al público de la prenda.
    marca : str
        Marca fabricante de la prenda.
    año_venta : int
        Año de lanzamiento o temporada de la prenda.
    temporada : str
        Época del año recomendada.
    seccion : str
        Sección demográfica objetivo ("WOMAN", "MAN", "OTHERS").
    family : str
        Categoría estándar de la prenda (ej. "CAMISETA", "BAMBAS").
    processor : Any
        Procesador del modelo de IA cargado en memoria (ej. FashionCLIP processor).
    model : Any
        Modelo de IA cargado en memoria (ej. FashionCLIP model).
    ocasion : list[str] | None, opcional
        Lista de ocasiones de uso recomendadas, por defecto None.
    estilo_estetico : list[str] | None, opcional
        Lista de inspiraciones o estéticas de la prenda, por defecto None.
    bucket_name : str, opcional
        Nombre del bucket de almacenamiento, por defecto "fotos_usuarios".
    usuario_id : str | None, opcional
        ID del usuario creador de la prenda, por defecto None.
    
    Precondition
    ------------
    La conexión a Supabase (Client) está activa y los modelos de IA (procesador y modelo)
    están pre-cargados en la memoria RAM del servidor.
    
    Returns
    -------
    int | str
        El ID único del registro creado en la base de datos (entero o UUID).
        
    Raises
    ------
    Exception
        Si la subida al bucket, el procesamiento IA o la inserción en BD fallan.
    '''
    
    # ---------------------------------------------------------------------
    # PASO 1: Subir imagen al Storage de Supabase (Fuera del try de la BD)
    # ---------------------------------------------------------------------
    img_url = registrar_prenda_bucket(
        supabase=supabase,
        imagen=imagen,
        bucket_name=bucket_name
    )

    try:
        # ---------------------------------------------------------------------
        # PASO 2: Extracción automática de atributos visuales mediante IA
        # ---------------------------------------------------------------------
        embedding_ndarray, family_standar, color_predominante = procesar_imagen(imagen)
        embedding_lista = embedding_ndarray.tolist()

        # ---------------------------------------------------------------------
        # PASO 3: Construir el diccionario coherente con las columnas de BD
        # ---------------------------------------------------------------------
        datos_prenda = {
            "nombre": nombre,
            "precio": float(precio),
            "marca": marca,
            "año_venta": int(año_venta),
            "temporada": temporada,
            "seccion": seccion,
            "categoria": family,
            "categoria_std": family_standar[0][0],
            "url_bucket": img_url,
            "img_url_std": None,
            "embedding": embedding_lista,
            "color_pred_hex": color_predominante,
            "en_stock": False,
            "ocasion": ocasion or [],
            "inspiracion": estilo_estetico or []
        }

        if usuario_id:
            datos_prenda["usuario_id"] = usuario_id

        # ---------------------------------------------------------------------
        # PASO 4: Inserción en la tabla de base de datos
        # ---------------------------------------------------------------------
        respuesta = supabase.table(PRENDAS_TABLA).insert(datos_prenda).execute()

        if not respuesta.data:
            raise RuntimeError("La base de datos no devolvió datos tras el insert en PRENDAS.")

        print(f"✅ Prenda guardada con éxito en BD: ID {respuesta.data[0].get('id')} ({nombre})")
        return respuesta.data[0].get("id")

    except Exception as e:
        print(f"❌ Error al registrar la prenda '{nombre}' en BD. Iniciando Rollback...")
        
        # ---------------------------------------------------------------------
        # ROLLBACK: Borrar la imagen del bucket si falló algo del paso 2 al 4
        # ---------------------------------------------------------------------
        try:
            nombre_archivo = img_url.split("/")[-1]
            supabase.storage.from_(bucket_name).remove([nombre_archivo])
            print(f"✅ Rollback completado: Imagen eliminada del bucket ({nombre_archivo}).")
        except Exception as rb_error:
            print(f"⚠️ ADVERTENCIA CRÍTICA: Falló el rollback del bucket. Archivo huérfano: {img_url}. Error: {rb_error}")
        
        # Relanzamos la excepción original para que FastAPI se entere del error real
        raise e