import torch
import torch.nn as nn
import torch.nn.functional as F

class AttentionOutfitGenerator(nn.Module):
    def __init__(self, clip_dim=512, hidden_dim=512, color_dim=3, num_tags=9, num_slots=5, num_heads=8, num_layers=2):
        super().__init__()
        self.clip_dim = clip_dim
        
        # 1. PROYECCIONES DE CONTEXTO (Mejor que concatenar en crudo)
        self.color_proj = nn.Linear(color_dim, hidden_dim // 4)
        self.tag_proj = nn.Linear(num_tags, hidden_dim // 4)
        # Usamos Embedding real para los slots en lugar de una máscara One-Hot
        self.slot_embedding = nn.Embedding(num_slots, hidden_dim // 2) 
        
        # Proyección de entrada para igualar dimensiones
        self.item_proj = nn.Linear(clip_dim, hidden_dim)
        
        # 2. MECANISMO DE ATENCIÓN (Sustituye a la GRU)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, 
            nhead=num_heads, 
            dim_feedforward=hidden_dim * 4, 
            dropout=0.1, 
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # 3. RED DE FUSIÓN TARDÍA (Late Fusion)
        fusion_dim = hidden_dim + (hidden_dim // 4) + (hidden_dim // 4) + (hidden_dim // 2)
        
        self.fusion_network = nn.Sequential(
            nn.Linear(fusion_dim, hidden_dim),
            nn.GELU(), # GELU suele funcionar mejor que ReLU con Transformers
            nn.LayerNorm(hidden_dim),
            nn.Dropout(0.2)
        )
        
        # 4. PROYECCIÓN CONTRASTIVA FINAL
        self.output_proj = nn.Linear(hidden_dim, clip_dim)

    def forward(self, history_clips, target_slot, tags, color):
        # history_clips: (Batch, Seq_Len, clip_dim)
        
        # 1. Entender el historial con Self-Attention
        x = self.item_proj(history_clips) 
        transformer_out = self.transformer(x) 
        
        # Tomamos el último estado, que ahora contiene atención sobre toda la secuencia
        user_context = transformer_out[:, -1, :] 
        
        # 2. Codificar el contexto
        color_emb = self.color_proj(color)
        tag_emb = self.tag_proj(tags)
        slot_emb = self.slot_embedding(target_slot)
        
        # 3. Fusión
        fused = torch.cat([user_context, color_emb, tag_emb, slot_emb], dim=-1)
        refined_context = self.fusion_network(fused)
        
        # 4. Predicción en el Espacio Latente
        predicted_embedding = self.output_proj(refined_context)
        
        # ¡CRÍTICO! Normalización L2 para búsqueda por Similitud Coseno
        predicted_embedding = F.normalize(predicted_embedding, p=2, dim=-1)
        
        return predicted_embedding