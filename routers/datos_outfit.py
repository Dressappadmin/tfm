import numpy as np
from fastapi import APIRouter, HTTPException
from openai import OpenAI

from data.supabase import supabase
from config import LLM_API_KEY, OUTFITS_TABLA, PRENDAS_TABLA, ID_PRENDA, ID_OUTFIT, IDS_PRENDAS_OUTFIT, EMBEDDING_PRENDA, EMBEDDING_OUTFIT

# Definimos el Router
router = APIRouter(
    prefix="/outfits", 
    tags=["Gestión de Outfits"]
)

openai_client = OpenAI(api_key=LLM_API_KEY)

@router.put("/datos_outfit/{outfit_id}")
async def datos_outfit(outfit_id: str):
    """
    Calcula el vector característico (embedding) de un outfit como
    la media normalizada de los embeddings de sus prendas y lo guarda en BD.
    """
    try:
        # 1. Recuperar los IDs de las prendas del outfit
        resp_outfit = supabase.table(OUTFITS_TABLA).select("prendas_ids").eq(ID_PRENDA, outfit_id).execute()
        
        if not resp_outfit.data:
            raise HTTPException(status_code=404, detail="Outfit no encontrado.")
            
        prendas_ids = resp_outfit.data[0].get(IDS_PRENDAS_OUTFIT, [])
        if not prendas_ids:
            raise HTTPException(status_code=400, detail="El outfit no tiene prendas asignadas.")

        # 2. Recuperar los embeddings de esas prendas
        resp_prendas = supabase.table(PRENDAS_TABLA).select(EMBEDDING_PRENDA).in_(ID_PRENDA, prendas_ids).execute()
        
        embeddings_list = [prenda[EMBEDDING_PRENDA] for prenda in resp_prendas.data if prenda.get(EMBEDDING_PRENDA)]
        
        if not embeddings_list:
            raise HTTPException(status_code=400, detail="Las prendas de este outfit no tienen embeddings calculados.")

        # 3. Matemáticas: Calcular el embedding del outfit
        # El embedding de un conjunto se suele calcular como la media de sus prendas
        matriz_embeddings = np.array(embeddings_list) # Convertimos a matriz NumPy
        
        # Calculamos la media por columnas (axis=0)
        outfit_embedding_raw = np.mean(matriz_embeddings, axis=0)
        
        # Es CRÍTICO normalizar el vector resultante para que la similitud Coseno funcione bien luego
        norma = np.linalg.norm(outfit_embedding_raw)
        outfit_embedding_normalized = outfit_embedding_raw / norma if norma > 0 else outfit_embedding_raw

        # Convertimos de vuelta a lista de Python estricta (floats) para guardarlo en la BD (pgvector)
        outfit_embedding_final = outfit_embedding_normalized.tolist()

        # 4. Actualizar la tabla OUTFITS en Supabase
        update_bd = supabase.table(OUTFITS_TABLA).update({EMBEDDING_OUTFIT: outfit_embedding_final}).eq(ID_OUTFIT, outfit_id).execute()

        if not update_bd.data:
            raise HTTPException(status_code=500, detail="Error interno al actualizar el embedding en Supabase.")

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