import torch
import torch.nn as nn
import torch.nn.functional as F

import torch
import torch.nn as nn
import torch.nn.functional as F

class SequentialOutfitGenerator(nn.Module):
    def __init__(self, clip_dim=512, hidden_dim=256, color_dim=3, rnn_layers=1, num_tags=20):
        super(SequentialOutfitGenerator, self).__init__()
        
        self.num_slots = 6 # Superior, Inferior, Completo, Abrigo, Calzado, Accesorio
        
        # 1. Módulo del usuario
        self.user_encoder = nn.GRU(
            input_size=clip_dim, hidden_size=hidden_dim, num_layers=rnn_layers, batch_first=True
        )
        
        # 2. CAPA DE FUSIÓN MULTIMODAL (Actualizada)
        # Añadimos 'self.num_slots' a la dimensión de fusión para la máscara de presencia
        fusion_dim = hidden_dim + clip_dim + self.num_slots + num_tags + color_dim
        
        self.fusion_network = nn.Sequential(
            nn.Linear(fusion_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 512),
            nn.ReLU()
        )
        
        # 3. Cabezas por Slot (Igual que antes)
        self.slot_heads = nn.ModuleDict({
            'SUPERIOR': nn.Linear(512, clip_dim),
            'INFERIOR': nn.Linear(512, clip_dim),
            'CUERPO_COMPLETO': nn.Linear(512, clip_dim),
            'ABRIGO': nn.Linear(512, clip_dim),
            'CALZADO': nn.Linear(512, clip_dim),
            'ACCESORIO': nn.Linear(512, clip_dim)
        })

    def forward(self, user_history, partial_outfit_emb, slots_presence, tags_vector, color_explicito):
        """
        Nuevos parámetros:
        - partial_outfit_emb: Vector promedio de las prendas dadas (batch, 512)
        - slots_presence: Multi-hot indicando qué slots están ocupados (batch, 6)
        """
        _, h_n = self.user_encoder(user_history)
        user_state = h_n[-1] 
        
        # Unimos todo el contexto, incluyendo qué slots están presentes
        contexto_unificado = torch.cat([
            user_state, 
            partial_outfit_emb, 
            slots_presence,      # <--- La red ahora "ve" qué slots ya tiene el usuario
            tags_vector, 
            color_explicito
        ], dim=1)
        
        representacion_latente = self.fusion_network(contexto_unificado)
        
        predicciones = {}
        for slot_name, head in self.slot_heads.items():
            vector_crudo = head(representacion_latente)
            predicciones[slot_name] = F.normalize(vector_crudo, p=2, dim=1)
            
        return predicciones