import numpy as np

def normalizar_vector(vec: np.ndarray) -> list[float]:
    '''
    Asegura que el vector sea 1D y de norma unitaria para similitud coseno
    
    Parameters
    ----------
    vec: el vector
    
    Precondition
    ------------
    -
    
    Returns
    -------
    El vector normalizado
    '''

    vec_flat = np.asarray(vec, dtype=np.float32).flatten()
    norma = np.linalg.norm(vec_flat)
    vec_norm = vec_flat / norma if norma > 0 else vec_flat
    return [round(float(x), 6) for x in vec_norm]