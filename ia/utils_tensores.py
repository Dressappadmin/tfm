import torch
import torch.nn.functional as F
from utils.catalogos import SLOT_INDEX, VOCABULARIO_TAGS, NUM_TAGS

def tags_a_multihot(etiquetas_extraidas: list, num_tags: int = NUM_TAGS) -> torch.Tensor:
    '''
    Convierte una lista de etiquetas de estilo en una representación vectorial multi-hot utilizando un vocabulario predefinido.

    Parameters
    ----------
    etiquetas_extraidas : list
        Lista de cadenas de texto que representan las etiquetas o tags a codificar.
    num_tags : int, optional
        Tamaño o dimensión total del vector multi-hot resultante (por defecto es NUM_TAGS).

    Returns
    ----------
    torch.Tensor
        Tensor de PyTorch de dimensiones (1, num_tags) con valores de 1.0 en los índices correspondientes a las etiquetas válidas encontradas, y 0.0 en el resto.
    '''
    tensor_tags = torch.zeros(1, num_tags, dtype=torch.float32)
    
    if not etiquetas_extraidas:
        return tensor_tags
        
    for tag in etiquetas_extraidas:
        tag_limpio = tag.strip() 
        if tag_limpio in VOCABULARIO_TAGS:
            idx = VOCABULARIO_TAGS.index(tag_limpio)
            tensor_tags[0, idx] = 1.0
            
    return tensor_tags


def hex_a_tensor_color(hex_color: str) -> torch.Tensor:
    '''
    Convierte un código de color en formato hexadecimal a un tensor RGB normalizado en el rango [0, 1], con dimensiones (1, 3) para su integración directa en lotes de inferencia. Maneja de forma segura valores nulos o formatos inválidos devolviendo un tensor de ceros.

    Parameters
    ----------
    hex_color : str
        Cadena de texto que representa el código de color en formato hexadecimal (por ejemplo, '#FF0000').

    Returns
    ----------
    torch.Tensor
        Tensor de PyTorch de dimensiones (1, 3) con los valores RGB normalizados, o un tensor de ceros si la entrada proporcionada es inválida o nula.
    '''

    if not hex_color or not isinstance(hex_color, str):
        return torch.zeros(1, 3, dtype=torch.float32)
        
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) != 6:
        return torch.zeros(1, 3, dtype=torch.float32)
        
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return torch.tensor([[r, g, b]], dtype=torch.float32)
    except ValueError:
        return torch.zeros(1, 3, dtype=torch.float32)

def preparar_user_history(lista_embeddings, lista_colores, max_seq_len=10):
    '''
    Convierte listas de embeddings y colores correspondientes a interacciones previas del usuario en tensores de PyTorch acolchados (padded) o truncados a una longitud de secuencia máxima, añadiendo la dimensión de lote (batch) para su procesamiento en un modelo Transformer.

    Parameters
    ----------
    lista_embeddings : list
        Lista de arrays, listas de flotantes o tensores que representan los embeddings históricos de las prendas.
    lista_colores : list
        Lista de arrays, listas de flotantes o tensores que representan los colores históricos asociados a las prendas.
    max_seq_len : int, optional
        Número máximo de interacciones a considerar en la secuencia temporal (por defecto es 10).

    Returns
    ----------
    tuple
        Una tupla que contiene dos tensores de PyTorch (history_clips y history_colors), ambos con dimensiones (1, max_seq_len, dim).
    '''

    tensores_emb = [torch.tensor(emb, dtype=torch.float32) if not isinstance(emb, torch.Tensor) else emb 
                    for emb in lista_embeddings]
    
    tensores_col = [torch.tensor(col, dtype=torch.float32) if not isinstance(col, torch.Tensor) else col 
                    for col in lista_colores]

    history_tensor = torch.stack(tensores_emb)
    color_tensor = torch.stack(tensores_col)

    seq_len = history_tensor.size(0)
    
    if seq_len >= max_seq_len:
        history_tensor = history_tensor[-max_seq_len:]
        color_tensor = color_tensor[-max_seq_len:]
    else:
        pad_size = max_seq_len - seq_len
        history_tensor = F.pad(history_tensor, (0, 0, pad_size, 0))
        color_tensor = F.pad(color_tensor, (0, 0, pad_size, 0))
 
    return history_tensor.unsqueeze(0), color_tensor.unsqueeze(0)