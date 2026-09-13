import asyncio
from fastapi import APIRouter, HTTPException, Request
import httpx 
from crud.prendas import actualizar_prenda_por_id
from crud.storage import cargar_imagen_bucket
from schemas.ProcesarPrendaRequest import ProcesarPrendaRequest
from services.procesar_imagen import procesar_imagen
from utils.helpers import detectar_slot 
from core.config import URL_BUCKET_PRENDAS

from core.config import (
    COLOR_PRENDA, 
    EMBEDDING_PRENDA, 
    TIPO_PRENDA, 
    SLOT_PRENDA
)

router = APIRouter(
    prefix="/prendas", 
    tags=["Gestión de Prendas"]
)

@router.post("/procesar-ia")
async def procesar_datos_prenda_ia(
    payload: ProcesarPrendaRequest,
    request: Request
):
    '''
    Procesa mediante Inteligencia Artificial una prenda existente descargando su imagen, extrayendo características clave como el fondo, color, embedding y categoría, y actualiza los registros correspondientes en la base de datos.

    Parameters
    ----------
    payload : ProcesarPrendaRequest
        Cuerpo de la petición que incluye los datos extendidos o el identificador de archivo de la prenda.
    request : Request
        Objeto de solicitud de FastAPI que proporciona acceso al estado global de la aplicación, incluidos los modelos de Machine Learning cargados.

    Returns
    ----------
    dict
        Diccionario con el estado de la operación, un mensaje de éxito, el identificador de la prenda procesada y los metadatos de IA obtenidos (tipo, color en hexadecimal y slot).
    '''
    try:
        prenda_ext = payload.prenda_ext

        prenda_id = prenda_ext.split('.')[0]

        url_imagen = URL_BUCKET_PRENDAS + prenda_ext
        if not url_imagen:
            raise HTTPException(status_code=400, detail="La prenda seleccionada no tiene una URL de imagen.")

        try:
            img = await cargar_imagen_bucket(url_imagen)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar la imagen desde la URL: {e}")

        ml_models = request.app.state.ml_models
        processor = ml_models["processor"]
        model = ml_models["model"]
        remover = ml_models["remover"]

        embedding_img, tipo_img, color_img = await asyncio.to_thread(
            procesar_imagen, img, processor, model, remover
        )

        slot = detectar_slot(tipo_img)

        datos_actualizacion = {
            EMBEDDING_PRENDA: embedding_img.tolist(),
            COLOR_PRENDA: [color_img['hex']], 
            TIPO_PRENDA: tipo_img,      
            SLOT_PRENDA: slot
        }
        
        try:
            await actualizar_prenda_por_id(datos_actualizacion, prenda_id)
        except httpx.HTTPStatusError as e:
             raise HTTPException(status_code=500, detail=f"Error interno al actualizar la base de datos: {e.response.text}")

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