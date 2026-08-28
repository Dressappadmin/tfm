import pandas as pd
import numpy as np

# 1. Cargar el dataset original
# Asegurarnos de que el article_id se lee como string para no perder los ceros a la izquierda
df = pd.read_csv('articles.csv', dtype={'article_id': str})

# 2. Crear el nuevo DataFrame con tu estructura
df_nuevo = pd.DataFrame()

# id: Mantenemos el article_id (en Kaggle suelen ser de 10 dígitos, ej: 0108775015)
df_nuevo['id'] = df['article_id']

# name: Usamos prod_name y lo pasamos a mayúsculas para igualar tu formato
df_nuevo['name'] = df['prod_name'].str.upper()

# price: Como no viene en este CSV, le asignamos un precio base temporal (ej: 19.99)
df_nuevo['price'] = 19.99

# section (WOMAN/MAN): Mapeamos la columna index_group_name de H&M a tus secciones
def mapear_seccion(index_group):
    grupo = str(index_group).upper()
    if 'LADIES' in grupo:
        return 'WOMAN'
    elif 'MENS' in grupo:
        return 'MAN'
    elif 'BABY' in grupo or 'CHILDREN' in grupo:
        return 'KIDS'
    else:
        return 'OTHER'

df_nuevo['section'] = df['index_group_name'].apply(mapear_seccion)

# family: Usamos product_type_name en mayúsculas (ej: VEST TOP -> CAZADORA, CAMISETA...)
df_nuevo['family'] = df['product_type_name'].str.upper()

# img_url: Construimos la ruta apuntando a tu bucket
# Sustituye 'TU_URL_BASE' por la url pública de tu bucket 
# (ej: 'https://xxx.supabase.co/storage/v1/object/public/ropa/')
url_base_bucket = "https://tu-bucket.com/ruta/a/imagenes/"

# Nota: El dataset de H&M suele organizar las fotos en subcarpetas con los 3 primeros dígitos del ID
# ej: 010/0108775015.jpg. Si las tienes todas sueltas en la misma carpeta del bucket, usa la opción 1.

# Opción 1 (Todas las fotos en la misma carpeta):
df_nuevo['img_url'] = url_base_bucket + df_nuevo['id'] + ".jpg"

# Opción 2 (Si mantuviste la estructura de carpetas original de Kaggle):
# df_nuevo['img_url'] = url_base_bucket + df_nuevo['id'].str[:3] + "/" + df_nuevo['id'] + ".jpg"

# availability: Asumimos que están en stock para las pruebas
df_nuevo['availability'] = True

# 3. Guardar el resultado
df_nuevo.to_csv('dataset_adaptado.csv', index=False)
print("CSV transformado y guardado con éxito.")