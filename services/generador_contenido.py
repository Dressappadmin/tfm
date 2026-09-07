'''
from schemas.OutfitMetadataAI import OutfitMetadataAI
from openai import OpenAI 

import os

from dotenv import load_dotenv

from utils.catalogos import PRENDAS_TABLA, EMBEDDING_PRENDA, IMG_URL_PRENDA, TIPO_PRENDA
from data.cargar_tabla_memoria import cargar_tabla_memoria, supabase

from utils.registrar_outfit_bd import registrar_outfit_bd
from utils.cargar_imagen_url_bucket import cargar_imagen_url_bucket
from utils.registrar_post_bd import registrar_post_bd

from schemas.OutfitMetadataAI import OutfitMetadataAI

from generador_contenido.generar_metadatos_hibridos import generar_metadatos_hibridos
from generador_contenido.obtener_url_prenda_aleatoria import obtener_url_prenda_aleatoria

from modulos.cargar_modelos import cargar_modelos
from modulos.procesar_imagen import procesar_imagen
from modulos.completar_outfit import completar_outfit

import random
from typing import Any
from config import IMG_URL_PRENDA

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
    return prenda_elegida.get(IMG_URL_PRENDA)

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

def generar_post():

    load_dotenv()

    api_key = os.getenv("OPENAI_API")

    catalog, _ = cargar_tabla_memoria(PRENDAS_TABLA, embedding=EMBEDDING_PRENDA)

    prenda = cargar_imagen_url_bucket(obtener_url_prenda_aleatoria(catalog))

    processor, model, remover = cargar_modelos()

    embedding, tipo_prenda, color = procesar_imagen(prenda, processor, model, remover)

    print(color)

    outfit = completar_outfit(tipo_prenda, 5, 0.15, color, embedding, catalog)

    print(outfit)

    outfit_id = registrar_outfit_bd(outfit)

    nombres_prendas = []
    colores_hex = []
    for el in outfit:
        prenda = cargar_imagen_url_bucket(el[IMG_URL_PRENDA])
        _, _, color = procesar_imagen(prenda, processor, model, remover)
        nombres_prendas.append(TIPO_PRENDA)
        colores_hex.append(color['hex'])
        
    post = generar_metadatos_hibridos(
        nombres_prendas,
        colores_hex,
        [],
        api_key
    )

    print(post)

    registrar_post_bd(supabase, outfit_id)
'''