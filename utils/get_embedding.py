import numpy as np
from PIL import Image 
import torch
from transformers import CLIPProcessor, CLIPModel
from config import DEVICE

def get_embedding(img: Image.Image, processor: CLIPProcessor, model: CLIPModel, device:str = DEVICE) -> np.ndarray:

    '''
    Dada una imagen devuelve el vector de embedding de la misma para el modelo cargado FashionClip
    
    Parameters
    ----------
    img: la imagen de la que se quiere obtener el embedding
    processor: el procesador de FashionCLIP
    model: el modelo FashionCLIP
    device: definido en el archivo config. 
    
    Precondition
    ------------
    -
    
    Returns
    -------
    El array de numpy correspondiente al embedding de la imagen.
    '''

    inputs = processor(images=img, return_tensors='pt').to(device)

    with torch.no_grad():

        output = model.get_image_features(**inputs)

        if hasattr(output, 'pooler_output'):

            vec = output.pooler_output.squeeze()
        else:

            vec = output.squeeze()

        vec = vec / vec.norm()

    return vec.cpu().numpy()