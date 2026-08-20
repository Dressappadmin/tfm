import asyncio
from fastapi import APIRouter, HTTPException, Request

# Importamos tu cliente de base de datos y tus módulos
from data.supabase import supabase
from modulos.procesar_imagen import procesar_imagen
from utils.detectar_slot import detectar_slot
from utils.cargar_imagen_url_bucket import cargar_imagen_url_bucket
from config import PRENDAS_TABLA, ID_PRENDA, IMG_URL_PRENDA, COLOR_PRENDA, EMBEDDING_PRENDA, TIPO_PRENDA, SLOT_PRENDA

# Definimos el router con un prefijo para que todas las rutas cuelguen de /prendas
router = APIRouter(
    prefix="/prendas", 
    tags=["Gestión de Prendas"]
)

@router.put("/datos_prenda/{prenda_id}")
async def datos_prenda(
    prenda_id: str,
    request: Request
):
    """
    Dada una prenda existente en la BD, descarga su imagen, extrae
    fondo, color y embedding, y actualiza sus columnas respectivas.
    Las columnas actualizadas son:
    - embedding
    - color
    - tipo prenda
    - slot prenda
    """
    try:
        # 1. Recuperar la URL de la imagen en Supabase
        # Asegúrate de que tu columna se llama "url_imagen"
        respuesta_bd = supabase.table(PRENDAS_TABLA).select(IMG_URL_PRENDA).eq(ID_PRENDA, prenda_id).execute()
        
        if not respuesta_bd.data:
            raise HTTPException(status_code=404, detail="Prenda no encontrada en la base de datos.")
            
        url_imagen = respuesta_bd.data[0].get(IMG_URL_PRENDA)
        if not url_imagen:
            raise HTTPException(status_code=400, detail="La prenda seleccionada no tiene una URL de imagen.")

        # 2. Descargamos la imagen original desde la URL
        try:
            img = await cargar_imagen_url_bucket(url_imagen)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar la imagen desde la URL: {e}")

        # 3. Recuperamos los modelos pesados de la RAM (cargados en el lifespan de main.py)
        ml_models = request.app.state.ml_models
        processor = ml_models["processor"]
        model = ml_models["model"]
        remover = ml_models["remover"]

        # 4. Procesamiento IA (en hilo secundario para no bloquear el servidor)
        embedding_img, tipo_img, color_img = await asyncio.to_thread(
            procesar_imagen, img, processor, model, remover
        )

        slot = detectar_slot(tipo_img)

        # 5. Actualizamos las columnas en Supabase
        # Cambia "embedding", "color", y "family" si tus columnas se llaman distinto.
        datos_actualizacion = {
            EMBEDDING_PRENDA: embedding_img,
            COLOR_PRENDA: color_img['hex'],
            TIPO_PRENDA: tipo_img,      
            SLOT_PRENDA: slot
        }
        
        # Realizamos el UPDATE en la BD
        update_bd = supabase.table(PRENDAS_TABLA).update(datos_actualizacion).eq(ID_PRENDA, prenda_id).execute()
        
        if not update_bd.data:
            raise HTTPException(status_code=500, detail="Error interno al actualizar la base de datos.")

        # 6. Respuesta exitosa
        return {
            "status": "success",
            "mensaje": "Prenda procesada y actualizada correctamente.",
            "prenda_id": prenda_id,
            "metadata_ai": {
                "tipo_detectado": tipo_img,
                "color_hex": color_img['hex'],
                "slot": slot
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())