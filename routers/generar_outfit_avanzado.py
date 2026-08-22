import torch
from config import SLOT_INDEX

def preparar_outfit_parcial(prendas_dict, clip_dim=512):
    """
    Convierte un diccionario de prendas en un embedding promedio y su máscara de presencia.
    
    Ejemplo input: 
    prendas_dict = {
        'SUPERIOR': tensor_camiseta, 
        'INFERIOR': tensor_pantalon
    }
    """
    # Si por algún motivo no pasan ninguna prenda (cold start del outfit)
    if not prendas_dict:
        return torch.zeros(1, clip_dim), torch.zeros(1, 6)
        
    embeddings_list = []
    presence_vector = torch.zeros(1, 6)
    
    for slot, tensor in prendas_dict.items():
        embeddings_list.append(tensor)
        # Marcamos con un 1 el slot correspondiente
        idx = SLOT_INDEX[slot]
        presence_vector[0, idx] = 1.0
        
    # Apilamos y hacemos la media en la dimensión de los items
    # shape de torch.stack: (num_prendas, clip_dim)
    partial_outfit_emb = torch.stack(embeddings_list).mean(dim=0, keepdim=True)
    
    return partial_outfit_emb, presence_vector