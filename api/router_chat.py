import asyncio
import json
from fastapi import APIRouter, HTTPException, Request, Body
from openai import OpenAI

from core.config import LLM_API_KEY
from utils.catalogos import VOCABULARIO_TAGS
from schemas.ChatRequest import ChatRequest

# Importamos la lógica interna y la función de BD
from ia.ejecutar_pipeline_outfit import ejecutar_pipeline_outfit 
from crud.prendas import obtener_prenda_por_id

router = APIRouter(tags=["Interfaz Conversacional"])
openai_client = OpenAI(api_key=LLM_API_KEY)

HERRAMIENTAS_CHAT = [
    {
        "type": "function",
        "function": {
            "name": "generar_outfit_pytorch",
            "description": "Llama al motor de Deep Learning para generar un outfit completo. Úsalo SIEMPRE que el usuario pida recomendaciones de ropa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "etiquetas_extraidas": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": VOCABULARIO_TAGS 
                        },
                        "description": "Clasifica la petición del usuario usando ÚNICAMENTE las etiquetas de esta lista."
                    },
                    "color_solicitado": {
                        "type": "string",
                        "description": "Color principal deseado en formato HEX (ej: '#FF0000'). Null si no especifica."
                    }
                },
                "required": ["etiquetas_extraidas"]
            }
        }
    }
]

@router.post("/chat")
async def conversacion_ia(
    request: Request,
    datos: ChatRequest = Body(...)
):
    try:
        MAX_MENSAJES = 6 
        mensajes_recientes = datos.mensajes[-MAX_MENSAJES:] 
        
        # Como Pydantic ya fuerza a que sea "user" o "assistant", el check de != "system" es un extra de seguridad
        mensajes_formateados = [
            {"role": m.role, "content": m.content} 
            for m in mensajes_recientes 
            if m.role != "system"
        ]
        
        system_prompt = {
            "role": "system",
            "content": f"Eres el asistente personal de estilo de DressApp. Eres amable y experto en moda. Si el usuario pide un look, usa la función generar_outfit_pytorch. Las categorías válidas son: {', '.join(VOCABULARIO_TAGS)}. Adapta el lenguaje del usuario a estas categorías."
        }

        mensajes_formateados.insert(0, system_prompt)

        respuesta_llm = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4o-mini",
            messages=mensajes_formateados,
            tools=HERRAMIENTAS_CHAT,
            tool_choice="auto" 
        )

        mensaje_respuesta = respuesta_llm.choices[0].message
        
        if mensaje_respuesta.tool_calls:
            tool_call = mensaje_respuesta.tool_calls[0]
            
            if tool_call.function.name == "generar_outfit_pytorch":
                argumentos = json.loads(tool_call.function.arguments)
                tags = argumentos.get("etiquetas_extraidas", [])
                color_llm = argumentos.get("color_solicitado", None)
                
                # --- NUEVA LÓGICA DE PRENDAS (Igual que en el Endpoint 3) ---
                prendas_input_dict = {}
                color_prenda = None
                
                if datos.contexto_prenda_id:
                    for prenda_id in datos.contexto_prenda_id:
                        prenda_db = await obtener_prenda_por_id(prenda_id)
                        
                        if prenda_db:
                            slot = prenda_db.get("slot")
                            color = prenda_db.get("color")
                            
                            if slot:
                                prendas_input_dict[slot] = prenda_id
                            
                            if color and color_prenda is None:
                                color_prenda = color

                # Priorizamos el color que el usuario haya pedido en el chat. 
                # Si no pidió ninguno, usamos el color de la prenda de contexto.
                color_final = color_llm if color_llm else color_prenda
                
                outfit_generado = await ejecutar_pipeline_outfit(
                    app_state=request.app.state,
                    usuario_id=datos.usuario_id,
                    prendas_input=prendas_input_dict,
                    tags_llm=tags,
                    color_hex=color_final
                )
                
                return {
                    "tipo": "OUTFIT_GENERADO",
                    "mensaje_texto": "¡Aquí tienes una propuesta basada en lo que me has pedido!",
                    "datos_outfit": outfit_generado,
                    "debug_tags_usados": tags
                }

        return {
            "tipo": "TEXTO_PLANO",
            "mensaje_texto": mensaje_respuesta.content,
            "datos_outfit": None
        }

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())