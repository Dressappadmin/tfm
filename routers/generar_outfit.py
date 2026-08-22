import asyncio
import numpy as np

from fastapi import APIRouter, HTTPException, Body, Request
from openai import OpenAI

# 1. CONFIGURACIÓN Y CLIENTES
from config import LLM_API_KEY, PRENDAS_TABLA, COL_ID, COL_EMBEDDING, COL_COLOR, COL_TIPO_PRENDA, USE_ADVANCED_MODEL
from data.supabase import supabase

# 2. SCHEMAS DE VALIDACIÓN
from schemas.GenerarOutfitExistenteRequest import GenerarOutfitExistenteRequest

# 3. MÓDULOS DE LÓGICA DE IA
from modulos.procesar_texto import procesar_texto
from modulos.completar_outfit import completar_outfit_con_texto

# Definimos el Router
router = APIRouter(tags=["Generación Multimodal"])
openai_client = OpenAI(api_key=LLM_API_KEY)

@router.post("/generar-desde-existente")
async def generar_outfit(
    request: Request,
    datos: GenerarOutfitExistenteRequest = Body(...)
):
    """
    Genera un outfit a partir de una prenda que el usuario ya tiene guardada en su perfil/BD.
    """
    try:
        from data.catalogos import prendas as catalogo

        # Recuperamos los modelos desde el estado global de la aplicación (cargados en main.py)
        ml_models = request.app.state.ml_models
        processor = ml_models["processor"]
        model = ml_models["model"]

        # 1. Buscamos la prenda seleccionada en Supabase
        respuesta = await asyncio.to_thread(
            lambda: supabase.table(PRENDAS_TABLA).select("*").eq(COL_ID, datos.prenda_id).single().execute()
        )
        
        prenda_base = respuesta.data
        if not prenda_base:
            raise HTTPException(status_code=404, detail="La prenda seleccionada no existe en tu armario.")

        # Extraemos los datos que YA estaban calculados
        embedding_final = prenda_base.get(COL_EMBEDDING)
        tipo_prenda_final = prenda_base.get(COL_TIPO_PRENDA, "OTRO")
        color_final_hex = prenda_base.get(COL_COLOR, "#FFFFFF")
        etiquetas_ai = None
        embedding_texto_puro = None

        # 2. Si el usuario añadió texto opcional (ej: "combínalo para la playa"), fusionamos con el texto
        if datos.texto:
            # procesar_texto extraerá las etiquetas y el embedding del prompt
            emb_txt, etiquetas_ai = await asyncio.to_thread(
                procesar_texto, datos.texto, openai_client, processor, model
            )
            embedding_texto_puro = emb_txt
            
            # Fusión del vector existente con el vector del nuevo texto
            if embedding_final:
                embedding_final = (np.array(embedding_final) + emb_txt) / 2.0
                embedding_final = embedding_final / np.linalg.norm(embedding_final)

        # 3. Generamos las prendas complementarias con el motor de IA
        prendas_complementarias = await asyncio.to_thread(
            completar_outfit_con_texto,
            tipo_prenda=tipo_prenda_final,
            top_n=10,
            temperatura=0.2,
            color_hex=color_final_hex,
            query_emb=embedding_final,
            catalog=catalogo,
            etiquetas=etiquetas_ai,
            embedding_texto=embedding_texto_puro
        )

        # 4. Construimos la lista final de IDs (Prenda base + prendas recomendadas)
        ids_finales = [datos.prenda_id]
        ids_finales.extend([p.get(COL_ID) for p in prendas_complementarias])

        return {
            "status": "success",
            "prenda_origen": prenda_base,
            "outfit_generado": prendas_complementarias,
            "ids_outfit": ids_finales,
            "mensaje": "Outfit generado desde tu armario correctamente."
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())