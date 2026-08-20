from supabase import create_client, Client

# Importamos las constantes limpias de config.py
from config import SUPABASE_URL, SUPABASE_KEY

# 1. Creamos el cliente centralizado aquí (en minúsculas, como estándar)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)