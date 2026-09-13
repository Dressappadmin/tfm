from typing import List
from openai import AsyncOpenAI
from core.config import LLM_API_KEY
from crud.prendas import obtener_prenda_aleatoria
from ia.ejecutar_pipeline_outfit import ejecutar_pipeline_outfit

client = AsyncOpenAI(api_key=LLM_API_KEY)

async def generador_contenido(app_state, usuario_id: str, tags_estilo: List[str] = None):
    '''
    Genera un outfit completo partiendo de una prenda aleatoria como base y redacta una descripción atractiva optimizada para redes sociales utilizando un modelo de lenguaje.

    Parameters
    ----------
    app_state : object
        Objeto que almacena el estado global de la aplicación, necesario para ejecutar el pipeline de generación.
    usuario_id : str
        Identificador único del usuario para el cual se personaliza y genera el outfit.
    tags_estilo : list, optional
        Lista de etiquetas o tags de estilo para condicionar la generación de las prendas (por defecto es None, en cuyo caso se asigna ["casual"]).

    Returns
    ----------
    tuple
        Una tupla que contiene el outfit completo generado (como lista o estructura de datos) y la cadena de texto con la descripción atractiva para redes sociales.
    '''
    if tags_estilo is None:
        tags_estilo = ["casual"]

    prenda = await obtener_prenda_aleatoria()
    
    prenda_id = prenda.get("id") if isinstance(prenda, dict) else getattr(prenda, "id", str(prenda))

    outfit = await ejecutar_pipeline_outfit(
        app_state=app_state,
        usuario_id=usuario_id,
        prendas_input=[prenda_id],
        tags_llm=tags_estilo,
        temperatura=0.7
    )

    if isinstance(outfit, list):
        nombres_prendas = [item.get("tipo_prenda", "prenda") for item in outfit]
    else:
        nombres_prendas = ["varias prendas seleccionadas"]
    
    prompt = (
        f"Crea un copy o descripción muy atractiva para redes sociales (Instagram/TikTok) "
        f"para un outfit que incluye las siguientes prendas: {', '.join(nombres_prendas)}.\n"
        f"Usa un tono fresco, natural y añade un par de emojis relevantes."
    )

    respuesta = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "Eres el editor jefe de moda de una app de estilo. Escribes textos que maximizan los likes."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )
    
    descripcion = respuesta.choices[0].message.content.strip()

    return outfit, descripcion