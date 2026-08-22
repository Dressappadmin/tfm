from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos solo lo necesario para el arranque
from modulos.cargar_modelos import cargar_modelos

# Importamos nuestro nuevo router
from routers import datos_outfit, datos_prenda, generar_outfit, validar_outfit

# =====================================================================
# CICLO DE VIDA (LIFESPAN)
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Arrancando servidor: Cargando modelos de IA en memoria RAM...")
    processor, model, remover, outfit_generator = cargar_modelos()
    
    # Inyectamos los modelos en el estado de la app para que los routers puedan usarlos
    app.state.ml_models = {
        "processor": processor,
        "model": model,
        "remover": remover,
        "outfit_generator": outfit_generator
    }
    
    print("✅ Modelos cargados con éxito. API lista para recibir peticiones.")
    yield
    app.state.ml_models.clear()

# =====================================================================
# CONFIGURACIÓN DE FASTAPI
# =====================================================================
app = FastAPI(
    title="OutfitAI API - Buscador Híbrido",
    description="Generación de Outfits mediante Visión y LLM en 2 pasos",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# REGISTRO DE ROUTERS
# =====================================================================

app.include_router(datos_prenda.router)
app.include_router(datos_outfit.router)
app.include_router(generar_outfit.router)
app.include_router(validar_outfit.router)