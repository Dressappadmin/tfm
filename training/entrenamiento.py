from training.perdida_coseno import perdida_coseno

def entrenar_epoca(modelo, dataloader, optimizer):
    modelo.train()
    loss_acumulado = 0.0
    
    for batch in dataloader:
        optimizer.zero_grad()
        
        # 1. Extraemos el contexto
        user_history = batch['user_history']
        tags_vector = batch['tags_vector']
        color = batch['color_explicito']
        
        # 2. Extraemos los inputs del outfit parcial (generados por tu DataLoader)
        # partial_outfit: Tensor (batch, 512) con el promedio de las prendas dadas
        # slots_presence: Tensor (batch, 6) con 1s en los slots que se dan como input
        partial_outfit = batch['partial_outfit_emb']
        slots_presence = batch['slots_presence']
        
        # 3. Extraemos el Ground Truth (todas las prendas del outfit real)
        targets_reales = batch['targets'] 
        
        # Máscaras originales: indican qué slots existen realmente en este outfit
        mascaras_existencia = batch['mascaras'] 
        
        # =====================================================================
        # EL CAMBIO CLAVE: CREAR LA MÁSCARA DE PREDICCIÓN
        # Solo queremos que calcule Loss si: 
        # a) El slot existe en el outfit real (mascara_existencia == 1)
        # b) Y NO se lo hemos dado como input (slots_presence == 0)
        # =====================================================================
        
        # 4. Forward pass
        predicciones_modelo = modelo(user_history, partial_outfit, slots_presence, tags_vector, color)
        
        loss_batch = 0.0
        slots_presentes = 0 
        
        # Mapeo para relacionar el nombre del slot con el índice en slots_presence
        SLOT_INDEX = {'SUPERIOR': 0, 'INFERIOR': 1, 'CUERPO_COMPLETO': 2, 
                      'ABRIGO': 3, 'CALZADO': 4, 'ACCESORIO': 5}
        
        for slot in modelo.slot_heads.keys():
            idx = SLOT_INDEX[slot]
            
            # Comprobamos si, en todo el batch, hay algún outfit que necesite predecir este slot
            if slot in targets_reales:
                # mascara_prediccion = existe_en_real AND NOT dado_como_input
                # Extraemos la columna correspondiente de slots_presence: (batch_size,)
                dado_como_input = slots_presence[:, idx]
                
                # Invertimos el input (1 si NO se dio, 0 si se dio) y multiplicamos
                # mascara_prediccion valdrá 1 solo donde hay que predecir y calcular loss
                mascara_prediccion = mascaras_existencia[slot] * (1 - dado_como_input)
                
                # Solo calculamos si al menos un elemento del batch necesita este slot
                if mascara_prediccion.sum() > 0:
                    loss_cabeza = perdida_coseno(
                        prediccion = predicciones_modelo[slot],
                        target = targets_reales[slot],
                        mascara_validez = mascara_prediccion
                    )
                    
                    loss_batch += loss_cabeza
                    slots_presentes += 1
                
        # 5. Promediamos el loss y aplicamos backpropagation
        if slots_presentes > 0:
            loss_batch = loss_batch / slots_presentes
            loss_batch.backward()
            optimizer.step()
            
            loss_acumulado += loss_batch.item()
            
    return loss_acumulado / len(dataloader)