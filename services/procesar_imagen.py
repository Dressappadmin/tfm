import numpy as np
import torch
from PIL import Image
from sklearn.cluster import KMeans
from transformers import CLIPProcessor, CLIPModel
from transparent_background import Remover
import numpy as np
from utils.catalogos import CATEGORIAS
from ia.device import DEVICE


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

def quitar_fondo(img: Image.Image, remover: Remover) -> Image.Image:
    '''
    Elimina el fondo de una imagen dejando únicamente el sujeto principal.
    
    Utiliza el modelo preentrenado de 'transparent_background' para generar 
    una máscara de segmentación y aplicar un fondo blanco puro.
    
    Parameters
    ----------
    img : Image.Image
        La imagen original cargada mediante PIL.
    remover : Remover
        Instancia del modelo de eliminación de fondo inicializado en memoria.
    
    Precondition
    ------------
    El modelo Remover debe estar cargado correctamente en el dispositivo (CPU/GPU).
    
    Returns
    -------
    Image.Image
        La nueva imagen en formato RGB con el fondo original reemplazado por blanco.
    '''
    # Nos aseguramos de trabajar en modo RGB estándar
    img = img.convert('RGB')

    # Genera la imagen RGBA (con canal alfa/transparencia en el fondo)
    out = remover.process(img, type='rgba')

    # Creamos un lienzo en blanco del mismo tamaño
    bg = Image.new('RGBA', out.size, (255, 255, 255, 255))

    # Pegamos la prenda sobre el lienzo blanco usando el canal alfa como máscara
    bg.paste(out, mask=out.split()[3])
    
    return bg.convert('RGB')

def detectar_color_prenda(
    img_clean: Image.Image, 
    bg_color: tuple[int, int, int] = (255, 255, 255), 
    tol: int = 18
) -> dict[str, str | tuple[int, int, int]]:
    '''
    Detecta el color predominante de una prenda ignorando el fondo.
    
    Aplica el algoritmo de clustering K-means (K=3) sobre los píxeles de la prenda
    para agrupar los colores y descartar sombras o brillos, quedándose con el 
    centroide del cluster más numeroso.
    
    Parameters
    ----------
    img_clean : Image.Image
        La imagen de la prenda ya procesada (sin fondo original).
    bg_color : tuple[int, int, int], opcional
        El color RGB del fondo insertado previamente, por defecto blanco (255, 255, 255).
    tol : int, opcional
        Tolerancia (distancia euclidiana) para considerar que un píxel es parte 
        del fondo y debe ser ignorado, por defecto 18.
    
    Precondition
    ------------
    La imagen debe haber pasado por la función `quitar_fondo` para tener un 
    fondo uniforme y predecible.
    
    Returns
    -------
    dict[str, str | tuple[int, int, int]]
        Diccionario con dos claves:
        - 'hex': El color predominante en formato hexadecimal (str).
        - 'rgb': El color predominante en formato RGB (tupla de 3 enteros).
    '''
    arr = np.array(img_clean.convert('RGB'))
    pixels = arr.reshape(-1, 3)
    
    # Calcular distancia de cada píxel al color de fondo
    dist_to_bg = np.sqrt(((pixels.astype(int) - np.array(bg_color)) ** 2).sum(axis=1))
    
    # Filtrar píxeles que pertenecen a la prenda
    fg_pixels = pixels[dist_to_bg > tol]
    if len(fg_pixels) < 10:
        fg_pixels = pixels  # Fallback en caso de que la imagen sea casi toda blanca
        
    k = min(3, len(fg_pixels))
    km = KMeans(n_clusters=k, n_init=4, random_state=0).fit(fg_pixels)
    
    counts = np.bincount(km.labels_)
    dominante = km.cluster_centers_[counts.argmax()].astype(int)
    
    hex_color = '#{:02X}{:02X}{:02X}'.format(*dominante)
    return {'hex': hex_color, 'rgb': tuple(int(x) for x in dominante)}

def reconocer_prenda(
    img: Image.Image, 
    processor: CLIPProcessor, 
    model: CLIPModel, 
    categorias: list[str] = CATEGORIAS, 
    device: str = DEVICE
) -> list[tuple[str, float]]:
    '''
    Clasifica el tipo de prenda de una imagen mediante Zero-Shot classification.
    
    Utiliza FashionCLIP para proyectar la imagen y las categorías de texto en el 
    mismo espacio vectorial y calcular la probabilidad de coincidencia (softmax).
    
    Parameters
    ----------
    img : Image.Image
        Imagen de la prenda a clasificar.
    processor : CLIPProcessor
        Procesador de Hugging Face para FashionCLIP.
    model : CLIPModel
        Modelo FashionCLIP cargado en memoria.
    categorias : list[str], opcional
        Lista de etiquetas de texto a comparar, por defecto usa CATEGORIAS de config.
    device : str, opcional
        Dispositivo de inferencia ('cpu' o 'cuda'), por defecto usa DEVICE de config.
    
    Returns
    -------
    list[tuple[str, float]]
        Una lista con el Top 3 de prendas más probables. Cada elemento es una 
        tupla que contiene el nombre de la categoría y su probabilidad (0.0 a 1.0).
    '''
    inputs = processor(text=categorias, images=img, return_tensors='pt', padding=True).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)

    top3_idx = probs[0].topk(3).indices.tolist()

    return [(categorias[i], float(probs[0][i])) for i in top3_idx]

def procesar_imagen(
    img: Image.Image, 
    processor: CLIPProcessor, 
    model: CLIPModel, 
    remover: Remover
) -> tuple[np.ndarray, str, dict[str, str | tuple[int, int, int]]]:
    '''
    Pipeline completo que extrae todas las características necesarias de una imagen.
    
    Orquesta las funciones de eliminación de fondo, cálculo de embeddings visuales,
    clasificación de categoría y detección del color predominante en una sola pasada.
    
    Parameters
    ----------
    img : Image.Image
        La imagen original proporcionada por el usuario o catálogo.
    processor : CLIPProcessor
        Procesador del modelo FashionCLIP.
    model : CLIPModel
        Modelo visual FashionCLIP.
    remover : Remover
        Modelo de segmentación para eliminar el fondo.
    
    Precondition
    ------------
    Todos los modelos (CLIP y Remover) deben estar cargados correctamente en memoria.
    
    Returns
    -------
    tuple[np.ndarray, str, dict]
        Una tupla que contiene:
        - embedding: Vector visual característico de 512 dimensiones (ndarray).
        - tipo_prenda: El nombre de la categoría de prenda detectada con mayor probabilidad (str).
        - color: Diccionario con los valores hex y rgb del color dominante (dict).
    '''
    # 1. Limpieza de imagen
    image_clean = quitar_fondo(img, remover)
    
    # 2. Extracción de Embedding
    embedding = calcular_embedding_imagen(image_clean, processor, model)

    # 3. Categorización (nos quedamos solo con la mejor predicción: posición 0, clave 0)
    tipo_prenda = reconocer_prenda(image_clean, processor, model)[0][0]

    # 4. Extracción de color dominante
    color = detectar_color_prenda(image_clean)

    return embedding, tipo_prenda, color