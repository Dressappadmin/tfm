import torch
from core.config import ID_PRENDA, EMBEDDING_PRENDA, COLOR_PRENDA
from utils.catalogos import TODOS_LOS_SLOTS, SLOT_INDEX

# Importamos las funciones de IA y Tensores
from ia.utils_tensores import (
    preparar_user_history, 
    hex_a_tensor_color, 
    tags_a_multihot
)

from crud.prendas import obtener_varias_prendas_por_id, buscar_prendas_por_slot_pgvector
from crud.usuarios import obtener_historial

async def ejecutar_pipeline_outfit(app_state, usuario_id: str, prendas_input: dict, tags_llm: list, color_hex: str = None):
    """
    Agrupa toda la lógica de Inferencia PyTorch + Búsqueda en pgvector adaptada para AttentionOutfitGenerator.
    """
    # 1. Recuperamos la nueva red
    red_generadora = app_state.ml_models["outfit_generator"]
    
    prendas_input_norm = {k.strip().upper(): v for k, v in prendas_input.items()} if prendas_input else {}
    
    # =====================================================================
    # 1. RECUPERAR TENSORES DE LAS PRENDAS INPUT
    # =====================================================================
    dict_tensores_input = {}
    color_promedio = torch.zeros(1, 3)
    prendas_db = {}
    
    if prendas_input_norm:
        lista_ids = list(prendas_input_norm.values())
        
        # LLAMADA 1 A LA API
        lista_prendas_data = await obtener_varias_prendas_por_id(lista_ids)
        prendas_db = {p[ID_PRENDA]: p for p in lista_prendas_data}
        
        for slot, prenda_id in prendas_input_norm.items():
            if prenda_id in prendas_db:
                emb = torch.tensor(prendas_db[prenda_id][EMBEDDING_PRENDA], dtype=torch.float32)
                dict_tensores_input[slot] = emb
                color_promedio += hex_a_tensor_color(prendas_db[prenda_id][COLOR_PRENDA])
            
        color_promedio = color_promedio / len(prendas_input_norm)
        
    elif color_hex:
        color_promedio = hex_a_tensor_color(color_hex)

    # =====================================================================
    # 2. RECUPERAR HISTORIAL DEL USUARIO
    # =====================================================================
    historial_embeddings = await obtener_historial(usuario_id)
    
    # =====================================================================
    # 3. PREPARAR SECUENCIA (MAGIA DEL TRANSFORMER)
    # =====================================================================
    tags_tensor = tags_a_multihot(tags_llm) # (1, 9)
    user_history_tensor = preparar_user_history(historial_embeddings, max_seq_len=10) # (1, seq_len, 512)

    # Ya no procesamos el 'outfit_parcial' como un bloque estático.
    # Simplemente lo adjuntamos como los últimos elementos de la secuencia histórica.
    if dict_tensores_input:
        # Apilamos las prendas de entrada (1, num_prendas, 512)
        tensores_input = torch.stack(list(dict_tensores_input.values())).unsqueeze(0) 
        # Las concatenamos en la dimensión de la secuencia
        history_clips = torch.cat([user_history_tensor, tensores_input], dim=1) 
    else:
        history_clips = user_history_tensor

    # =====================================================================
    # 4 & 5. INFERENCIA Y BÚSQUEDA VECTORIAL ITERATIVA
    # =====================================================================
    slots_input = set(prendas_input_norm.keys())
    slots_a_buscar = [s for s in TODOS_LOS_SLOTS if s not in slots_input]
    
    ids_generados = []
    
    with torch.no_grad():
        for slot in slots_a_buscar:
            # A. Convertimos el nombre del slot ('SUPERIOR') a su índice de la base de datos (0, 1, 2...)
            slot_idx = torch.tensor([SLOT_INDEX[slot]], dtype=torch.long)
            
            # B. Inferencia: Pedimos a la red la prenda ideal para ESTE slot en concreto
            vector_predicho = red_generadora(
                history_clips=history_clips,
                target_slot=slot_idx,
                tags=tags_tensor,
                color=color_promedio
            )
            
            vector_objetivo = vector_predicho.squeeze(0).tolist()
            
            # C. LLAMADA 2 A LA API: Búsqueda en pgvector (Supabase/PostgreSQL)
            prendas_match = await buscar_prendas_por_slot_pgvector(
                embedding_objetivo=vector_objetivo,
                slot=slot,
                top_n=1
            )
            
            if prendas_match and len(prendas_match) > 0:
                prenda_encontrada = prendas_match[0]
                ids_generados.append(prenda_encontrada[ID_PRENDA])
                
                # D. ACTUALIZACIÓN DE CONTEXTO (Auto-regresión)
                # Extraemos el embedding de la prenda real que acaba de encontrar pgvector
                nuevo_emb = torch.tensor(prenda_encontrada[EMBEDDING_PRENDA], dtype=torch.float32).view(1, 1, -1)
                
                # Lo añadimos al historial. Así, al buscar la siguiente prenda del bucle,
                # el modelo "verá" la prenda que acaba de seleccionar y combinará perfectamente.
                history_clips = torch.cat([history_clips, nuevo_emb], dim=1)

    # Unimos los IDs originales que pasó el usuario con los nuevos de la IA
    ids_originales = list(prendas_input_norm.values()) if prendas_input_norm else []
    outfit_final_ids = ids_originales + ids_generados

    return outfit_final_ids