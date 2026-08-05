import json
import numpy as np
import random
from typing import Any
from utils.normalize_vector import normalize_vector
from data.db_loader import supabase, catalog
from config import OUTFITS, PRENDAS
from utils.get_embedding import get_embedding
from utils.load_image_from_url import load_image_from_url
from modulos.cargar_modelos import cargar_modelos
from modulos.procesar_imagen import procesar_imagen
from modulos.completar_outfit import completar_outfit
from modulos.completar_outfit import detectar_color_prenda
import os

from pydantic import BaseModel, Field
from openai import OpenAI  # Compatible con OpenAI, DeepSeek, o APIs compatibles

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API")

class OutfitMetadataAI(BaseModel):
    ocasiones: list[str] = Field(description="1 o 2 ocasiones ideales: casual, business, party, sport")
    temporalidad: list[str] = Field(description="Época del año: verano, invierno, entretiempo")
    inspiracion: list[str] = Field(description="Estilo estético: minimal, old money, y2k, streetwear, chic")
    titulo: str = Field(description="Título corto de 3 a 5 palabras, elegante y comercial")
    descripcion_catchy: str = Field(description="Copy para redes sociales de 15-20 palabras con un emoji al final")

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











##################################################################
def obtener_url_prenda_aleatoria(catalog: list[dict[str, Any]]) -> str | None:
    """
    Selecciona una prenda aleatoria del catálogo y devuelve únicamente su URL de imagen.
    
    Args:
        catalog: Lista de diccionarios de prendas devuelta por Supabase.
        
    Returns:
        Un string con la URL de la imagen o None si el catálogo está vacío.
    """
    if not catalog:
        return None
        
    prenda_elegida = random.choice(catalog)
    
    # Extraemos solo la URL (compatible con 'url_imagen' o 'img_url' según tu tabla)
    return prenda_elegida.get("url_imagen") or prenda_elegida.get("img_url")

prenda = load_image_from_url(obtener_url_prenda_aleatoria(catalog))

processor, model, remover = cargar_modelos()

embedding, tipo_prenda, color = procesar_imagen(prenda, processor, model, remover)

print(color)

outfit = completar_outfit(tipo_prenda, 5, 0.15, color, embedding, catalog)

print(outfit)

nombres_prendas = []
colores_hex = []
for el in outfit:
    prenda = load_image_from_url(el['img_url'])
    _, _, color = procesar_imagen(prenda, processor, model, remover)
    nombres_prendas.append(el['name'])
    colores_hex.append(color['hex'])
    
post = generar_metadatos_hibridos(
    nombres_prendas,
    colores_hex,
    [],
    api_key
)

print(post)