from typing import Any
import httpx
from core.api_client import cliente_api
from core.config import supabase_client, OUTFITS_TABLA

async def obtener_outfit_por_id(outfit_id: str):
    """
    Busca un outfit por su ID directamente en la base de datos Supabase.
    """
    try:
        respuesta = await supabase_client.table(OUTFITS_TABLA).select("*").eq("id", outfit_id).execute()
        
        # Si no hay datos, devolvemos None
        if not respuesta.data:
            return None
            
        # Devolvemos el primer y único elemento de la lista
        return respuesta.data[0]
        
    except Exception as e:
        print(f"❌ Error al obtener el outfit {outfit_id}: {str(e)}")
        raise e

# FALTA ENDPOINT ALLAN
async def actualizar_outfit_por_id(outfit_id: str, embedding: list):
    return True