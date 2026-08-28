import numpy as np
import httpx
from typing import Any
from fastapi import HTTPException
from core.api_client import cliente_api
from core.config import PRENDAS_TABLA, ID_PRENDA, supabase_client

# ENDPOINT ALLAN
async def actualizar_prenda_por_id(datos_a_actualizar: dict):
    """Hace un PATCH a la API externa para actualizar columnas."""
    url = f"/wardrobes/image_ai_process"
    respuesta = await cliente_api.patch(url, json=datos_a_actualizar)
    respuesta.raise_for_status()
    return respuesta.json()

async def obtener_prenda_por_id(prenda_id: str):
    """Obtiene los datos de una prenda por su ID."""
    try:
        respuesta = await supabase_client.table(PRENDAS_TABLA).select("*").eq(ID_PRENDA, prenda_id).execute()
        
        return respuesta.data[0] if respuesta.data else None
        
    except Exception as e:
        print(f"❌ Error al obtener la prenda {prenda_id}: {str(e)}")
        raise e


async def obtener_varias_prendas_por_id(lista_ids: list):
    """Obtiene un lote de prendas usando una lista de IDs."""
    try:
        # El método .in_() de Supabase hace exactamente la búsqueda que querías
        respuesta = await supabase_client.table(PRENDAS_TABLA).select("*").in_(ID_PRENDA, lista_ids).execute()
        
        return respuesta.data
        
    except Exception as e:
        print(f"❌ Error al obtener lote de prendas: {str(e)}")
        raise e


async def buscar_prendas_por_slot_pgvector(embedding_objetivo: list, slot: str, top_n: int = 1):
    """
    Busca prendas similares filtradas por un slot específico.
    """
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
    """
    Obtiene una prenda al azar.
    """
    try:
        # En Supabase/PostgreSQL, no se puede hacer un 'ORDER BY random()' directo 
        # con el cliente de Python. La mejor forma es llamar a una pequeña función SQL.
        respuesta = await supabase_client.rpc("obtener_prenda_aleatoria_db").execute() 
        
        if not respuesta.data:
            raise HTTPException(status_code=404, detail="No hay prendas en la base de datos.")
            
        return respuesta.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo prenda aleatoria: {str(e)}")