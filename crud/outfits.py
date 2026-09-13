from core.config import supabase_client, OUTFITS_TABLA

async def obtener_outfit_por_id(outfit_id: str):
    '''
    Busca y recupera un outfit específico de la base de datos de Supabase utilizando su identificador único.

    Parameters
    ----------
    outfit_id : str
        Identificador único del outfit que se desea buscar.

    Returns
    ----------
    dict or None
        Diccionario con los datos del outfit encontrado, o None si no se encuentra ningún registro con ese identificador.
    '''
    try:
        respuesta = await supabase_client.table(OUTFITS_TABLA).select("*").eq("id", outfit_id).execute()
        
        if not respuesta.data:
            return None

        return respuesta.data[0]
        
    except Exception as e:
        print(f"❌ Error al obtener el outfit {outfit_id}: {str(e)}")
        raise e

# FALTA ENDPOINT
async def actualizar_outfit_por_id(outfit_id: str, embedding: list):
    return True