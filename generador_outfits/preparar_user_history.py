import torch
import torch.nn.functional as F

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