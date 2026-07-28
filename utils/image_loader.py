from PIL import Image

def get_public_url(img_url_value: str) -> str:
    url = img_url_value
    url = url.replace('w={width}', 'w=800')
    return url

def load_image_from_url(url: str) -> Image.Image:
    url = url.replace('w={width}', 'w=800')
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, timeout=10, headers=headers)
    if resp.status_code != 200:
        raise Exception(f'HTTP {resp.status_code}')
    return Image.open(io.BytesIO(resp.content)).convert('RGB')

def get_imagen():

    ruta_imagen = "data/ejemplo.jpg" 

    imagen = Image.open(ruta_imagen)

    return imagen