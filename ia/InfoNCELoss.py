import torch
import torch.nn as nn
import torch.nn.functional as F

class InfoNCELoss(nn.Module):
    def __init__(self, temperature=0.07):
        super().__init__()
        # La temperatura escala los valores para que la función Softmax 
        # (dentro de CrossEntropy) sea más "agresiva" separando positivos de negativos.
        self.temperature = temperature
        self.criterion = nn.CrossEntropyLoss()

    def forward(self, predicted_embeddings, target_embeddings):
        # 1. Asegurarnos de que ambos vectores están normalizados (L2)
        preds = F.normalize(predicted_embeddings, p=2, dim=-1)
        targets = F.normalize(target_embeddings, p=2, dim=-1)
        
        # 2. Calcular matriz de similitud coseno (Batch_size x Batch_size)
        # Multiplicar una matriz por su transpuesta calcula el producto escalar de todos con todos
        logits = torch.matmul(preds, targets.T) / self.temperature
        
        # 3. Las "etiquetas correctas" están en la diagonal [0, 1, 2, ..., batch_size-1]
        batch_size = preds.shape[0]
        labels = torch.arange(batch_size, device=preds.device)
        
        # 4. Calcular pérdida
        loss = self.criterion(logits, labels)
        
        return loss