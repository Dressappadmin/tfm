import os

from dotenv import load_dotenv

from config import PRENDAS_TABLA, EMBEDDING_PRENDA, IMG_URL_PRENDA, TIPO_PRENDA
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