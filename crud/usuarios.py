import json
import torch
from ia.utils_tensores import hex_a_tensor_color
from core.config import EMBEDDING_PRENDA, COLOR_PRENDA
from core.config import supabase_client

async def obtener_historial(usuario_id: str, max_items: int = 10):
    '''
    Obtiene el historial de interacciones de un usuario desde la base de datos mediante una función RPC en Supabase, procesando y transformando los embeddings y colores en tensores de PyTorch ordenados cronológicamente.

    Parameters
    ----------
    usuario_id : str
        Identificador único del usuario cuyo historial de interacciones se desea consultar.
    max_items : int, optional
        Número máximo de elementos del historial que se recuperarán (por defecto es 10).

    Returns
    ----------
    tuple
        Una tupla que contiene dos listas de tensores de PyTorch: una con los embeddings de las prendas y otra con los tensores de color correspondientes.
    '''
    try:
        respuesta = await supabase_client.rpc(
            "obtener_historial_usuario", 
            {"p_usuario_id": usuario_id, "p_max_items": max_items}
        ).execute()
        
        registros = respuesta.data if respuesta.data else []

        if not registros or len(registros) == 0:
            return [torch.zeros(512)], [torch.zeros(3)]

        historial_embeddings = []
        historial_colores = []

        registros_ordenados = reversed(registros)

        for fila in registros_ordenados:
            
            # A) Procesar Embedding
            emb = fila.get(EMBEDDING_PRENDA)
            if isinstance(emb, str):
                emb = json.loads(emb)
                
            historial_embeddings.append(torch.tensor(emb, dtype=torch.float32))

            color_hex = fila.get(COLOR_PRENDA)
            if color_hex and isinstance(color_hex, str):
                color_tensor = hex_a_tensor_color(color_hex).squeeze(0)
            else:
                color_tensor = torch.zeros(3)
                
            historial_colores.append(color_tensor)

        return historial_embeddings, historial_colores

    except Exception as e:
        print(f"❌ Error al obtener historial (RPC) para {usuario_id}: {str(e)}")
        return [torch.zeros(512)], [torch.zeros(3)]