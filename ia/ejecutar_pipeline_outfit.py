# modulos/ia_pytorch.py
import asyncio
import torch

from config import PRENDAS_TABLA, COL_ID, COL_EMBEDDING, COL_COLOR, TODOS_LOS_SLOTS
from data.supabase import supabase

# Importamos las funciones de tensores que definimos antes
from generador_outfits import (
    preparar_outfit_parcial, 
    preparar_user_history, 
    hex_a_tensor_color, 
    tags_a_multihot
)

async def ejecutar_pipeline_outfit(app_state, usuario_id: str, prendas_input: dict, tags_llm: list, color_hex: str = None):
    """
    Agrupa toda la lógica de Inferencia PyTorch + Búsqueda en pgvector.
    Puede ser llamada desde el endpoint directo o desde el Agente Chat.
    """
    
    red_generadora = app_state.ml_models["sequential_generator"]
    
    # 1. Recuperar tensores de las prendas de input (Si hay alguna)
    dict_tensores_input = {}
    color_promedio = torch.zeros(1, 3)
    
    if prendas_input:
        lista_ids = list(prendas_input.values())
        respuesta_input = await asyncio.to_thread(
            lambda: supabase.table(PRENDAS_TABLA).select("*").in_(COL_ID, lista_ids).execute()
        )
        prendas_db = {p[COL_ID]: p for p in respuesta_input.data}
        
        for slot, prenda_id in prendas_input.items():
            emb = torch.tensor(prendas_db[prenda_id][COL_EMBEDDING], dtype=torch.float32)
            dict_tensores_input[slot] = emb
            color_promedio += hex_a_tensor_color(prendas_db[prenda_id][COL_COLOR])
        color_promedio = color_promedio / len(prendas_input)
    elif color_hex:
        # Si el usuario pidió un color en el chat pero no dio prenda base
        color_promedio = hex_a_tensor_color(color_hex)

    # 2. Recuperar historial del usuario (Likes/Guardados)
    # Aquí consultarías tu tabla de interacciones (ej. 'user_likes')
    historial_embeddings = [] 
    # (Lógica omitida por brevedad: SELECT embedding FROM user_likes WHERE user_id = usuario_id LIMIT 10)

    # 3. Preparar todos los tensores
    tags_tensor = tags_a_multihot(tags_llm)
    partial_outfit_emb, slots_presence = preparar_outfit_parcial(dict_tensores_input)
    user_history_tensor = preparar_user_history(historial_embeddings, max_seq_len=10)

    # 4. Inferencia con PyTorch
    with torch.no_grad():
        predicciones_slots = red_generadora(
            user_history=user_history_tensor,
            partial_outfit_emb=partial_outfit_emb,
            slots_presence=slots_presence,
            tags_vector=tags_tensor,
            color_explicito=color_promedio
        )

    # 5. Búsqueda Vectorial (pgvector)
    slots_input = set(prendas_input.keys())
    slots_a_buscar = [s for s in TODOS_LOS_SLOTS if s not in slots_input]
    
    outfit_generado = []
    for slot in slots_a_buscar:
        vector_objetivo = predicciones_slots[slot].squeeze(0).tolist()
        
        respuesta_rpc = await asyncio.to_thread(
            lambda: supabase.rpc("match_prendas_por_slot", {
                "query_embedding": vector_objetivo,
                "match_slot": slot,
                "match_count": 1
            }).execute()
        )
        
        if respuesta_rpc.data:
            outfit_generado.append(respuesta_rpc.data[0])

    return outfit_generado