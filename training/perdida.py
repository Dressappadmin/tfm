import torch
import torch.nn as nn
import torch.nn.functional as F

def perdida_coseno(anchor: torch.Tensor, positive: torch.Tensor, negative: torch.Tensor, margin: float = 0.2) -> torch.Tensor:
    '''
    Calcula la función de pérdida Triplet Loss utilizando la similitud del coseno, optimizando el modelo para que la predicción (anchor) sea más similar a la prenda elegida (positiva) que a la rechazada (negativa) por un margen específico. Ideal para el Hard Negative Mining.

    Parameters
    ----------
    anchor : torch.Tensor
        Tensor de dimensiones (Batch, Dim) con los vectores de embedding predichos por la red neuronal.
    positive : torch.Tensor
        Tensor de dimensiones (Batch, Dim) con los embeddings reales correspondientes a las prendas elegidas o correctas.
    negative : torch.Tensor
        Tensor de dimensiones (Batch, Dim) con los embeddings reales correspondientes a las prendas rechazadas o incorrectas.
    margin : float, optional
        Margen mínimo de separación exigido entre la similitud positiva y la similitud negativa (por defecto es 0.2).

    Returns
    ----------
    torch.Tensor
        Tensor escalar que contiene el valor promedio de la pérdida calculada para el lote (batch) actual, utilizado para la retropropagación.
    '''
    
    sim_pos = F.cosine_similarity(anchor, positive, dim=-1)
    sim_neg = F.cosine_similarity(anchor, negative, dim=-1)
    
    losses = F.relu(sim_neg - sim_pos + margin)
    
    return losses.mean()