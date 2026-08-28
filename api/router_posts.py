import httpx
from fastapi import APIRouter, HTTPException, Request
from openai import OpenAI

from core.config import LLM_API_KEY, ID_PRENDA, SLOT_PRENDA
from core.api_client import cliente_api

# Importamos la lógica de IA y CRUD
from ia.ejecutar_pipeline_outfit import ejecutar_pipeline_outfit
from crud.outfits import registrar_outfit_bd
from crud.posts import registrar_post_bd, obtener_posts_recomendados
from crud.prendas import obtener_prenda_aleatoria
from services.generador_contenido import generar_metadatos_hibridos

router = APIRouter(
    prefix="/posts",
    tags=["Feed Automático"]
)

openai_client = OpenAI(api_key=LLM_API_KEY)

@router.post("/generar-automatico")
async def generar_post_automatico(request: Request):
    """
    Flujo 100% autónomo:
    1. Coge una prenda aleatoria del catálogo.
    2. La usa como 'ancla' para que la IA genere el resto del outfit.
    3. Guarda el outfit en base de datos.
    4. Genera el pie de foto con LLM.
    5. Guarda el post final en el feed.
    """
    try:
        # 1. Obtener prenda semilla
        prenda_base = await obtener_prenda_aleatoria()
        prenda_id = prenda_base[ID_PRENDA]
        slot_prenda = prenda_base[SLOT_PRENDA]
        
        prendas_input = {slot_prenda: prenda_id}

        # 2. Generar el Outfit completo con tu modelo PyTorch
        prendas_db, outfit_generado = await ejecutar_pipeline_outfit(
            app_state=request.app.state,
            prendas_input_dict=prendas_input,
            historial_ids=[], # No hay usuario, es un bot
            texto=None,       # No hay petición de texto
            openai_client=openai_client
        )
        
        # 3. Recopilar todos los IDs (la prenda base + las prendas generadas)
        ids_totales = [prenda_id] + [p[ID_PRENDA] for p in outfit_generado]
        
        # 4. Registrar el Outfit en la BD
        outfit_id = await registrar_outfit_bd(
            ids_prendas=ids_totales, 
            nombre="Look Automático IA",
            user_id="bot_outfit_ai" # Identificador para saber que lo creó el sistema
        )
        
        if not outfit_id:
            raise HTTPException(status_code=500, detail="Fallo al registrar el outfit.")

        # 5. Generar pie de foto con el LLM
        # (Pasas el cliente y la info que tu LLM necesite para inspirarse)
        metadatos = await generar_metadatos_hibridos(
            outfit_id=outfit_id,
            openai_client=openai_client
        )
        pie_de_foto = metadatos.get("pie_de_foto", "¡Inspiración del día creada por OutfitAI!")

        # 6. Registrar el Post en la BD
        post_id = await registrar_post_bd(
            outfit_id=outfit_id,
            usuario_id="bot_outfit_ai",
            imagen_cuerpo_entero=None, # Como es automático, no hay foto real puesta
            pie_de_foto=pie_de_foto
        )

        return {
            "status": "success",
            "mensaje": "Post automático publicado en el feed.",
            "post_id": post_id,
            "outfit_id": outfit_id,
            "pie_de_foto": pie_de_foto,
            "prendas_incluidas": ids_totales
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())

@router.get("/feed/{usuario_id}")
async def ver_feed_usuario(usuario_id: str, limite: int = 10, pagina: int = 1):
    """
    Devuelve los posts recomendados para el feed principal de un usuario.
    """
    try:
        posts = await obtener_posts_recomendados(usuario_id, limite, pagina)
        
        return {
            "status": "success",
            "pagina": pagina,
            "resultados": len(posts),
            "feed": posts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al cargar el feed.")