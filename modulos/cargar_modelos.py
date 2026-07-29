from transformers import CLIPProcessor, CLIPModel
from transparent_background import Remover
from config import DEVICE

def cargar_modelos(device: str = DEVICE) -> tuple[CLIPProcessor, CLIPModel, Remover]:
    
    '''
    Carga los modelos preentrenados que se utilizan:
        - FashionCLIP: para el reconocimiento de prendas
        - Remover: para eliminar el fondo de las imagenes
    Los modelos se cargan al construir la imagen del docker, asi no se tienen que
    recargar cada vez que se ejecute main.
    
    Parameters
    ----------
    device: definido en el archivo config. 
    
    Precondition
    ------------
    -
    
    Returns
    -------
    clip_procesor: procesador de fashionclip (<<el traductor>>) 
    clip_model: modelo de fashionclip (<<el cerebro>>) 
    remover: modelo que elimina el fondo
    '''

    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    clip_model = CLIPModel.from_pretrained('patrickjohncyh/fashion-clip').to(device)
    clip_model.eval()

    remover = Remover()
    
    return clip_processor, clip_model, remover