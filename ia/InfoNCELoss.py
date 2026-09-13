import torch
import torch.nn as nn
import torch.nn.functional as F

class InfoNCELoss(nn.Module):
    def __init__(self, temperature=0.07):
        '''
        Inicializa la función de pérdida InfoNCELoss utilizando una temperatura ajustable para escalar los logits y un criterio de entropía cruzada estándar para optimizar el contraste entre muestras positivas y negativas.

        Parameters
        ----------
        temperature : float, optional
            Valor de temperatura que escala las similitudes del modelo para controlar la nitidez de la distribución Softmax (por defecto es 0.07).

        Returns
        ----------
        None
        '''
        super().__init__()
        self.temperature = temperature
        self.criterion = nn.CrossEntropyLoss()

    def forward(self, predicted_embeddings, target_embeddings):
        '''
        Calcula la pérdida InfoNCE (contrastive loss) normalizando los embeddings, computando la matriz de similitudes del coseno escalada por la temperatura y aplicando entropía cruzada para maximizar la similitud de las predicciones con sus objetivos (pares positivos) y minimizarla con el resto (negativos).

        Parameters
        ----------
        predicted_embeddings : torch.Tensor
            Tensor que contiene los vectores de embedding generados o predichos por el modelo para el lote (batch) actual.
        target_embeddings : torch.Tensor
            Tensor que contiene los vectores de embedding reales u objetivos correspondientes para el lote.

        Returns
        ----------
        torch.Tensor
            Tensor escalar que representa el valor de la pérdida calculada para la optimización del modelo.
        '''

        preds = F.normalize(predicted_embeddings, p=2, dim=-1)
        targets = F.normalize(target_embeddings, p=2, dim=-1)
        
        logits = torch.matmul(preds, targets.T) / self.temperature
        
        batch_size = preds.shape[0]
        labels = torch.arange(batch_size, device=preds.device)
        
        loss = self.criterion(logits, labels)
        
        return loss