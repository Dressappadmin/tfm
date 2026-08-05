from supabase import create_client, Client as SBClient
from config import SUPABASE_KEY, SUPABASE_URL, PRENDAS_TABLA, OUTFITS_TABLA

supabase: SBClient = create_client(SUPABASE_URL, SUPABASE_KEY)

test = supabase.table(PRENDAS_TABLA).select('*').limit(2).execute()
print(f'Supabase OK — {len(test.data)} filas de prueba')
print(f'Columnas: {list(test.data[0].keys())}')

catalog = supabase.table(PRENDAS_TABLA).select('*').execute().data

outfits = supabase.table(OUTFITS_TABLA).select('*').execute().data