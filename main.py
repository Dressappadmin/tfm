from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos la lógica de inicialización y nuestro cliente HTTP
from core.cargar_modelos import cargar_modelos
from core.config import render_client

# Importamos nuestros nuevos routers desde la capa 'api'
from api import router_chat
from api import router_outfits
from api import router_prendas
from api import router_posts

# =====================================================================
# CICLO DE VIDA (LIFESPAN)
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Gestiona el ciclo de vida de la aplicación FastAPI, encargándose de la inicialización y limpieza de recursos. Durante el arranque, carga los modelos de Inteligencia Artificial en memoria y los asigna al estado global; durante el apagado, libera la memoria y cierra las conexiones de red asíncronas de forma segura.

    Parameters
    ----------
    app : FastAPI
        Instancia principal de la aplicación FastAPI cuyo ciclo de vida y estado global se están configurando.

    Returns
    ----------
    None
    '''
    
    print("Arrancando servidor: Cargando modelos de IA en memoria RAM...")

    processor, model, remover, outfit_generator = cargar_modelos()
    
    app.state.ml_models = {
        "processor": processor,
        "model": model,
        "remover": remover,
        "outfit_generator": outfit_generator
    }
    
    print("Modelos cargados con éxito. API lista para recibir peticiones.")
    
    yield
    
    # =====================================================================
    # APAGADO DEL SERVIDOR (Limpieza)
    # =====================================================================
    print("Apagando servidor, limpiando recursos...")
    
    app.state.ml_models.clear()

    await render_client.aclose()
    
    print("Conexiones de red cerradas correctamente.")

# =====================================================================
# CONFIGURACIÓN DE FASTAPI
# =====================================================================
app = FastAPI(
    title="DressApi - GoogleCloud",
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

app.include_router(router_prendas.router)
app.include_router(router_outfits.router)
app.include_router(router_chat.router)
app.include_router(router_posts.router)