import torch
from transformers import CLIPProcessor, CLIPModel
from transparent_background import Remover

# Detectar dispositivo una sola vez
device = "cuda" if torch.cuda.is_available() else "cpu"

def cargar_modelos():
    print(f'Cargando FashionCLIP en {device}...')
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained('patrickjohncyh/fashion-clip').to(device)
    clip_model.eval()

    print('Cargando modelo de fondo...')
    remover = Remover()
    
    print('Todos los modelos listos.')
    return clip_processor, clip_model, remover