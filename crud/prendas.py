import numpy as np
from typing import Any
from fastapi import HTTPException
from core.config import (
    supabase_client,
    render_client,
    PRENDAS_TABLA, 
    ID_PRENDA,
    TIPO_PRENDA, 
    SLOT_PRENDA
)

# ENDPOINT RENDER
async def actualizar_prenda_por_id(datos_a_actualizar: dict, prenda_id: str):
    '''
    Realiza una petición HTTP PATCH a una API externa para actualizar los datos de una prenda específica, separando los parámetros requeridos para la URL y el cuerpo de la solicitud.

    Parameters
    ----------
    datos_a_actualizar : dict
        Diccionario que contiene los campos y valores que se van a actualizar en la prenda, del cual se extraen y remueven el tipo de prenda y el slot.
    prenda_id : str
        Identificador único de la prenda que se desea actualizar.

    Returns
    ----------
    dict
        Respuesta en formato JSON devuelta por la API externa tras completar con éxito la actualización.
    '''
    url = f"/wardrobes/image_ai_process"
    
    parametros_url = {
        "image_id": prenda_id,
        "tipo_prenda": datos_a_actualizar.pop(TIPO_PRENDA),
        "slot": datos_a_actualizar.pop(SLOT_PRENDA)
    }
    
    respuesta = await render_client.patch(
        url, 
        params=parametros_url,  
        json=datos_a_actualizar,
        timeout=30.0
    )
    
    respuesta.raise_for_status()
    return respuesta.json()

async def obtener_prenda_por_id(prenda_id: str):
    '''
    Busca y recupera los datos de una prenda específica de la tabla de prendas en Supabase utilizando su identificador único.

    Parameters
    ----------
    prenda_id : str
        Identificador único de la prenda que se desea consultar.

    Returns
    ----------
    dict or None
        Diccionario con la información de la prenda encontrada, o None si no existe ningún registro con dicho identificador.
    '''
    try:
        respuesta = await supabase_client.table(PRENDAS_TABLA).select("*").eq(ID_PRENDA, prenda_id).execute()
        
        return respuesta.data[0] if respuesta.data else None
        
    except Exception as e:
        print(f"❌ Error al obtener la prenda {prenda_id}: {str(e)}")
        raise e


async def obtener_varias_prendas_por_id(lista_ids: list):
    '''
    Recupera un lote de prendas de la base de datos de Supabase de forma simultánea utilizando una lista de identificadores únicos.

    Parameters
    ----------
    lista_ids : list
        Lista de cadenas de texto con los identificadores de las prendas que se desean consultar.

    Returns
    ----------
    list
        Lista de diccionarios que contienen la información de las prendas encontradas en la base de datos.
    '''
    try:
        respuesta = await supabase_client.table(PRENDAS_TABLA).select("*").in_(ID_PRENDA, lista_ids).execute()
        
        return respuesta.data
        
    except Exception as e:
        print(f"❌ Error al obtener lote de prendas: {str(e)}")
        raise e


async def buscar_prendas_por_slot_pgvector(embedding_objetivo: list, slot: str, top_n: int = 1):
    '''
    Busca prendas similares en la base de datos mediante búsqueda vectorial (pgvector) aplicando un filtro por un slot o categoría específica.

    Parameters
    ----------
    embedding_objetivo : list
        Vector numérico que representa el embedding de referencia para realizar la búsqueda por similitud.
    slot : str
        Categoría o slot de la prenda por el cual se filtrarán los resultados de la consulta.
    top_n : int, optional
        Número máximo de prendas similares que se desean recuperar (por defecto es 1).

    Returns
    ----------
    list
        Lista de diccionarios con la información de las prendas encontradas que cumplen con los criterios de similitud y slot.
    '''
    try:
        parametros = {
            "vector": embedding_objetivo,
            "p_slot": slot, 
            "limite": top_n
        }
        
        respuesta = await supabase_client.rpc("buscar_prendas_por_slot_db", parametros).execute()
        
        return respuesta.data
        
    except Exception as e:
        print(f"❌ Error al buscar prendas por slot {slot}: {str(e)}")
        raise e


async def obtener_prenda_aleatoria() -> dict:
    '''
    Selecciona y recupera una prenda de vestir de forma aleatoria desde la base de datos utilizando una función almacenada (RPC).

    Parameters
    ----------
    None

    Returns
    ----------
    dict
        Diccionario con la información detallada de la prenda seleccionada al azar.
    '''
    try:
        respuesta = await supabase_client.rpc("obtener_prenda_aleatoria_db").execute() 
        
        if not respuesta.data:
            raise HTTPException(status_code=404, detail="No hay prendas en la base de datos.")
            
        return respuesta.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo prenda aleatoria: {str(e)}")