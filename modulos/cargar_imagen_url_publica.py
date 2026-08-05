import io
import requests
from PIL import Image

def cargar_imagen_url_publica(url: str) -> Image.Image:

    '''
    Dada una url de una imagen devuelve esa imagen en objeto image
    
    Parameters
    ----------
    url: la url
    
    Precondition
    ------------
    -
    
    Returns
    -------
    El objeto image de la imagen
    '''

    url = url.replace('w={width}', 'w=800')
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, timeout=10, headers=headers)
    if resp.status_code != 200:
        raise Exception(f'HTTP {resp.status_code}')
    return Image.open(io.BytesIO(resp.content)).convert('RGB')