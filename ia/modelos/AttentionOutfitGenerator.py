import torch
import torch.nn as nn
import torch.nn.functional as F

class AttentionOutfitGenerator(nn.Module):
    def __init__(self, clip_dim=512, hidden_dim=512, color_dim=3, num_tags=9, num_slots=5, num_heads=8, num_layers=2):
        '''
        Inicializa las capas y componentes de la arquitectura del modelo AttentionOutfitGenerator, configurando las proyecciones lineales, embeddings de slots, codificador Transformer y la red de fusión para la recomendación de prendas.

        Parameters
        ----------
        clip_dim : int, optional
            Dimensión de los vectores de embedding CLIP (por defecto es 512).
        hidden_dim : int, optional
            Dimensión oculta interna utilizada para las representaciones vectoriales (por defecto es 512).
        color_dim : int, optional
            Dimensión del espacio de color de cada prenda (por defecto es 3).
        num_tags : int, optional
            Número total de etiquetas o tags de estilo soportadas (por defecto es 9).
        num_slots : int, optional
            Número total de categorías o slots de prendas disponibles (por defecto es 5).
        num_heads : int, optional
            Número de cabezas de atención en el codificador Transformer (por defecto es 8).
        num_layers : int, optional
            Número de capas apiladas del codificador Transformer (por defecto es 2).

        Returns
        ----------
        None
        '''
        super().__init__()
        self.clip_dim = clip_dim
        
        self.tag_proj = nn.Linear(num_tags, hidden_dim // 4)
        self.slot_embedding = nn.Embedding(num_slots, hidden_dim // 2) 
        
        self.item_proj = nn.Linear(clip_dim + color_dim, hidden_dim)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, 
            nhead=num_heads, 
            dim_feedforward=hidden_dim * 4, 
            dropout=0.1, 
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        fusion_dim = hidden_dim + (hidden_dim // 4) + (hidden_dim // 2)
        
        self.fusion_network = nn.Sequential(
            nn.Linear(fusion_dim, hidden_dim),
            nn.GELU(), 
            nn.LayerNorm(hidden_dim),
            nn.Dropout(0.2)
        )
        
        self.output_proj = nn.Linear(hidden_dim, clip_dim)

    def forward(self, history_clips, history_colors, target_slot, tags):
        '''
        Ejecuta la pasada hacia adelante (forward pass) del modelo AttentionOutfitGenerator para procesar el historial de interacciones del usuario junto con las características objetivo y predecir el embedding normalizado de la siguiente prenda recomendada.

        Parameters
        ----------
        history_clips : torch.Tensor
                Tensor que contiene los vectores de embedding CLIP históricos de las prendas con forma (Batch, Seq_Len, clip_dim).
        history_colors : torch.Tensor
                Tensor que contiene los vectores de color históricos de las prendas con forma (Batch, Seq_Len, color_dim).
        target_slot : torch.Tensor
                Tensor con el identificador del slot o categoría objetivo que se desea predecir.
        tags : torch.Tensor
                Tensor con las etiquetas o tags de estilo asociadas a la recomendación.

        Returns
        ----------
        torch.Tensor
                Tensor con el embedding predicho y normalizado mediante L2 para la nueva prenda recomendada.
        '''
        x_input = torch.cat([history_clips, history_colors], dim=-1)
        
        x = self.item_proj(x_input) 
        transformer_out = self.transformer(x) 
        
        user_context = transformer_out[:, -1, :] 
        
        tag_emb = self.tag_proj(tags)
        slot_emb = self.slot_embedding(target_slot)

        fused = torch.cat([user_context, tag_emb, slot_emb], dim=-1)
        refined_context = self.fusion_network(fused)

        predicted_embedding = self.output_proj(refined_context)
        predicted_embedding = F.normalize(predicted_embedding, p=2, dim=-1)
        
        return predicted_embedding