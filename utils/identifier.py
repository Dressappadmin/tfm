from config import CATEGORIAS, device
from PIL import Image
import torch

def reconocer_prenda(img: Image.Image, processor, model, categorias: list =CATEGORIAS) -> list:
    """Usa FashionCLIP para identificar qué tipo de prenda es."""
    inputs = processor(text=categorias, images=img, return_tensors='pt', padding=True).to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
    top3_idx = probs[0].topk(3).indices.tolist()
    return [(categorias[i], float(probs[0][i])) for i in top3_idx]