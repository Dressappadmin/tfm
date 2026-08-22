import asyncio
import json
from fastapi import APIRouter, HTTPException, Request, Body
from openai import OpenAI

from config import LLM_API_KEY
from schemas.ChatRequest import ChatRequest

# Importamos la lógica interna de tu red neuronal (asumiendo que la extrajiste a una función)
# de modo que tanto el endpoint directo como el chat puedan usarla.
from modulos.ia_pytorch import ejecutar_pipeline_outfit 

router = APIRouter(tags=["Interfaz Conversacional"])
openai_client = OpenAI(api_key=LLM_API_KEY)

# Definimos la herramienta (Tool) para el LLM
HERRAMIENTAS_CHAT = [
    {
        "type": "function",
        "function": {
            "name": "generar_outfit_pytorch",
            "description": "Llama al motor de Deep Learning para generar un outfit completo. Úsalo SIEMPRE que el usuario pida recomendaciones de ropa, qué ponerse, o cómo combinar algo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "etiquetas_extraidas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de etiquetas exactas de la taxonomía (ej: 'Casual', 'Verano', 'Fiesta')."
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
        # 1. Preparamos el historial de mensajes para OpenAI
        mensajes_formateados = [{"role": m.role, "content": m.content} for m in datos.mensajes]
        
        # Inyectamos un System Prompt robusto
        system_prompt = {
            "role": "system",
            "content": "Eres el asistente personal de estilo de OutfitAI. Tu objetivo es ayudar al usuario a encontrar qué ponerse. Eres amable, conciso y experto en moda. Si el usuario te pide un look, DEBES usar la función generar_outfit_pytorch para dárselo."
        }
        mensajes_formateados.insert(0, system_prompt)

        # 2. Llamada a GPT-4o-mini
        respuesta_llm = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4o-mini",
            messages=mensajes_formateados,
            tools=HERRAMIENTAS_CHAT,
            tool_choice="auto" # El modelo decide si responde con texto o llama a la herramienta
        )

        mensaje_respuesta = respuesta_llm.choices[0].message
        
        # 3. ¿El LLM decidió usar la red neuronal?
        if mensaje_respuesta.tool_calls:
            tool_call = mensaje_respuesta.tool_calls[0]
            
            if tool_call.function.name == "generar_outfit_pytorch":
                # Extraemos los argumentos que el LLM dedujo del chat
                argumentos = json.loads(tool_call.function.arguments)
                tags = argumentos.get("etiquetas_extraidas", [])
                color = argumentos.get("color_solicitado", None)
                
                # Ejecutamos tu pipeline de PyTorch (el que creamos en el paso anterior)
                # Pasamos los inputs que tengamos (el contexto de la prenda si lo hay, el historial del usuario, etc.)
                outfit_generado = await ejecutar_pipeline_outfit(
                    app_state=request.app.state,
                    usuario_id=datos.usuario_id,
                    prendas_input=datos.contexto_prenda_id or {},
                    tags_llm=tags,
                    color_hex=color
                )
                
                return {
                    "tipo": "OUTFIT_GENERADO",
                    "mensaje_texto": "¡Aquí tienes una propuesta basada en lo que me has pedido!",
                    "datos_outfit": outfit_generado,
                    "debug_tags_usados": tags
                }

        # 4. Si el LLM solo quiso hablar (ej: "¡Hola! ¿En qué te ayudo hoy?")
        return {
            "tipo": "TEXTO_PLANO",
            "mensaje_texto": mensaje_respuesta.content,
            "datos_outfit": None
        }

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())