from supabase import create_client, Client as SBClient
from config import SUPABASE_KEY, SUPABASE_URL, SUPABASE_TABLE

supabase: SBClient = create_client(SUPABASE_URL, SUPABASE_KEY)

test = supabase.table(SUPABASE_TABLE).select('*').limit(2).execute()
print(f'Supabase OK — {len(test.data)} filas de prueba')
print(f'Columnas: {list(test.data[0].keys())}')

catalog = supabase.table(SUPABASE_TABLE).select('*').execute().data
print(f'Catálogo cargado: {len(catalog)} prendas en memoria')

print(supabase.table(SUPABASE_TABLE).select('*').limit(5).execute())