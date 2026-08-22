# core/config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==========================================
# LLM & APIS
# ==========================================
LLM_API_KEY = os.getenv("LLM_API_KEY")

# ==========================================
# CREDENCIALES Y BD (SUPABASE O API EXTERNA)
# ==========================================
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")

# Tablas y buckets
OUTFITS_TABLA = 'outfit'
PRENDAS_TABLA = 'prenda'
USUARIOS_TABLA = ''
PRENDAS_BUCKET = 'armario_usuarios'

# ==========================================
# NOMBRES DE COLUMNAS PRENDAS
# ==========================================
ID_PRENDA               = 'id' 
IMG_URL_PRENDA          = '' 
COLOR_PRENDA            = 'color'
EMBEDDING_PRENDA        = 'embedding'
TIPO_PRENDA             = 'categoria' 
SLOT_PRENDA             = 'slot' 
OCASION_PRENDA          = 'ocasion' 
TEMPORADA_PRENDA        = 'temporada' 
INSPIRACION_PRENDA      = 'inspiracion' 

# ==========================================
# NOMBRES DE COLUMNAS OUTFITS & USUARIOS
# ==========================================
ID_OUTFIT               = 'id_outfit' 
EMBEDDING_OUTFIT        = 'embedding'
IDS_PRENDAS_OUTFIT      = 'ids_prendas'

ID_USUARIO              = '' 
EMBEDDING_USUARIO       = ''

# ==========================================
# CONSTANTES GLOBALES DEL SISTEMA
# ==========================================
TOP_K = 5