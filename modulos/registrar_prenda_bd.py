# AND (lower((storage.foldername(name))[1]) = 'public'::text)
from typing import Any
from PIL import Image
from supabase import Client
from config import PRENDAS_TABLA
from .reconocer_prenda import reconocer_prenda
from .detectar_color_prenda import detectar_color_prenda
from .subir_imagen_bucket import subir_imagen_bucket
from .calcular_embedding import calcular_embedding

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
    # Modelos cargados en memoria
    processor: Any,
    model: Any,
    # Parámetros opcionales adicionales para recomendación
    ocasion: list[str] | None = None,
    estilo_estetico: list[str] | None = None,
    bucket_name: str = "fotos_usuarios",
    usuario_id: str | None = None
) -> dict[str, Any]:
    '''
    Función que añade una fila nueva a la base de datos de prendas.
    
    Parameters
    ----------
    
    Precondition
    ------------
    La imagen ha sido procesada
    
    Returns
    -------
    La url de la imagen en el bucket
    '''
    try:
        # ---------------------------------------------------------------------
        # PASO 1: Subir imagen al Storage de Supabase y obtener URL pública
        # ---------------------------------------------------------------------
        img_url = subir_imagen_bucket(
            supabase=supabase,
            imagen=imagen,
            bucket_name=bucket_name
        )

        # ---------------------------------------------------------------------
        # PASO 2: Extracción automática de atributos visuales mediante IA
        # ---------------------------------------------------------------------
        # 2.1. Vector de características (FashionCLIP) -> Normalizado L2 [cite: 2924]
        embedding_ndarray = calcular_embedding(img=imagen, processor=processor, model=model)
        # CRÍTICO: Convertir np.ndarray a list[float] para que supabase-py lo acepte como JSON 
        embedding_lista = embedding_ndarray.tolist()

        # 2.2. Color predominante
        color_predominante = detectar_color_prenda(imagen)['hex']

        # 2.3. Categoría estándar normalizada para el generador de outfits
        family_standar = reconocer_prenda(imagen, processor, model)

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
            # Si el esquema incluye stock y campos de recomendación opcionales:
            "en_stock": False,
            "ocasion": ocasion or [],
            "inspiracion": estilo_estetico or []
        }

        # Si habéis configurado un campo usuario_id en BD para ropa subida por usuarios
        if usuario_id:
            datos_prenda["usuario_id"] = usuario_id

        # ---------------------------------------------------------------------
        # PASO 4: Inserción en la tabla de base de datos
        # ---------------------------------------------------------------------
        respuesta = supabase.table(PRENDAS_TABLA).insert(datos_prenda).execute()

        if not respuesta.data:
            raise RuntimeError("La base de datos no devolvió datos tras el insert en PRENDAS.")

        print(f"✅ Prenda guardada con éxito en BD: ID {respuesta.data[0].get('id')} ({nombre})")
        return respuesta.data[0]

    except Exception as e:
        print(f"❌ Error al registrar la prenda '{nombre}' en base de datos: {str(e)}")
        raise e


'''
ruta_local = "./data/ejemplo.jpg"
imagen_pil: Image.Image = Image.open(ruta_local)
imagen = imagen_pil.convert("RGB")

registrar_prenda_bd(
    supabase,
    imagen,
    'prueba 1',
    0,
    'marca',
    2026,
    'verano',
    'sección',
    'camiseta',
    processor,
    model,
    usuario_id = 0000
)
'''