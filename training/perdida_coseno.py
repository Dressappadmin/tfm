def perdida_coseno(prediccion, target, mascara_validez=None):
    """
    Calcula la pérdida basada en la similitud del coseno.
    Al estar normalizados en L2 previamente, la similitud va de -1 a 1.
    Queremos que la distancia (1 - similitud) tienda a 0.
    """
    # sim = F.cosine_similarity(prediccion, target, dim=1) -> shape: (batch_size,)
    similitud = F.cosine_similarity(prediccion, target, dim=1)
    distancia = 1.0 - similitud
    
    if mascara_validez is not None:
        # Aplicamos la máscara (0 o 1) para ignorar outfits del batch que no tengan este slot
        distancia = distancia * mascara_validez
        # Hacemos la media solo sobre los ejemplos válidos
        suma_loss = distancia.sum()
        elementos_validos = mascara_validez.sum()
        # Evitamos división por cero
        return suma_loss / (elementos_validos + 1e-8)
    
    return distancia.mean()