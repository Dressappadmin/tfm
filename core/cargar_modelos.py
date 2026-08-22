import torch
from transformers import CLIPProcessor, CLIPModel
from transparent_background import Remover
from config import DEVICE
from generador_outfits.SequentialOutfitGenerator import SequentialOutfitGenerator

def cargar_modelos(device: str = DEVICE) -> tuple[CLIPProcessor, CLIPModel, Remover]:
    '''
    Descarga e inicializa en la memoria RAM los modelos de Inteligencia Artificial 
    necesarios para el procesamiento visual de la aplicación.
    
    Se encarga de instanciar el procesador y el modelo de FashionCLIP (para la 
    extracción de embeddings) y el modelo Remover (para la eliminación de fondos). 
    Esta función debe ejecutarse una única vez durante el ciclo de arranque del 
    servidor (lifespan) para evitar latencias severas en cada petición HTTP.
    
    Parameters
    ----------
    device : str, opcional
        Dispositivo de hardware donde se ejecutarán los modelos tensores 
        (ej. 'cpu', 'cuda', 'mps'). Por defecto utiliza la constante DEVICE de config.
    
    Precondition
    ------------
    El entorno debe disponer de suficiente memoria RAM (recomendado > 4GB) para 
    alojar ambos modelos simultáneamente. Si es la primera ejecución y no están 
    cacheados, requerirá conexión a internet para descargar los pesos desde Hugging Face.
    
    Returns
    -------
    tuple[CLIPProcessor, CLIPModel, Remover]
        Una tupla que contiene:
        - clip_processor: El procesador de FashionCLIP (transforma imágenes/texto a tensores).
        - clip_model: El modelo FashionCLIP cargado en el dispositivo y en modo evaluación.
        - remover: La instancia del modelo encargado de segmentar y eliminar fondos.
    '''

    print(f"🧠 Cargando modelos de IA en memoria ({device})...")

    # 1. Cargar el procesador base de CLIP
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    # 2. Cargar el modelo adaptado al dominio de la moda (FashionCLIP)
    clip_model = CLIPModel.from_pretrained('patrickjohncyh/fashion-clip').to(device)
    clip_model.eval()  # Lo ponemos en modo inferencia, no vamos a entrenarlo

    # 3. Cargar el modelo de eliminación de fondo
    remover = Remover()
    
    print("✅ Modelos cargados exitosamente.")

    # 4. NUEVO MODELO
    print("🧠 Cargando red generativa secuencial...")
    outfit_generator = SequentialOutfitGenerator()

    # Inyectamos el archivo .pth horneado en el Docker
    outfit_generator.load_state_dict(torch.load("pesos_recomendador_v1.pth", map_location=device))
    outfit_generator.eval() # Modo inferencia
    outfit_generator.to(device)

    return clip_processor, clip_model, remover, outfit_generator