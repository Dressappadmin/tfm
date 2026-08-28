import numpy as np
import httpx
from fastapi import APIRouter, HTTPException, Body, Request
from openai import OpenAI

# Configuración y utilidades
from core.config import LLM_API_KEY, SLOT_PRENDA, EMBEDDING_PRENDA
from schemas.ValidarOutfitRequest import ValidarOutfitRequest
from schemas.GenerarOutfitRequest import GenerarOutfitRequest

# Lógica de Negocio (Servicios)
from services.validar_reglas_outfit import validar_reglas_outfit
from ia.ejecutar_pipeline_outfit import ejecutar_pipeline_outfit 

# Lógica de Datos (CRUD a través de la API externa)
from crud.prendas import obtener_varias_prendas_por_id, obtener_prenda_por_id
from crud.outfits import obtener_outfit_por_id, actualizar_embedding_outfit

router = APIRouter(
    prefix="/outfits", 
    tags=["Gestión de Outfits"]
)

openai_client = OpenAI(api_key=LLM_API_KEY)

# ---------------------------------------------------------
# ENDPOINT 1: VALIDAR COMBINACIÓN DE PRENDAS
# ---------------------------------------------------------
@router.post("/validar")
async def validar_outfit(request: ValidarOutfitRequest):
    """
    Comprueba si una lista de IDs de prendas forman un conjunto válido.
    """
    try:
        prendas_ids = request.prendas_ids

        if not prendas_ids:
            raise HTTPException(status_code=400, detail="La lista de prendas está vacía.")

        # Sustituimos el in_() de Supabase por nuestra llamada a la API
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
# ENDPOINT 2: CALCULAR CAMPOS DEL OUTFIT (MEAN POOLING)
# ---------------------------------------------------------
@router.put("/{outfit_id}/calcular-embedding")
async def calcular_embedding_outfit(outfit_id: str):
    """
    Calcula el vector característico (embedding) de un outfit como
    la media normalizada de los embeddings de sus prendas y lo guarda.
    """
    try:
        # 1. Recuperar los IDs de las prendas del outfit vía API
        try:
            outfit_data = await obtener_outfit_por_id(outfit_id)
        except httpx.HTTPError:
             raise HTTPException(status_code=404, detail="Outfit no encontrado.")
            
        prendas_ids = outfit_data.get("ids_prendas", [])
        if not prendas_ids:
            raise HTTPException(status_code=400, detail="El outfit no tiene prendas asignadas.")

        # 2. Recuperar los embeddings de esas prendas vía API
        prendas_db = await obtener_varias_prendas_por_id(prendas_ids)
        embeddings_list = [p[EMBEDDING_PRENDA] for p in prendas_db if p.get(EMBEDDING_PRENDA)]
        
        if not embeddings_list:
            raise HTTPException(status_code=400, detail="Las prendas de este outfit no tienen embeddings.")

        # 3. Matemáticas: Calcular el embedding del outfit
        matriz_embeddings = np.array(embeddings_list) 
        outfit_embedding_raw = np.mean(matriz_embeddings, axis=0)
        
        norma = np.linalg.norm(outfit_embedding_raw)
        outfit_embedding_normalized = outfit_embedding_raw / norma if norma > 0 else outfit_embedding_raw

        outfit_embedding_final = outfit_embedding_normalized.tolist()

        # 4. Actualizar la tabla OUTFITS vía API (PATCH)
        try:
            await actualizar_embedding_outfit(outfit_id, outfit_embedding_final)
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
    datos: GenerarOutfitRequest = Body(...)
):
    """
    Endpoint principal de generación. Usa la red PyTorch y búsqueda pgvector.
    """
    try:
        # Toda la lógica de PyTorch, LLM y Base de Datos (CRUD) está abstraída 
        # dentro de esta función, que ya la adaptamos en la carpeta `ia/`
        prendas_db, outfit_generado = await ejecutar_pipeline_outfit(
            app_state=request.app.state,
            prendas_input_dict=datos.prendas_input,
            historial_ids=datos.historial_usuario_ids,
            texto=datos.texto,
            openai_client=openai_client
        )

        return {
            "status": "success",
            "prendas_input": prendas_db,
            "outfit_generado": outfit_generado,
            "mensaje": "Outfit generado inteligentemente mediante Deep Learning."
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())