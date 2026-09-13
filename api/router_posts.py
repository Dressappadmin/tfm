from fastapi import APIRouter, HTTPException, Request
import traceback
from openai import OpenAI
from core.config import LLM_API_KEY, ID_PRENDA, SLOT_PRENDA
from ia.ejecutar_pipeline_outfit import ejecutar_pipeline_outfit
from crud.posts import obtener_posts_recomendados
from crud.prendas import obtener_prenda_aleatoria

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)
openai_client = OpenAI(api_key=LLM_API_KEY)

# ---------------------------------------------------------
# ENDPOINT 1: GENERAR UN POST
# ---------------------------------------------------------
@router.post("/generar-post")
async def generar_post_automatico(request: Request):
    '''
    Genera de forma autónoma una propuesta de outfit completa utilizando una prenda aleatoria del catálogo como ancla, crea una descripción atractiva para redes sociales mediante un modelo de lenguaje y devuelve ambos elementos sin guardarlos en la base de datos.

    Parameters
    ----------
    request : Request
        Objeto de solicitud de FastAPI que proporciona acceso al estado global de la aplicación.

    Returns
    ----------
    dict
        Estructura que contiene el outfit completo generado y la descripción optimizada para redes sociales.
    '''
    try:
        prenda_base = await obtener_prenda_aleatoria()
        prenda_id = prenda_base[ID_PRENDA]
        slot_prenda = prenda_base[SLOT_PRENDA]
        
        prendas_input = {slot_prenda: prenda_id}

        outfit_completo = await ejecutar_pipeline_outfit(
            app_state=request.app.state,
            prendas_input_dict=prendas_input,
            historial_ids=[],
            texto=None,       
            openai_client=openai_client
        )

        nombres_prendas = [p.get("tipo_prenda", "prenda") for p in outfit_completo]
        
        prompt = (
            f"Crea un copy o descripción muy atractiva para redes sociales (Instagram/TikTok) "
            f"para un outfit que incluye las siguientes prendas: {', '.join(nombres_prendas)}.\n"
            f"Usa un tono fresco, natural y añade un par de emojis relevantes."
        )

        respuesta = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "Eres el editor jefe de moda de una app de estilo. Escribes textos que maximizan los likes."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        descripcion = respuesta.choices[0].message.content.strip()

        return {
            "outfit": outfit_completo,
            "descripcion": descripcion
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

# ---------------------------------------------------------
# ENDPOINT 2: CALCULAR POSTS PARA MOSTRAR EN EL FEED
# ---------------------------------------------------------
@router.post("/generar-feed")
async def ver_feed_usuario(usuario_id: str, limite: int = 10, pagina: int = 1):
    '''
    Obtiene y devuelve los posts recomendados para estructurar el feed principal de un usuario específico, con soporte para paginación y límite de resultados.

    Parameters
    ----------
    usuario_id : str
        Identificador único del usuario para el cual se generan las recomendaciones del feed.
    limite : int, optional
        Número máximo de posts a devolver por página (por defecto es 10).
    pagina : int, optional
        Número de página actual para la paginación de resultados (por defecto es 1).

    Returns
    ----------
    dict
        Estructura JSON con el estado de la operación, la página actual, la cantidad de resultados obtenidos y la lista de posts del feed.
    '''
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
