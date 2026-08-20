import numpy as np
from openai import OpenAI
from transformers import CLIPProcessor, CLIPModel

from config import DEVICE
from utils.calcular_embedding_texto import calcular_embedding_texto
from schemas.OutfitMetadataAI import OutfitMetadataAI

def extraer_etiquetas(prompt_usuario: str, client: OpenAI) -> OutfitMetadataAI:
    '''
    Analiza el texto libre introducido por el usuario y extrae de forma estructurada 
    las etiquetas de moda principales (ocasión, temporalidad, inspiración, colores y prenda mencionada).

    Utiliza el endpoint de Structured Outputs de OpenAI con el modelo gpt-4o-mini y el esquema OutfitMetadataAI.

    Parameters
    ----------
    prompt_usuario : str
        El texto o consulta ingresado por el usuario (ej. "busco un outfit elegante para una boda de verano").
    client : OpenAI
        Instancia configurada del cliente de OpenAI.

    Returns
    -------
    OutfitMetadataAI
        Objeto Pydantic instanciado con los metadatos y atributos de moda extraídos del texto.
    '''
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un estilista de moda e IA experto. Analiza la petición del usuario "
                        "y extrae etiquetas clave para buscar y filtrar prendas del catálogo."
                    )
                },
                {"role": "user", "content": prompt_usuario}
            ],
            response_format=OutfitMetadataAI,
            temperature=0.1
        )
        return response.choices[0].message.parsed
    except Exception as e:
        print(f"⚠️ Error procesando el texto con el LLM: {e}")
        # Retorna el esquema con valores por defecto si ocurre algún fallo en la llamada API
        return OutfitMetadataAI()

def procesar_texto(
    prompt_usuario: str, 
    client: OpenAI,
    processor: CLIPProcessor,
    model: CLIPModel,
    device: str = DEVICE
) -> tuple[np.ndarray, OutfitMetadataAI]:
    '''
    Orquesta el procesamiento de la consulta de texto del usuario obteniendo tanto 
    su vector de características (FashionCLIP) como sus etiquetas estructuradas (LLM).

    Parameters
    ----------
    prompt_usuario : str
        El texto libre de búsqueda ingresado por el usuario.
    client : OpenAI
        Cliente de OpenAI inyectado para la extracción de etiquetas.
    processor : CLIPProcessor
        Procesador de texto de FashionCLIP.
    model : CLIPModel
        Modelo visual/lenguaje FashionCLIP.
    device : str, opcional
        Dispositivo de inferencia, por defecto constante DEVICE de config.

    Returns
    -------
    tuple[np.ndarray, OutfitMetadataAI]
        Una tupla que contiene:
        - embedding_texto: Vector de características normalizado (512 dimensiones).
        - etiquetas_ai: Las etiquetas duras extraídas para el filtrado semántico.
    '''
    # 1. Extracción del embedding espacial del texto con FashionCLIP
    embedding_texto = calcular_embedding_texto(
        texto=prompt_usuario,
        processor=processor,
        model=model,
        device=device
    )

    # 2. Extracción de metadatos/restricciones duras con el LLM (gpt-4o-mini)
    etiquetas_ai = extraer_etiquetas(prompt_usuario, client)

    return embedding_texto, etiquetas_ai