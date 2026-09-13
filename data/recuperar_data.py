import os
import pandas as pd
import requests
import concurrent.futures
from supabase import create_client

SUPABASE_URL = "https://tyoqkvnleusdsdwimjbj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR5b3Frdm5sZXVzZHNkd2ltamJqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDgxNjkyMywiZXhwIjoyMTAwMzkyOTIzfQ.nHuDXt5RXjzIUm_NBVrk1fgV4BnYsUK0wChUV7DgGks"
BASE_DIR = "./dataset_entrenamiento"

# Mapeo por defecto (aunque el script ahora es a prueba de fallos y leerá la URL)
BUCKETS = {
    'zara': 'zara_imgs_wback',
    'hym': 'hym_productos',
    'mango': 'mango_productos',
    'bershka': 'bershka_productos'
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Crear la estructura de carpetas
carpetas = ["defectuosas", "usadas", "sin_usar"]
for c in carpetas:
    os.makedirs(os.path.join(BASE_DIR, c), exist_ok=True)

# 2. Cargar los tres CSVs
print("Leyendo y cruzando los CSVs...")
df_datos = pd.read_csv('vista_ropa_unificada_rows.csv')
df_defectuosos = pd.read_csv('defectuosos_rows.csv')
df_sinteticos = pd.read_csv('datos_sinteticos_rows.csv')

# 3. Preparar los conjuntos de IDs (Sets para velocidad)
set_defectuosos = set(df_defectuosos['prenda_id'].dropna().astype(str).str.strip())

set_usadas = set()
for valor in df_sinteticos['prendas_ids'].dropna():
    limpio = str(valor).replace('[', '').replace(']', '').replace("'", "").replace('"', '')
    ids_extraidos = [x.strip() for x in limpio.split(',') if x.strip()]
    set_usadas.update(ids_extraidos)

total = len(df_datos)
print(f"Total imágenes a procesar: {total}")
print(f"- Defectuosas detectadas: {len(set_defectuosos)}")
print(f"- Usadas detectadas: {len(set_usadas)}\n")

def descargar_imagen(row):
    img_id = str(row['id']).strip()
    url = str(row['img_url'])
    marca = str(row['marca']).lower().strip()
    
    # Averiguar a qué carpeta local va
    if img_id in set_defectuosos:
        subcarpeta = "defectuosas"
    elif img_id in set_usadas:
        subcarpeta = "usadas"
    else:
        subcarpeta = "sin_usar"
        
    ruta_local = os.path.join(BASE_DIR, subcarpeta, f"{img_id}.jpg")
    
    # Si ya existe y pesa algo, la saltamos (para poder reanudar sin problemas)
    if os.path.exists(ruta_local) and os.path.getsize(ruta_local) > 0:
        return True

    try:
        # Si es Zara web
        if 'zara' in marca and url.startswith('http') and 'supabase.co' not in url:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            datos_imagen = res.content
        else:
            # Magia pura: extraemos el bucket real directamente de la URL
            # Así nos da igual si nos hemos equivocado en el diccionario BUCKETS
            if '/public/' in url:
                # De https://.../public/bershka/123.jpg saca "bershka"
                bucket_real = url.split('/public/')[-1].split('/')[0]
            else:
                # Fallback por si acaso la URL es un texto raro
                bucket_real = next((v for k, v in BUCKETS.items() if k in marca), "default")
                
            nombre_archivo = url.split('/')[-1]
            descarga_url = f"{SUPABASE_URL}/storage/v1/object/authenticated/{bucket_real}/{nombre_archivo}"
            
            headers_supa = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            
            res = requests.get(descarga_url, headers=headers_supa, timeout=15)
            
            if res.status_code == 404:
                print(f"⚠️ Imagen no encontrada (404): ID {img_id}")
                return False
                
            res.raise_for_status() 
            datos_imagen = res.content
            
        with open(ruta_local, "wb") as f:
            f.write(datos_imagen)
        return True
    
    except Exception as e:
        print(f"❌ Error HTTP con ID {img_id} (Marca: {marca}): {e}")
        return False

if __name__ == "__main__":
    descargados = 0
    filas = df_datos.to_dict('records')
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        resultados = executor.map(descargar_imagen, filas)
        
        for i, completado in enumerate(resultados):
            if completado:
                descargados += 1
            if i > 0 and i % 200 == 0:
                print(f"Progreso: {i} / {total} procesadas...")
                
    print(f"\n🎉 ¡RESCATE Y CLASIFICACIÓN COMPLETADOS!")