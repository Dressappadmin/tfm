import httpx

# URL ENDPOINT ALLAN
URL_DE_LA_NUEVA_API = "https://dressapi.onrender.com/api/v1" 

# URL ARMARIO_USUARIOS
URL_ARMARIO_USUARIOS = 'https://xjsiuxyadnqxsuzjgvnj.supabase.co/storage/v1/object/public/armario_usuarios/'

# Cliente asíncrono
cliente_api = httpx.AsyncClient(base_url=URL_DE_LA_NUEVA_API)