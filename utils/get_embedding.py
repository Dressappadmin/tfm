import numpy as np
from PIL import Image 
import torch
from config import device


def get_embedding(img: Image.Image, processor, model) -> np.ndarray:
    inputs = processor(images=img, return_tensors='pt').to(device)
    with torch.no_grad():
        output = model.get_image_features(**inputs)
        if hasattr(output, 'pooler_output'):
            vec = output.pooler_output.squeeze()
        else:
            vec = output.squeeze()
        vec = vec / vec.norm()
    return vec.cpu().numpy()