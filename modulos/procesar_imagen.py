import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from transparent_background import Remover
from .quitar_fondo import quitar_fondo
from .calcular_embedding import calcular_embedding
from .reconocer_prenda import reconocer_prenda
from .detectar_color_prenda import detectar_color_prenda

def procesar_imagen(
    img: Image.Image, 
    processor: CLIPProcessor, 
    model: CLIPModel, 
    remover: Remover) -> tuple[Image.Image, np.ndarray, str, dict]:

    '''
    Dada una imagen nueva para la base de datos (de usuario o de catalogo)
    se procesa la imagen para dejarla en el formato pertinente y extraer
    las caracteristicas de ella que sean necesarias.
    
    Parameters
    ----------
    img: la imagen original
    processor: procesador de FashionCLIP
    model: modelo de FashionCLIP
    remover: elemina el fondo de la imagen, dejando solo la prenda
    
    Precondition
    ------------
    Imagen valida
    
    Returns
    -------
    image_clean: la imagen sin fondo
    embedding: el embedding correspondiente de FashionCLIP
    tipo_prenda: el tipo de prenda que es
    color: el color de la prenda (hex)
    '''

    image_clean = quitar_fondo(img, remover)
    
    embedding = calcular_embedding(image_clean, processor, model)

    tipo_prenda = reconocer_prenda(image_clean, processor, model)[0][0]

    color = detectar_color_prenda(image_clean)

    return embedding, tipo_prenda, color