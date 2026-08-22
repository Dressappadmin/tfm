import httpx

# Aquí pones la URL que te hayan dado. Lo ideal es leerla del .env
URL_DE_LA_NUEVA_API = "https://api-datos.tuempresa.com" 

# Este cliente es el "teléfono" asíncrono
cliente_api = httpx.AsyncClient(base_url=URL_DE_LA_NUEVA_API)