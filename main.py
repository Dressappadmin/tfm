# IMPORTS DE LIBRERÍAS EXTERNAS
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from PIL import Image
import matplotlib.pyplot as plt
import io

# IMPORTAMOS LIBRERÍAS Y MÓDULOS INTERNOS
from config import *
from data.db_loader import catalog
from modulos.cargar_modelos import cargar_modelos
from modulos.procesar_imagen import procesar_imagen
from modulos.completar_outfit import completar_outfit

# PIPELINE
def pipeline(processor, model, remover, img, catalog, top_n=5, temperatura=0.15):

    # PROCESAMOS IMAGEN
    embedding, tipo_prenda, color = procesar_imagen(img, processor, model, remover)

    # GENERAMOS UN OUTFIT
    matches = completar_outfit(tipo_prenda, top_n, temperatura, color, embedding, catalog)

    return matches

# API
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ESTO SE EJECUTA UNA SOLA VEZ AL ENCENDER LA API
    print("Arrancando servidor: Cargando modelos en memoria RAM...")
    processor, model, remover = cargar_modelos()
    
    # Los guardamos en el diccionario global
    ml_models["processor"] = processor
    ml_models["model"] = model
    ml_models["remover"] = remover
    print("Modelos cargados. API lista para recibir peticiones.")
    
    yield
    
    # ESTO SE EJECUTA AL APAGAR LA API (Para liberar memoria)
    ml_models.clear()

# API
# Inicializamos pasándole el lifespan
app = FastAPI(
    title="OutfitAI API",
    description="Motor de recomendación y análisis visual de prendas",
    version="1.0.0",
    lifespan=lifespan # Conectamos el ciclo de vida
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Peticiones
@app.post("/analyze-outfit")
async def analyze_outfit_endpoint(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen válida.")

    try:
        image_bytes = await file.read()
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # límite de resolución
        img.thumbnail((1024, 1024))

        # RESCATAMOS LOS MODELOS DE LA MEMORIA RAM
        processor = ml_models["processor"]
        model = ml_models["model"]
        remover = ml_models["remover"]

        # Pipeline
        matches = pipeline(processor, model, remover, img, catalog)

        return {
            "status": "success",
            "resultados": {
                "recomendaciones": [m.get(COL_ID) for m in matches],
            }
        }

    except Exception as e:
        import traceback
        error_completo = traceback.format_exc()
        print(error_completo) 
        raise HTTPException(status_code=500, detail=error_completo)