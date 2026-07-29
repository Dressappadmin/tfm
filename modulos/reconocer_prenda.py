from config import CATEGORIAS, DEVICE
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import torch

def reconocer_prenda(img: Image.Image, processor: CLIPProcessor, model: CLIPModel, categorias: list = CATEGORIAS, device: str = DEVICE) -> list[tuple[str, float]]:

    '''
    Dada una imagen devuelve el tipo de prenda que es (camiseta, pantalon) utilizando FashionCLIP
    
    Parameters
    ----------
    img: la imagen de la que se quiere obtener el embedding
    processor: el procesador de FashionCLIP
    model: el modelo FashionCLIP
    categorías: lista de tipos de prenda entre la que elegir la mas adecuada para la imagen
    
    Precondition
    ------------
    -
    
    Returns
    -------
    Las 3 prendas con mayor probabilidad de ser la de la imagen y sus respectivas probabilidades
    '''

    inputs = processor(text=categorias, images=img, return_tensors='pt', padding=True).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)

    top3_idx = probs[0].topk(3).indices.tolist()

    return [(categorias[i], float(probs[0][i])) for i in top3_idx]