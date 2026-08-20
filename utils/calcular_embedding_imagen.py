import numpy as np
from PIL import Image 
import torch
from transformers import CLIPProcessor, CLIPModel

def calcular_embedding_imagen(img: Image.Image, processor: CLIPProcessor, model: CLIPModel,) -> np.ndarray:

    '''
    Dada una imagen devuelve el vector de embedding de la misma para el modelo cargado FashionClip
    
    Parameters
    ----------
    img: la imagen de la que se quiere obtener el embedding
    processor: el procesador del modelo
    model: el modelo
    
    Returns
    -------
    El array de numpy correspondiente al embedding de la imagen.
    '''

    inputs = processor(images=img, return_tensors="pt")
    
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
    
    # Normalización L2 para que el producto escalar equivalga a Similitud Coseno
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    
    return image_features.squeeze().cpu().numpy().astype(np.float32)