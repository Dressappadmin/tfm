import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel

def calcular_embedding_texto(
    texto: str, 
    processor: CLIPProcessor, 
    model: CLIPModel, 
    device: str = "cpu"
) -> np.ndarray:
    '''
    Convierte un texto natural en un vector numérico (embedding) usando FashionCLIP.
    
    Utiliza el codificador de lenguaje (Text Encoder) del modelo CLIP para proyectar
    la consulta del usuario en el mismo espacio vectorial de 512 dimensiones que 
    las imágenes. Se normaliza el vector resultante (L2 norm) para poder aplicar 
    similitud coseno (producto escalar).
    
    Parameters
    ----------
    texto : str
        Consulta o descripción escrita por el usuario (ej. "vestido rojo elegante").
    processor : CLIPProcessor
        Procesador de Hugging Face pre-cargado en memoria (tokeniza el texto).
    model : CLIPModel
        Modelo visual/lenguaje FashionCLIP pre-cargado en memoria.
    device : str, opcional
        Dispositivo de inferencia ('cpu', 'cuda', etc.). Por defecto "cpu".
        
    Returns
    -------
    np.ndarray
        Array unidimensional de NumPy (forma: (512,)) de tipo float32,
        representando el embedding semántico normalizado.
    '''
    # 1. Tokenizar el texto: convertir las palabras en tensores que el modelo entiende
    inputs = processor(
        text=[texto], 
        return_tensors="pt", 
        padding=True, 
        truncation=True
    ).to(device)

    # 2. Inferencia: pasar los tokens por la red neuronal sin calcular gradientes
    with torch.no_grad():
        # Extraemos específicamente los "text_features" (no los de imagen)
        text_features = model.get_text_features(**inputs)
        
    # 3. Normalización L2 (Imprescindible para buscar luego por similitud coseno)
    text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
    
    # 4. Extraer el primer (y único) vector de la tanda y convertirlo a NumPy
    embedding_numpy = text_features.cpu().numpy()[0].astype(np.float32)
    
    return embedding_numpy