from PIL import Image
from transparent_background import Remover

def remove_background(img_bytes: bytes, remover: Remover) -> Image.Image:

    '''
    Dada una imagen devuelve la misma imagen pero eliminando el fondo
    
    Parameters
    ----------
    img_bytes: la imagen de la que se quiere quitar el fondo, en bytes
    remover: el modelo que elimina el fondo
    
    Precondition
    ------------
    -
    
    Returns
    -------
    La imagen en RGB con el fondo quitado
    '''

    img = img_bytes.convert('RGB')

    out = remover.process(img, type='rgba')

    bg = Image.new('RGBA', out.size, (255, 255, 255, 255))

    bg.paste(out, mask=out.split()[3])
    
    return bg.convert('RGB')