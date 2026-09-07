import torch
import torch.nn.functional as F
from utils.catalogos import SLOT_INDEX, VOCABULARIO_TAGS, NUM_TAGS

def tags_a_multihot(etiquetas_extraidas: list, num_tags: int = NUM_TAGS) -> torch.Tensor:
    """
    Convierte una lista de etiquetas en un vector multi-hot.
    """
    tensor_tags = torch.zeros(1, num_tags, dtype=torch.float32)
    
    if not etiquetas_extraidas:
        return tensor_tags
        
    for tag in etiquetas_extraidas:
        # Solo quitamos espacios por seguridad, pero respetamos mayúsculas
        tag_limpio = tag.strip() 
        if tag_limpio in VOCABULARIO_TAGS:
            idx = VOCABULARIO_TAGS.index(tag_limpio)
            tensor_tags[0, idx] = 1.0
            
    return tensor_tags


def hex_a_tensor_color(hex_color: str) -> torch.Tensor:
    """
    Convierte un código hexadecimal '#FF0000' en un tensor RGB normalizado [0, 1].
    Devuelve shape (1, 3) para integrarse en batches de inferencia.
    """
    # Fallback si el color viene vacío o nulo
    if not hex_color or not isinstance(hex_color, str):
        return torch.zeros(1, 3, dtype=torch.float32)
        
    hex_color = hex_color.lstrip('#')
    
    # Si el formato no tiene 6 caracteres, devolvemos ceros por seguridad
    if len(hex_color) != 6:
        return torch.zeros(1, 3, dtype=torch.float32)
        
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return torch.tensor([[r, g, b]], dtype=torch.float32)
    except ValueError:
        # Por si entra un string que no es un hex válido (ej. "blanco")
        return torch.zeros(1, 3, dtype=torch.float32)

def preparar_outfit_parcial(prendas_dict, clip_dim=512):
    """
    Convierte un diccionario de prendas en un embedding promedio (1, 512) 
    y su máscara de presencia (1, 6) para la red neuronal.
    """
    # Si no hay prendas de entrada (cold start del outfit)
    if not prendas_dict:
        return torch.zeros(1, clip_dim, dtype=torch.float32), torch.zeros(1, 6, dtype=torch.float32)
        
    embeddings_list = []
    presence_vector = torch.zeros(1, 6, dtype=torch.float32)
    
    for slot, emb in prendas_dict.items():
        # 1. Asegurarnos de que es un tensor 1D (512,) para evitar dimensiones extrañas
        tensor_emb = torch.tensor(emb, dtype=torch.float32).view(-1)
        embeddings_list.append(tensor_emb)
        
        # 2. Normalizar el nombre del slot para evitar KeyErrors
        slot_upper = slot.strip().upper()
        if slot_upper in SLOT_INDEX:
            idx = SLOT_INDEX[slot_upper]
            presence_vector[0, idx] = 1.0
            
    # 3. Matemáticas seguras:
    # torch.stack -> (num_prendas, 512)
    # .mean(dim=0) -> (512,)
    # .unsqueeze(0) -> (1, 512) (Perfecto para hacer torch.cat en tu red)
    partial_outfit_emb = torch.stack(embeddings_list).mean(dim=0).unsqueeze(0)
    
    return partial_outfit_emb, presence_vector

def preparar_user_history(lista_embeddings, max_seq_len=10, clip_dim=512):
    """
    Convierte una lista de embeddings de interacciones previas 
    en un tensor válido para la capa GRU.
    
    Args:
        lista_embeddings: Lista de tensores o arrays NumPy (cada uno de tamaño 512).
        max_seq_len: Número máximo de interacciones a considerar en el historial.
    """
    # Manejo del "Cold Start" (usuario nuevo sin historial)
    if not lista_embeddings:
        # Devuelve un tensor de ceros: (batch_size=1, max_seq_len, clip_dim)
        return torch.zeros(1, max_seq_len, clip_dim)

    # Convertir lista a un solo tensor bidimensional: (seq_len, clip_dim)
    # Asumimos que los embeddings más antiguos están al principio y los más recientes al final
    tensores = [torch.tensor(emb, dtype=torch.float32) if not isinstance(emb, torch.Tensor) else emb 
                for emb in lista_embeddings]
    history_tensor = torch.stack(tensores)
    
    seq_len = history_tensor.size(0)
    
    if seq_len >= max_seq_len:
        # Truncar: nos quedamos solo con las 'max_seq_len' interacciones más recientes
        history_tensor = history_tensor[-max_seq_len:]
    else:
        # Pad: rellenamos con ceros para alcanzar el max_seq_len.
        # En series temporales, suele ser mejor rellenar por la izquierda (al principio)
        # para que el estado oculto del GRU reciba los datos reales justo antes de la salida.
        pad_size = max_seq_len - seq_len
        # F.pad recibe tuplas empezando por la última dimensión: (pad_right, pad_left, pad_bottom, pad_top)
        history_tensor = F.pad(history_tensor, (0, 0, pad_size, 0))
        
    # Añadir la dimensión del batch para inferencia individual: (1, seq_len, clip_dim)
    return history_tensor.unsqueeze(0)