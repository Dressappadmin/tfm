from PIL import Image
from sklearn.cluster import KMeans
import numpy as np

def detectar_color_prenda(img_clean: Image.Image, bg_color: tuple =(255, 255, 255), tol: int =18) -> dict:

    '''
    Dada una imagen detecta el color predominante de la misma.
        - Descarta píxeles de fondo (blancos).
        - Agrupa el resto en 3 clusters (K-means) para ignorar sombras/reflejos.
        - Se queda con el cluster más grande = color dominante real.
    
    Parameters
    ----------
    img_clean: la imagen
    bg_color: el color del fondo, blanco puro
    tol: tolerancia de distancia de color para descartar píxeles cercanos a bg_color.
    
    Precondition
    ------------
    La imagen no debe tener fondo
    
    Returns
    -------
    Un diccionario con la entrada 'hex' y otra 'rgb' para el color dominante
    '''

    arr = np.array(img_clean.convert('RGB'))
    pixels = arr.reshape(-1, 3)
    dist_to_bg = np.sqrt(((pixels.astype(int) - np.array(bg_color)) ** 2).sum(axis=1))
    fg_pixels = pixels[dist_to_bg > tol]
    if len(fg_pixels) < 10:
        fg_pixels = pixels
    k = min(3, len(fg_pixels))
    km = KMeans(n_clusters=k, n_init=4, random_state=0).fit(fg_pixels)
    counts = np.bincount(km.labels_)
    dominante = km.cluster_centers_[counts.argmax()].astype(int)
    hex_color = '#{:02X}{:02X}{:02X}'.format(*dominante)
    return {'hex': hex_color, 'rgb': tuple(int(x) for x in dominante)}
