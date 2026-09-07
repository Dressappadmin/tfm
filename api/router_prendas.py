import asyncio
from fastapi import APIRouter, HTTPException, Request
import httpx 
from crud.prendas import actualizar_prenda_por_id
from crud.storage import cargar_imagen_bucket
from schemas.ProcesarPrendaRequest import ProcesarPrendaRequest
from services.procesar_imagen import procesar_imagen
from utils.helpers import detectar_slot 
from core.api_client import URL_ARMARIO_USUARIOS

from core.config import (
    COLOR_PRENDA, 
    EMBEDDING_PRENDA, 
    TIPO_PRENDA, 
    SLOT_PRENDA
)

# Definimos el router
router = APIRouter(
    prefix="/prendas", 
    tags=["Gestión de Prendas"]
)

@router.post("/procesar-ia")
async def procesar_datos_prenda_ia(
    payload: ProcesarPrendaRequest,
    request: Request
):
    """
    Dada una prenda existente en la BD, descarga su imagen, extrae
    fondo, color y embedding mediante IA, y actualiza sus columnas respectivas.
    """
    try:
        # Extraemos el nombre/extensión de la prenda desde el body
        prenda_ext = payload.prenda_ext

        # 1. Recuperar datos de la prenda usando nuestra nueva API de datos
        prenda_id = prenda_ext.split('.')[0]

        url_imagen = URL_ARMARIO_USUARIOS + prenda_ext
        if not url_imagen:
            raise HTTPException(status_code=400, detail="La prenda seleccionada no tiene una URL de imagen.")

        # 2. Descargamos la imagen original desde la URL
        try:
            img = await cargar_imagen_bucket(url_imagen)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar la imagen desde la URL: {e}")

        # 3. Recuperamos los modelos pesados de la RAM (cargados en main.py)
        ml_models = request.app.state.ml_models
        processor = ml_models["processor"]
        model = ml_models["model"]
        remover = ml_models["remover"]

        # 4. Procesamiento IA (en hilo secundario)
        embedding_img, tipo_img, color_img = await asyncio.to_thread(
            procesar_imagen, img, processor, model, remover
        )

        slot = detectar_slot(tipo_img)

        # 5. Actualizamos las columnas a través de nuestra API de datos
        datos_actualizacion = {
            EMBEDDING_PRENDA: embedding_img,
            COLOR_PRENDA: color_img['hex'],
            TIPO_PRENDA: tipo_img,      
            SLOT_PRENDA: slot
        }
        
        try:
            await actualizar_prenda_por_id(datos_actualizacion)
        except httpx.HTTPStatusError as e:
             raise HTTPException(status_code=500, detail=f"Error interno al actualizar la base de datos: {e.response.text}")

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