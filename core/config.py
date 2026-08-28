# core/config.py
import os
from dotenv import load_dotenv
from supabase import create_async_client, AsyncClient

# Cargar variables de entorno
load_dotenv()

# ==========================================
# LLM & APIS
# ==========================================
LLM_API_KEY = os.getenv("LLM_API_KEY")

# ==========================================
# CREDENCIALES Y BD (SUPABASE O API EXTERNA)
# ==========================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("⚠️ Faltan las credenciales de Supabase en las variables de entorno.")

supabase_client: AsyncClient = create_async_client(SUPABASE_URL, SUPABASE_KEY)

# Tablas y buckets
OUTFITS_TABLA = 'outfit'
PRENDAS_TABLA = 'prenda'
USUARIOS_TABLA = ''
POSTS_TABLA = 'posts_lucia'
PRENDAS_BUCKET = 'armario_usuarios'
FOTOS_REALES_BUCKET = 'armario_usuarios'

# ==========================================
# NOMBRES DE COLUMNAS PRENDAS
# ==========================================
ID_PRENDA               = 'id' 
COLOR_PRENDA            = 'color'
EMBEDDING_PRENDA        = 'embedding'
TIPO_PRENDA             = 'categoria' 
SLOT_PRENDA             = 'slot' 
OCASION_PRENDA          = 'ocasion' 
TEMPORADA_PRENDA        = 'temporada' 
INSPIRACION_PRENDA      = 'inspiracion' 

# ==========================================
# NOMBRES DE COLUMNAS OUTFITS
# ==========================================
ID_OUTFIT               = 'id_outfit' 
EMBEDDING_OUTFIT        = 'embedding'
IDS_PRENDAS_OUTFIT      = 'ids_prendas'

# ==========================================
# NOMBRES DE COLUMNAS USUARIOS
# ==========================================
ID_USUARIO              = '' 

# ==========================================
# NOMBRES DE COLUMNAS POSTS
# ==========================================
ID_POST              = 'id' 


# ==========================================
# CONSTANTES GLOBALES DEL SISTEMA
# ==========================================
TOP_K = 5