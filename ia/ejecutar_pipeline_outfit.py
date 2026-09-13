import json
import torch
import torch.nn.functional as F
from typing import List

from core.config import ID_PRENDA, EMBEDDING_PRENDA, COLOR_PRENDA, SLOT_PRENDA
from utils.catalogos import SLOT_INDEX
from ia.utils_tensores import preparar_user_history, hex_a_tensor_color, tags_a_multihot
from crud.prendas import obtener_varias_prendas_por_id, buscar_prendas_por_slot_pgvector
from crud.usuarios import obtener_historial
from services.validar_reglas_outfit import validar_reglas_outfit, determinar_slot_faltante

async def ejecutar_pipeline_outfit(
    app_state, 
    usuario_id: str, 
    prendas_input: List[str], 
    tags_llm: List[str], 
    temperatura: float = 0.5
):
    '''
    Ejecuta el pipeline iterativo de recomendación de outfits combinando el historial del usuario, características de color y vectores CLIP, utilizando un modelo generativo y muestreo estocástico autorregresivo hasta completar un conjunto válido.

    Parameters
    ----------
    app_state : object
        Objeto que almacena el estado global de la aplicación FastAPI, incluyendo los modelos de Machine Learning.
    usuario_id : str
        Identificador único del usuario para el cual se genera el outfit.
    prendas_input : List[str]
        Lista de identificadores de prendas iniciales seleccionadas como base o ancla para la recomendación.
    tags_llm : List[str]
        Lista de etiquetas de estilo o tags proporcionadas por el modelo de lenguaje para condicionar la generación.
    temperatura : float, optional
        Parámetro de temperatura que controla la aleatoriedad y diversidad en la selección de las prendas (por defecto es 0.5).

    Returns
    ----------
    List[str]
        Lista con los identificadores de todas las prendas que componen el outfit final generado (incluyendo las de entrada y las añadidas).
    '''

    red_generadora = app_state.ml_models["outfit_generator"]
    tipos_actuales = []
    
    lista_clips_input = []
    lista_colors_input = []
    
    if prendas_input:
        lista_prendas_data = await obtener_varias_prendas_por_id(prendas_input)
        
        for prenda_data in lista_prendas_data:
            slot = prenda_data[SLOT_PRENDA].strip().upper()
            tipos_actuales.append(slot)
            
            embedding_raw = prenda_data[EMBEDDING_PRENDA]
            
            if isinstance(embedding_raw, str):
                embedding_raw = json.loads(embedding_raw)
                
            emb = torch.tensor(embedding_raw, dtype=torch.float32)
            
            lista_clips_input.append(emb)
            
            color_prenda = prenda_data.get(COLOR_PRENDA)
            if color_prenda:
                lista_colors_input.append(hex_a_tensor_color(color_prenda).squeeze(0))
            else:
                lista_colors_input.append(torch.zeros(3))

    historial_embeddings, historial_colores = await obtener_historial(usuario_id)
    
    user_history_clips, user_history_colors = preparar_user_history(
        historial_embeddings, 
        historial_colores, 
        max_seq_len=10
    )

    if lista_clips_input:
        tensores_clips_input = torch.stack(lista_clips_input).unsqueeze(0) # [1, N, 512]
        tensores_colors_input = torch.stack(lista_colors_input).unsqueeze(0) # [1, N, 3]
        
        history_clips = torch.cat([user_history_clips, tensores_clips_input], dim=1) 
        history_colors = torch.cat([user_history_colors, tensores_colors_input], dim=1)
    else:
        history_clips = user_history_clips
        history_colors = user_history_colors

    tags_tensor = tags_a_multihot(tags_llm)
    ids_generados = []
    
    for _ in range(5):
        es_valido, _ = validar_reglas_outfit(tipos_actuales)
        if es_valido:
            break 
            
        slot_objetivo = determinar_slot_faltante(tipos_actuales)
        if not slot_objetivo:
            break 
            
        slot_idx = torch.tensor([SLOT_INDEX[slot_objetivo]], dtype=torch.long)
        
        with torch.no_grad():
            vector_predicho = red_generadora(
                history_clips=history_clips,
                history_colors=history_colors, # Toda la secuencia lleva su color real asociado
                target_slot=slot_idx,
                tags=tags_tensor
            )
            vector_objetivo = vector_predicho.squeeze(0).tolist()
            
        prendas_match = await buscar_prendas_por_slot_pgvector(vector_objetivo, slot_objetivo, top_n=10)
        
        if prendas_match and len(prendas_match) > 0:
            similitudes = torch.tensor([p.get("similitud", 0.0) for p in prendas_match], dtype=torch.float32)
            probabilidades = F.softmax(similitudes / temperatura, dim=0)
            prenda_encontrada = prendas_match[torch.multinomial(probabilidades, 1).item()]

            ids_generados.append(prenda_encontrada[ID_PRENDA])
            tipos_actuales.append(slot_objetivo)
            
            embedding_raw_encontrada = prenda_encontrada[EMBEDDING_PRENDA]

            if isinstance(embedding_raw_encontrada, str):
                embedding_raw_encontrada = json.loads(embedding_raw_encontrada)

            nuevo_clip = torch.tensor(embedding_raw_encontrada, dtype=torch.float32).view(1, 1, -1)
            
            color_nuevo = prenda_encontrada.get(COLOR_PRENDA)
            nuevo_color_tensor = hex_a_tensor_color(color_nuevo).view(1, 1, 3) if color_nuevo else torch.zeros(1, 1, 3)
            
            history_clips = torch.cat([history_clips, nuevo_clip], dim=1)
            history_colors = torch.cat([history_colors, nuevo_color_tensor], dim=1)
        else:
            break
            
    return prendas_input + ids_generados