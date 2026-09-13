import numpy as np
import httpx
from fastapi import APIRouter, HTTPException, Request
from core.config import SLOT_PRENDA, EMBEDDING_PRENDA, IDS_PRENDAS_OUTFIT, COLOR_PRENDA
from schemas.ValidarOutfitRequest import ValidarOutfitRequest
from schemas.OutfitEmbeddingRequest import OutfitEmbeddingRequest
from schemas.GenerarOutfitRequest import GenerarOutfitRequest
from services.validar_reglas_outfit import validar_reglas_outfit
from ia.ejecutar_pipeline_outfit import ejecutar_pipeline_outfit 
from crud.prendas import obtener_varias_prendas_por_id
from crud.outfits import obtener_outfit_por_id, actualizar_outfit_por_id

router = APIRouter(
    prefix="/outfits", 
    tags=["Gestión de Outfits"]
)

# ---------------------------------------------------------
# ENDPOINT 1: VALIDAR COMBINACIÓN DE PRENDAS
# ---------------------------------------------------------
@router.post("/validar")
async def validar_outfit(request: ValidarOutfitRequest):
    '''
    Valida si un conjunto de identificadores de prendas de vestir cumple con las reglas básicas de combinación para formar un outfit correcto.

    Parameters
    ----------
    request : ValidarOutfitRequest
        Objeto de la petición que contiene la lista de identificadores de las prendas a validar.

    Returns
    ----------
    dict
        Diccionario con el estado de la validación ('success' o 'invalid'), un mensaje descriptivo y las categorías o slots correspondientes a las prendas evaluadas.
    '''
    try:
        prendas_ids = request.prendas_ids

        if not prendas_ids:
            raise HTTPException(status_code=400, detail="La lista de prendas está vacía.")

        try:
            prendas_db = await obtener_varias_prendas_por_id(prendas_ids)
        except httpx.HTTPError:
            raise HTTPException(status_code=404, detail="Error al buscar las prendas en la BD.")

        if not prendas_db:
             raise HTTPException(status_code=404, detail="No se encontraron las prendas indicadas.")

        # Extraemos los slots
        slots_prendas = [prenda.get(SLOT_PRENDA) for prenda in prendas_db if prenda.get(SLOT_PRENDA)]

        # Validamos usando la función de reglas dura
        es_valido = validar_reglas_outfit(slots_prendas)
        mensaje = "Outfit válido" if es_valido else "Faltan prendas básicas (Top/Bottom o Vestido)."

        if not es_valido:
            return {"status": "invalid", "mensaje": mensaje, "categorias": slots_prendas}

        return {
            "status": "success",
            "mensaje": "El outfit cumple con las reglas de moda.",
            "categorias": slots_prendas
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())

# ---------------------------------------------------------
# ENDPOINT 2: CALCULAR CAMPOS DEL OUTFIT
# ---------------------------------------------------------
@router.post("/calcular-embedding")
async def calcular_embedding_outfit(request: OutfitEmbeddingRequest):
    """
    Calcula el vector característico (embedding) de un outfit como
    la media normalizada de los embeddings de sus prendas y lo guarda.
    """
    try:
        outfit_id = request.outfit_id

        try:
            outfit_data = await obtener_outfit_por_id(outfit_id)
        except httpx.HTTPError:
             raise HTTPException(status_code=404, detail="Outfit no encontrado.")
            
        prendas_ids = outfit_data.get(IDS_PRENDAS_OUTFIT, [])
        if not prendas_ids:
            raise HTTPException(status_code=400, detail="El outfit no tiene prendas asignadas.")

        prendas_db = await obtener_varias_prendas_por_id(prendas_ids)
        embeddings_list = [p[EMBEDDING_PRENDA] for p in prendas_db if p.get(EMBEDDING_PRENDA)]
        
        if not embeddings_list:
            raise HTTPException(status_code=400, detail="Las prendas de este outfit no tienen embeddings.")

        matriz_embeddings = np.array(embeddings_list) 
        outfit_embedding_raw = np.mean(matriz_embeddings, axis=0)
        
        norma = np.linalg.norm(outfit_embedding_raw)
        outfit_embedding_normalized = outfit_embedding_raw / norma if norma > 0 else outfit_embedding_raw

        outfit_embedding_final = outfit_embedding_normalized.tolist()

        try:
            await actualizar_outfit_por_id(outfit_id, outfit_embedding_final)
        except httpx.HTTPError:
             raise HTTPException(status_code=500, detail="Error interno al actualizar el embedding en la BD.")

        return {
            "status": "success",
            "mensaje": f"Embedding calculado (promedio de {len(embeddings_list)} prendas) y guardado.",
            "outfit_id": outfit_id,
            "dimensiones": len(outfit_embedding_final)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())

# ---------------------------------------------------------
# ENDPOINT 3: GENERAR OUTFIT AVANZADO (IA MULTIMODAL)
# ---------------------------------------------------------
@router.post("/generar")
async def generar_outfit_avanzado(
    request: Request,
    datos: GenerarOutfitRequest
):
    '''
    Calcula el vector de embedding característico para un outfit a partir de la media normalizada de los vectores individuales de sus prendas constituyentes y almacena el resultado en la base de datos.

    Parameters
    ----------
    request : OutfitEmbeddingRequest
        Objeto de la petición que incluye el identificador único del outfit a procesar.

    Returns
    ----------
    dict
        Diccionario que indica el éxito de la operación, un mensaje informativo con estadísticas del cálculo, el ID del outfit y la dimensión del embedding resultante.
    '''
    try:
        outfit_generado = await ejecutar_pipeline_outfit(
            app_state=request.app.state,
            usuario_id=datos.usuario_id,
            prendas_input=datos.prendas_input, 
            tags_llm=datos.tags,
            temperatura=datos.temperatura       
        )

        return {
            "status": "success",
            "outfit_generado": outfit_generado,
            "mensaje": "Outfit generado"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())

        