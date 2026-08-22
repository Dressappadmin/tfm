import numpy as np
from fastapi import APIRouter, HTTPException, Body
from openai import OpenAI

# Importamos tu cliente de base de datos y utilidades
from data.supabase import supabase
from config import LLM_API_KEY, OUTFITS_TABLA, SLOT_PRENDA, PRENDAS_TABLA, ID_PRENDA, ID_OUTFIT, IDS_PRENDAS_OUTFIT, EMBEDDING_PRENDA, EMBEDDING_OUTFIT

# Asumo que tienes una función de validación ya creada (ajusta la importación a tu ruta real)
from modulos.validar_reglas_outfit import validar_reglas_outfit 
from schemas.ValidarOutfitRequest import ValidarOutfitRequest

# Definimos el esquema de lo que va a recibir el endpoint
router = APIRouter(
    prefix="/outfits", 
    tags=["Gestión de Outfits"]
)

# ---------------------------------------------------------
# ENDPOINT 1: VALIDAR COMBINACIÓN DE PRENDAS
# ---------------------------------------------------------
@router.post("/validar_outfit") # Cambiamos a POST para recibir el JSON en el body
async def validar_outfit(request: ValidarOutfitRequest):
    """
    Dada una lista de IDs de prendas, extrae sus tipos (family) 
    y comprueba si forman un conjunto válido.
    """
    try:
        prendas_ids = request.prendas_ids

        # 1. Validación básica
        if not prendas_ids or len(prendas_ids) == 0:
            raise HTTPException(status_code=400, detail="La lista de prendas está vacía.")

        # 2. Recuperar el tipo (family) de cada prenda directamente
        # Usamos el operador 'in' para traer todas las prendas de una sola consulta
        resp_prendas = supabase.table(PRENDAS_TABLA).select(ID_PRENDA, SLOT_PRENDA).in_(ID_PRENDA, prendas_ids).execute()
        
        if not resp_prendas.data:
            raise HTTPException(status_code=404, detail="No se encontraron las prendas en la BD.")

        # Extraemos la lista de categorías detectadas
        slots_prendas = [prenda[SLOT_PRENDA] for prenda in resp_prendas.data if prenda.get(SLOT_PRENDA)]

        # 3. Validar utilizando tu lógica ya creada
        es_valido = validar_reglas_outfit(slots_prendas)
        mensaje = "Outfit válido" if es_valido else "Faltan prendas básicas (Top/Bottom o Vestido)."

        # -------------------------------------------------------------------------

        if not es_valido:
            return {"status": "invalid", "mensaje": mensaje, "categorias": slots_prendas}

        return {
            "status": "success",
            "mensaje": "El outfit cumple con las reglas de moda.",
            "categorias": slots_prendas
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())

# ---------------------------------------------------------
# ENDPOINT 2: CALCULAR CAMPOS DEL OUTFIT
# ---------------------------------------------------------
# Definimos el Router
router = APIRouter(
    prefix="/outfits", 
    tags=["Gestión de Outfits"]
)

openai_client = OpenAI(api_key=LLM_API_KEY)

@router.put("/datos_outfit/{outfit_id}")
async def datos_outfit(outfit_id: str):
    """
    Calcula el vector característico (embedding) de un outfit como
    la media normalizada de los embeddings de sus prendas y lo guarda en BD.
    """
    try:
        # 1. Recuperar los IDs de las prendas del outfit
        resp_outfit = supabase.table(OUTFITS_TABLA).select("prendas_ids").eq(ID_PRENDA, outfit_id).execute()
        
        if not resp_outfit.data:
            raise HTTPException(status_code=404, detail="Outfit no encontrado.")
            
        prendas_ids = resp_outfit.data[0].get(IDS_PRENDAS_OUTFIT, [])
        if not prendas_ids:
            raise HTTPException(status_code=400, detail="El outfit no tiene prendas asignadas.")

        # 2. Recuperar los embeddings de esas prendas
        resp_prendas = supabase.table(PRENDAS_TABLA).select(EMBEDDING_PRENDA).in_(ID_PRENDA, prendas_ids).execute()
        
        embeddings_list = [prenda[EMBEDDING_PRENDA] for prenda in resp_prendas.data if prenda.get(EMBEDDING_PRENDA)]
        
        if not embeddings_list:
            raise HTTPException(status_code=400, detail="Las prendas de este outfit no tienen embeddings calculados.")

        # 3. Matemáticas: Calcular el embedding del outfit
        # El embedding de un conjunto se suele calcular como la media de sus prendas
        matriz_embeddings = np.array(embeddings_list) # Convertimos a matriz NumPy
        
        # Calculamos la media por columnas (axis=0)
        outfit_embedding_raw = np.mean(matriz_embeddings, axis=0)
        
        # Es CRÍTICO normalizar el vector resultante para que la similitud Coseno funcione bien luego
        norma = np.linalg.norm(outfit_embedding_raw)
        outfit_embedding_normalized = outfit_embedding_raw / norma if norma > 0 else outfit_embedding_raw

        # Convertimos de vuelta a lista de Python estricta (floats) para guardarlo en la BD (pgvector)
        outfit_embedding_final = outfit_embedding_normalized.tolist()

        # 4. Actualizar la tabla OUTFITS en Supabase
        update_bd = supabase.table(OUTFITS_TABLA).update({EMBEDDING_OUTFIT: outfit_embedding_final}).eq(ID_OUTFIT, outfit_id).execute()

        if not update_bd.data:
            raise HTTPException(status_code=500, detail="Error interno al actualizar el embedding en Supabase.")

        return {
            "status": "success",
            "mensaje": f"Embedding calculado (promedio de {len(embeddings_list)} prendas) y guardado.",
            "outfit_id": outfit_id,
            "dimensiones": len(outfit_embedding_final)
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())

# ---------------------------------------------------------
# ENDPOINT 3: GENERAR OUTFIT
# ---------------------------------------------------------
@router.post("/generar-outfit")
async def generar_outfit(
    request: Request,
    datos: GenerarOutfitExistenteRequest = Body(...)
):
    """
    Genera un outfit a partir de una prenda que el usuario ya tiene guardada en su perfil/BD.
    """
    try:
        from data.catalogos import prendas as catalogo

        # Recuperamos los modelos desde el estado global de la aplicación (cargados en main.py)
        ml_models = request.app.state.ml_models
        processor = ml_models["processor"]
        model = ml_models["model"]

        # 1. Buscamos la prenda seleccionada en Supabase
        respuesta = await asyncio.to_thread(
            lambda: supabase.table(PRENDAS_TABLA).select("*").eq(COL_ID, datos.prenda_id).single().execute()
        )
        
        prenda_base = respuesta.data
        if not prenda_base:
            raise HTTPException(status_code=404, detail="La prenda seleccionada no existe en tu armario.")

        # Extraemos los datos que YA estaban calculados
        embedding_final = prenda_base.get(COL_EMBEDDING)
        tipo_prenda_final = prenda_base.get(COL_TIPO_PRENDA, "OTRO")
        color_final_hex = prenda_base.get(COL_COLOR, "#FFFFFF")
        etiquetas_ai = None
        embedding_texto_puro = None

        # 2. Si el usuario añadió texto opcional (ej: "combínalo para la playa"), fusionamos con el texto
        if datos.texto:
            # procesar_texto extraerá las etiquetas y el embedding del prompt
            emb_txt, etiquetas_ai = await asyncio.to_thread(
                procesar_texto, datos.texto, openai_client, processor, model
            )
            embedding_texto_puro = emb_txt
            
            # Fusión del vector existente con el vector del nuevo texto
            if embedding_final:
                embedding_final = (np.array(embedding_final) + emb_txt) / 2.0
                embedding_final = embedding_final / np.linalg.norm(embedding_final)

        # 3. Generamos las prendas complementarias con el motor de IA
        prendas_complementarias = await asyncio.to_thread(
            completar_outfit_con_texto,
            tipo_prenda=tipo_prenda_final,
            top_n=10,
            temperatura=0.2,
            color_hex=color_final_hex,
            query_emb=embedding_final,
            catalog=catalogo,
            etiquetas=etiquetas_ai,
            embedding_texto=embedding_texto_puro
        )

        # 4. Construimos la lista final de IDs (Prenda base + prendas recomendadas)
        ids_finales = [datos.prenda_id]
        ids_finales.extend([p.get(COL_ID) for p in prendas_complementarias])

        return {
            "status": "success",
            "prenda_origen": prenda_base,
            "outfit_generado": prendas_complementarias,
            "ids_outfit": ids_finales,
            "mensaje": "Outfit generado desde tu armario correctamente."
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())

# ---------------------------------------------------------
# ENDPOINT 4: GENERAR OUTFIT AVANZADO
# ---------------------------------------------------------
@router.post("/generar-outfit-avanzado")
async def generar_outfit_avanzado(
    request: Request,
    datos: GenerarOutfitRequest = Body(...)
):
    try:
        # Recuperamos la red PyTorch cargada en memoria (definida en main.py)
        # Asumimos que el modelo ya tiene model.eval() aplicado al cargar
        red_generadora = request.app.state.ml_models["sequential_generator"]
        
        # =====================================================================
        # 1. OBTENER EMBEDDINGS DE LAS PRENDAS INPUT
        # =====================================================================
        if not datos.prendas_input:
            raise HTTPException(status_code=400, detail="Debes proporcionar al menos una prenda.")

        lista_ids_input = list(datos.prendas_input.values())
        
        # Consulta SQL a Supabase: obtener todas las prendas del input de golpe
        respuesta_input = await asyncio.to_thread(
            lambda: supabase.table(PRENDAS_TABLA).select("*").in_(ID_PRENDA, lista_ids_input).execute()
        )
        
        # Convertimos la respuesta a un diccionario fácil de usar
        prendas_db = {p[ID_PRENDA]: p for p in respuesta_input.data}
        
        # Mapeamos los tensores y extraemos el color promedio (muy simplificado)
        dict_tensores_input = {}
        color_promedio = torch.zeros(1, 3) # RGB
        
        for slot, prenda_id in datos.prendas_input.items():
            if prenda_id not in prendas_db:
                raise HTTPException(status_code=404, detail=f"Prenda no encontrada: {prenda_id}")
            
            emb = torch.tensor(prendas_db[prenda_id][EMBEDDING_PRENDA], dtype=torch.float32)
            dict_tensores_input[slot] = emb
            color_promedio += hex_a_tensor_color(prendas_db[prenda_id][COLOR_PRENDA])
            
        color_promedio = color_promedio / len(datos.prendas_input)

        # =====================================================================
        # 2. OBTENER EL HISTORIAL DEL USUARIO
        # =====================================================================
        historial_embeddings = []
        if datos.historial_usuario_ids:
            respuesta_historial = await asyncio.to_thread(
                lambda: supabase.table(USUARIOS_TABLA).select(EMBEDDING_USUARIO).in_(ID_USUARIO, datos.historial_usuario_ids).execute()
            )
            # Extraemos la lista de tensores
            historial_embeddings = [p[EMBEDDING_USUARIO] for p in respuesta_historial.data]
            
        # =====================================================================
        # 3. PROCESAR EL TEXTO (LLM -> TAXONOMÍA MULTI-HOT)
        # =====================================================================
        # Vector por defecto (todo ceros) si no hay texto
        tags_vector_tensor = torch.zeros(1, 20) 
        
        if datos.texto:
            # extraer_tags_llm usa a Gemini/OpenAI para devolver una lista: ['Formal', 'Verano']
            etiquetas_extraidas = await asyncio.to_thread(
                extraer_tags_llm, datos.texto, openai_client
            )
            # tags_a_multihot convierte ['Formal', 'Verano'] en [0,1,0,0,1...]
            tags_vector_tensor = tags_a_multihot(etiquetas_extraidas)

        # =====================================================================
        # 4. PREPARAR TENSORES PARA LA RED NEURONAL
        # =====================================================================
        # Creamos el partial_outfit (Promedio) y el slots_presence (Máscara)
        partial_outfit_emb, slots_presence = preparar_outfit_parcial(dict_tensores_input)
        
        # Preparamos el historial (Padding a longitud máxima y batch dim)
        user_history_tensor = preparar_user_history(historial_embeddings, max_seq_len=10)

        # =====================================================================
        # 5. INFERENCIA CON LA RED (Paso rápido en CPU/GPU)
        # =====================================================================
        with torch.no_grad():
            predicciones_slots = red_generadora(
                user_history=user_history_tensor,
                partial_outfit_emb=partial_outfit_emb,
                slots_presence=slots_presence,
                tags_vector=tags_vector_tensor,
                color_explicito=color_promedio
            )

        # =====================================================================
        # 6. BÚSQUEDA VECTORIAL EN BASE DE DATOS
        # =====================================================================
        # ¿Qué slots nos faltan rellenar?
        slots_input = set(datos.prendas_input.keys())
        
        # NOTA: En un caso real, no queremos forzar a generar SIEMPRE los 6 slots.
        # Aquí usarías tu lógica de compatibilidad o permitirías al usuario decir qué necesita.
        # Para el ejemplo, buscamos los que faltan.
        slots_a_buscar = [s for s in TODOS_LOS_SLOTS if s not in slots_input]
        
        outfit_generado = []
        
        for slot in slots_a_buscar:
            vector_objetivo = predicciones_slots[slot].squeeze(0).tolist()
            
            # Buscamos en pgvector la prenda de ESE slot más cercana al vector generado
            # usando una función RPC en Supabase que haga búsqueda por coseno
            respuesta_rpc = await asyncio.to_thread(
                lambda: supabase.rpc(
                    "match_prendas_por_slot", 
                    {
                        "query_embedding": vector_objetivo,
                        "match_slot": slot,
                        "match_count": 1 # Cogemos la mejor opción
                    }
                ).execute()
            )
            
            if respuesta_rpc.data:
                outfit_generado.append(respuesta_rpc.data[0])

        return {
            "status": "success",
            "prendas_input": prendas_db,
            "outfit_generado": outfit_generado,
            "mensaje": "Outfit generado inteligentemente mediante Deep Learning."
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())