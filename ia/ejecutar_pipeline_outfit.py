import torch
from core.config import ID_PRENDA, EMBEDDING_PRENDA, COLOR_PRENDA
from utils.catalogos import TODOS_LOS_SLOTS

# Importamos las funciones de IA y Tensores
from ia.utils_tensores import (
    preparar_outfit_parcial, 
    preparar_user_history, 
    hex_a_tensor_color, 
    tags_a_multihot
)

from crud.prendas import obtener_varias_prendas_por_id, buscar_prendas_por_slot_pgvector
from crud.usuarios import obtener_historial

async def ejecutar_pipeline_outfit(app_state, usuario_id: str, prendas_input: dict, tags_llm: list, color_hex: str = None):
    """
    Agrupa toda la lógica de Inferencia PyTorch + Búsqueda en pgvector.
    Puede ser llamada desde el endpoint directo, un feed automático o desde el Agente Chat.
    """
    red_generadora = app_state.ml_models["sequential_generator"]
    
    # =====================================================================
    # 1. RECUPERAR TENSORES DE LAS PRENDAS INPUT
    # =====================================================================
    dict_tensores_input = {}
    color_promedio = torch.zeros(1, 3)
    prendas_db = {}
    
    if prendas_input:
        lista_ids = list(prendas_input.values())
        
        # LLAMADA 1 A LA API: Obtenemos los datos de las prendas base
        lista_prendas_data = await obtener_varias_prendas_por_id(lista_ids)
        prendas_db = {p[ID_PRENDA]: p for p in lista_prendas_data}
        
        for slot, prenda_id in prendas_input.items():
            emb = torch.tensor(prendas_db[prenda_id][EMBEDDING_PRENDA], dtype=torch.float32)
            dict_tensores_input[slot] = emb
            color_promedio += hex_a_tensor_color(prendas_db[prenda_id][COLOR_PRENDA])
            
        color_promedio = color_promedio / len(prendas_input)
        
    elif color_hex:
        # Si el usuario pidió un color en el chat pero no dio prenda base
        color_promedio = hex_a_tensor_color(color_hex)

    # =====================================================================
    # 2. RECUPERAR HISTORIAL DEL USUARIO
    # =====================================================================
    historial_embeddings = obtener_historial(usuario_id)
    
    # =====================================================================
    # 3. PREPARAR TODOS LOS TENSORES
    # =====================================================================
    tags_tensor = tags_a_multihot(tags_llm)
    partial_outfit_emb, slots_presence = preparar_outfit_parcial(dict_tensores_input)
    user_history_tensor = preparar_user_history(historial_embeddings, max_seq_len=10)

    # =====================================================================
    # 4. INFERENCIA CON PYTORCH
    # =====================================================================
    with torch.no_grad():
        predicciones_slots = red_generadora(
            user_history=user_history_tensor,
            partial_outfit_emb=partial_outfit_emb,
            slots_presence=slots_presence,
            tags_vector=tags_tensor,
            color_explicito=color_promedio
        )

    # =====================================================================
    # 5. BÚSQUEDA VECTORIAL (A TRAVÉS DE LA API)
    # =====================================================================
    slots_input = set(prendas_input.keys()) if prendas_input else set()
    slots_a_buscar = [s for s in TODOS_LOS_SLOTS if s not in slots_input]
    
    outfit_generado = []
    
    for slot in slots_a_buscar:
        # Extraemos el vector ideal para este slot
        vector_objetivo = predicciones_slots[slot].squeeze(0).tolist()
        
        # LLAMADA 2 A LA API: Buscamos la prenda real más similar
        prendas_match = await buscar_prendas_por_slot_pgvector(
            embedding_objetivo=vector_objetivo,
            slot=slot,
            top_n=1
        )
        
        if prendas_match and len(prendas_match) > 0:
            outfit_generado.append(prendas_match[0])

    # Devolvemos tanto las prendas de entrada como el resultado (para que el router tenga toda la info)
    return prendas_db, outfit_generado