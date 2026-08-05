import io
import requests
from PIL import Image
from requests.exceptions import RequestException

def cargar_imagen_url_bucket(url: str, timeout: int = 10) -> Image.Image:
    '''
    Descarga una imagen desde una URL pública de un bucket y la convierte 
    en un objeto PIL Image en formato RGB.

    Parameters
    ----------
    url : str
        La URL web o del bucket donde está almacenada la imagen.
    timeout : int, opcional
        Tiempo máximo de espera en segundos para la petición HTTP (por defecto 10).

    Returns
    -------
    Image.Image
        La imagen cargada y convertida al modo RGB.

    Raises
    ------
    ValueError
        Si la URL está vacía o es inválida.
    RuntimeError
        Si ocurre un error de red o el archivo no es una imagen válida.
    '''
    if not url or not isinstance(url, str):
        raise ValueError("La URL proporcionada debe ser una cadena de texto válida y no vacía.")

    try:
        # 1. Realizar petición HTTP con timeout para no bloquear el servidor en Cloud Run
        respuesta = requests.get(url, timeout=timeout)
        respuesta.raise_for_status()  # Lanza excepción si el código no es 200 OK

        # 2. Leer los bytes en memoria sin escribir en disco temporal
        imagen_bytes = io.BytesIO(respuesta.content)

        # 3. Abrir la imagen con PIL y asegurar espacio de color RGB
        imagen_pil = Image.open(imagen_bytes)
        return imagen_pil.convert("RGB")

    except RequestException as error_red:
        raise RuntimeError(
            f"Error de comunicación al descargar la imagen desde el bucket ({url}): {error_red}"
        ) from error_red
    except Exception as error_imagen:
        raise RuntimeError(
            f"El archivo descargado de '{url}' no pudo procesarse como una imagen válida: {error_imagen}"
        ) from error_imagen