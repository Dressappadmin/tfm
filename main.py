from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos la lógica de inicialización y nuestro cliente HTTP
from core.cargar_modelos import cargar_modelos
from core.api_client import cliente_api

# Importamos nuestros nuevos routers desde la capa 'api'
from api import router_chat
from api import router_outfits
from api import router_prendas
#from api import router_posts

# =====================================================================
# CICLO DE VIDA (LIFESPAN)
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Arrancando servidor: Cargando modelos de IA en memoria RAM...")
    
    # 1. Cargamos todos los pesos de PyTorch y HuggingFace
    processor, model, remover, outfit_generator = cargar_modelos()
    
    # 2. Inyectamos los modelos en el estado de la app para que los routers puedan usarlos
    app.state.ml_models = {
        "processor": processor,
        "model": model,
        "remover": remover,
        "outfit_generator": outfit_generator
    }
    
    print("✅ Modelos cargados con éxito. API lista para recibir peticiones.")
    
    # El servidor se queda aquí "pausado" atendiendo peticiones...
    yield
    
    # =====================================================================
    # APAGADO DEL SERVIDOR (Limpieza)
    # =====================================================================
    print("🛑 Apagando servidor, limpiando recursos...")
    
    # Vaciamos la memoria RAM de los modelos
    app.state.ml_models.clear()
    
    # Cerramos de forma segura las conexiones asíncronas de la API externa
    await cliente_api.aclose()
    
    print("✅ Conexiones de red cerradas correctamente.")

# =====================================================================
# CONFIGURACIÓN DE FASTAPI
# =====================================================================
app = FastAPI(
    title="OutfitAI API - Core",
    description="Motor multimodal de IA para generación y recomendación de looks.",
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

# Ahora incluimos los routers que siguen la nueva nomenclatura limpia
app.include_router(router_prendas.router)
app.include_router(router_outfits.router)
app.include_router(router_chat.router)
#app.include_router(router_posts.router)