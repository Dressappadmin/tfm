import json
import torch
from torch.utils.data import Dataset
from ia.utils_tensores import preparar_user_history, hex_a_tensor_color, tags_a_multihot

class TripletOutfitDataset(Dataset):
    '''
    Dataset para el entrenamiento del modelo AttentionOutfitGenerator mediante Triplet Loss. Carga y procesa un archivo JSON con interacciones de usuarios para proporcionar el contexto de generación junto con los embeddings de la prenda elegida (positiva) y la prenda rechazada (negativa).

    Parameters
    ----------
    json_path : str
        Ruta del archivo JSON que contiene los registros de entrenamiento (tripletas de interacciones).
    max_seq_len : int, optional
        Longitud máxima permitida para procesar el historial de prendas del usuario (por defecto es 10).

    Returns
    ----------
    tuple
        Al acceder mediante índice (__getitem__), devuelve una tupla que contiene: un diccionario con el contexto para la red (historial, slot objetivo, tags y color), el tensor de la prenda elegida (positivo) y el tensor de la prenda rechazada (negativo).
    '''
    
    def __init__(self, json_path: str, max_seq_len: int = 10):

        self.max_seq_len = max_seq_len
        
        # Cargamos los datos del JSON (Tus 1k buenos y 10k malos modificados)
        with open(json_path, 'r', encoding='utf-8') as f:
            self.datos_brutos = json.load(f)
            
        print(f"📦 Dataset cargado: {len(self.datos_brutos)} tripletas disponibles.")

    def __len__(self):
        return len(self.datos_brutos)

    def __getitem__(self, idx):
        
        registro = self.datos_brutos[idx]
        
        historial_lista = registro["historial_embeddings"] 

        history_clips = preparar_user_history(historial_lista, self.max_seq_len)
        tags_tensor = tags_a_multihot(registro["tags_solicitados"])
        color_tensor = hex_a_tensor_color(registro["color_promedio_solicitado"])

        target_slot_idx = torch.tensor([registro["target_slot_index"]], dtype=torch.long)
   
        positive_emb = torch.tensor(registro["prenda_elegida_embedding"], dtype=torch.float32)

        negative_emb = torch.tensor(registro["prenda_rechazada_embedding"], dtype=torch.float32)

        contexto_red = {
            "history_clips": history_clips,
            "target_slot": target_slot_idx,
            "tags": tags_tensor,
            "color": color_tensor
        }
        
        return contexto_red, positive_emb, negative_emb