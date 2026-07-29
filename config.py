import os
import torch
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ==========================================
# CREDENCIALES Y BD
# ==========================================
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE  = 'zara_imgs_wback'
SUPABASE_BUCKET = 'Pruebas'

# ==========================================
# NOMBRES DE COLUMNAS (Mapeo de BD)
# ==========================================
COL_ID           = 'id'
COL_NAME         = 'name'
COL_PRICE        = 'price'
COL_SECTION      = 'section'
COL_FAMILY       = 'family'
COL_IMG_URL      = 'img_url'
COL_AVAILABILITY = 'availability'
COL_COLOR        = 'main_color_hex'

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
    'CALZADO':         ['bambas', 'bota plana', 'bota tacon', 'botin plano', 'botin tacon'],
    'ACCESORIO':       ['bisuteria', 'bolso', 'cinturon', 'pañuelo'],
}

TOP_K = 5