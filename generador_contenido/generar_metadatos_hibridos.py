from schemas.OutfitMetadataAI import OutfitMetadataAI
from openai import OpenAI 

def generar_metadatos_hibridos(
    nombres_prendas: list[str],
    colores_hex: list[str],
    ejemplos_top_likes: list[str],
    api_key: str
) -> dict:
    """
    Usa un LLM rápido para generar etiquetas de alta precisión y un copy 
    optimizado basándose en los textos que mejor funcionan en la app.
    """
    client = OpenAI(api_key=api_key)
    
    prompt_usuario = (
        f"Prendas del outfit: {', '.join(nombres_prendas)}.\n"
        f"Paleta de color principal: {', '.join(colores_hex)}.\n\n"
        f"Ejemplos de descripciones con alto engagement en nuestra app:\n"
        + "\n".join([f"- '{ej}'" for ej in ejemplos_top_likes]) +
        "\n\nGenera los metadatos para este nuevo conjunto:"
    )
    
    respuesta = client.beta.chat.completions.parse(
        model="gpt-5.4-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres el editor jefe de moda de una app de estilo. Tu objetivo es asignar etiquetas exactas y escribir copys muy atractivos y naturales para maximizar los likes."
            },
            {"role": "user", "content": prompt_usuario}
        ],
        response_format=OutfitMetadataAI
    )
    
    # Devuelve un diccionario validado listo para la tabla 'outfits' de Supabase
    return respuesta.choices[0].message.parsed.model_dump()
