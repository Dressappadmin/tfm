import os
import torch
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

# Device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ==========================================
# LLM
# ==========================================
LLM_API_KEY = os.getenv("LLM_API_KEY")

# ==========================================
# CREDENCIALES Y BD
# ==========================================
# Credenciales
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")

# Tablas y buckets
OUTFITS_TABLA = 'outfit'
PRENDAS_TABLA = 'prenda'
PRENDAS_BUCKET = 'armario_usuarios'

# ==========================================
# NOMBRES DE COLUMNAS PRENDAS
# ==========================================
ID_PRENDA               = 'id' # PK
IMG_URL_PRENDA          = '' # url del bucket
COLOR_PRENDA            = 'color'
EMBEDDING_PRENDA        = 'embedding'
TIPO_PRENDA             = 'categoria' # ya normalizado, pertenece a CATEGORIAS, más abajo
SLOT_PRENDA             = 'slot' # ya normalizado, debe pertenecer a SLOTS, más abajo
OCASION_PRENDA          = 'ocasion' # fiesta, oficina,...
TEMPORADA_PRENDA        = 'temporada' # primavera, verano, otoño, invierno
INSPIRACION_PRENDA      = 'inspiracion' # etiquetas libres: harry styles, flores, ...

# ==========================================
# NOMBRES DE COLUMNAS OUTFITS
# ==========================================
ID_OUTFIT               = 'id_outfit' # PK
EMBEDDING_OUTFIT        = 'embedding'
IDS_PRENDAS_OUTFIT      = 'ids_prendas'


# ==========================================
# REGLAS DE NEGOCIO Y LÓGICA DE MODA
# ==========================================
PESOS_COMPATIBILIDAD = {'color': 0.6, 'estilo': 0.4}

CATEGORIAS = [
    'abrigo', 'anorak', 'bambas', 'bañador', 'bermuda', 'bisuteria',
    'blazer', 'body', 'bolso', 'bota plana', 'bota tacon', 'botin plano',
    'botin tacon', 'camisa', 'camiseta', 'cazadora', 'chaleco', 'chaqueta',
    'cinturon', 'falda', 'gabardina', 'impermeable', 'jersey', 'leggings',
    'mono', 'pantalon', 'pañuelo', 'peto', 'running', 'sandalia plana',
    'sandalia tacon', 'short', 'sudadera', 'top', 'vestido',
    'zapato plano', 'zapato tacon'
]

SLOTS = { 
    'SUPERIOR':        ['camiseta', 'camisa', 'top', 'jersey', 'sudadera', 'body', 'chaleco'],
    'INFERIOR':        ['pantalon', 'falda', 'short', 'bermuda', 'leggings'],
    'CUERPO_COMPLETO': ['vestido', 'mono', 'peto', 'bañador'],
    'ABRIGO':          ['abrigo', 'anorak', 'chaqueta', 'cazadora', 'gabardina', 'impermeable', 'blazer'],
    'CALZADO':         ['bambas', 'bota plana', 'bota tacon', 'botin plano', 'botin tacon', 'zapato tacon'],
    'ACCESORIO':       ['bisuteria', 'bolso', 'cinturon', 'pañuelo', 'sombrero'],
}

# Mapeo fijo para asegurar que el orden del multi-hot vector sea siempre el mismo
# para el modelo avanzado
SLOT_INDEX = {
    'SUPERIOR': 0, 
    'INFERIOR': 1, 
    'CUERPO_COMPLETO': 2, 
    'ABRIGO': 3, 
    'CALZADO': 4, 
    'ACCESORIO': 5
}

TOP_K = 5
