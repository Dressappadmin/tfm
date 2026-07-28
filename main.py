'''
ANTES DE COMENZAR
CTRL MAYUS P y seleccionar el interpreter de venv/bin/python
abrir la terminal y escribir: pip install -r requirements.txt
'''

# IMPORTS DE LIBRERÍAS EXTERNAS
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import math
import matplotlib.pyplot as plt
import io

# IMPORTAMOS LIBRERÍAS Y MÓDULOS INTERNOS
from config import *
from modulos.model_loader import cargar_modelos
from data.db_loader import catalog
from utils.remove_background import remove_background
from utils.get_embedding import get_embedding
from utils.identifier import reconocer_prenda
from utils.compatibles import slots_compatibles
from utils.scoring import detectar_color_prenda, selection
from utils.image_loader import load_image_from_url, get_public_url

# PIPELINE
def pipeline(processor, model, remover, img, catalog, top_n=5, temperatura=0.15):

    # PROCESAMOS IMAGEN
    image_clean = remove_background(img, remover)

    # EMBEDDING, TIPO, COLOR
    embedding = get_embedding(image_clean, processor, model)
    print(type(embedding))
    print(embedding)
    tipo_prenda = reconocer_prenda(image_clean, processor, model)[0][0]
    print(tipo_prenda)
    color = detectar_color_prenda(image_clean)
    print(color)

    print('tipo catalog, tipo catalog[0]', type(catalog), type(catalog[0]))
    print('tipo de embedding', type(embedding))

    # PRENDAS COMPATIBLES
    prendas_compatibles = slots_compatibles(tipo_prenda)
    print(prendas_compatibles)

    # BUSCAMOS EN LA BD SOLO PRENDAS COMPATIBLES
    matches = selection(prendas_compatibles, top_n, temperatura, color, embedding, catalog)
    print('tipo matches[0] y matches[0].keys()', type(matches[0]), matches[0].keys())

    return img, image_clean, tipo_prenda, color, matches

# VISUALIZAR EL RESULTADO
def visualizar(img_original, img_clean, prenda_detectada, color_detectado, matches):
    # VISUALIZACION
    cols = 3
    rows_grid = math.ceil((TOP_K + 2) / cols)

    fig = plt.figure(figsize=(15, 5 + rows_grid * 6))

    ax1 = fig.add_subplot(rows_grid + 1, cols, 1)
    ax1.imshow(img_original)
    ax1.axis('off')
    ax1.text(0.5, -0.02, '📸 Tu prenda', ha='center', va='top',
            fontsize=10, fontweight='bold', transform=ax1.transAxes)

    ax2 = fig.add_subplot(rows_grid + 1, cols, 2)
    ax2.imshow(img_clean)
    ax2.axis('off')
    ax2.text(0.5, -0.02, f"✂️ Sin fondo · {prenda_detectada} · {color_detectado['hex']}", ha='center', va='top',
            fontsize=10, fontweight='bold', color='green', transform=ax2.transAxes)

    for i, match in enumerate(matches):
        ax = fig.add_subplot(rows_grid + 1, cols, cols + i + 1)
        try:
            url   = get_public_url(match[COL_IMG_URL])
            img_m = load_image_from_url(url)
            ax.imshow(img_m)
        except Exception as e:
            ax.text(0.5, 0.5, f'Error\n{e}', ha='center', va='center',
                    fontsize=7, transform=ax.transAxes)

        name          = str(match.get(COL_NAME, '?'))[:35]
        price_display = f'{int(match.get(COL_PRICE, 0)) / 100:.2f}'
        family        = match.get(COL_FAMILY, '')
        color_hex     = match.get(COL_COLOR, '')
        avail         = '✅' if match.get(COL_AVAILABILITY) else '❌'

        ax.axis('off')
        ax.text(0.5, -0.02, name, ha='center', va='top',
                fontsize=9, fontweight='bold', transform=ax.transAxes)
        ax.text(0.5, -0.10, f'{family} · {color_hex} · {price_display} € {avail}', ha='center', va='top',
                fontsize=8, color='gray', transform=ax.transAxes)

    plt.suptitle(f'👗 OutfitAI — Outfit completo para tu {prenda_detectada} ({color_detectado["hex"]})',
                fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout()
    
    plt.savefig('resultado_outfit.png')
    print("¡Proceso terminado! Imagen guardada como resultado_outfit.png")

# API
# Inicializamos
app = FastAPI(
    title="OutfitAI API",
    description="Motor de recomendación y análisis visual de prendas",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se cambia por el dominio exacto de tu web
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear el Endpoint (La ruta donde el cliente enviará la petición)
@app.post("/analyze-outfit")
async def analyze_outfit_endpoint(file: UploadFile = File(...)):
    """
    Recibe una imagen desde el cliente, la procesa y devuelve las recomendaciones.
    """
    # Validar que el archivo subido sea realmente una imagen
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen válida.")

    try:
        # Leer los datos binarios de la imagen subida
        image_bytes = await file.read()
        
        # Convertirla a un objeto de PIL, que es lo que espera tu función remove_background
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')

        # Modelos
        processor, model, remover = cargar_modelos()
        
        print(f"DEBUG: Prendas en memoria justo antes de filtrar: {len(catalog)}")

        # Pipeline
        original, clean, prenda, color, matches = pipeline(processor, model, remover, img, catalog)

        # Visualizar
        # visualizar(original, clean, prenda, color, matches)

        # Devolver la respuesta empaquetada en JSON
        return {
            "status": "success",
            "resultados": {
                "prenda_detectada": prenda,
                "color": color,
                "recomendaciones": [m.get(COL_ID) for m in matches],
            }
        }

    except Exception as e:
        import traceback
        error_completo = traceback.format_exc()
        print(error_completo) # Lo guardamos también en el log de Cloud Run
        
        # Devolvemos el error completo a la URL para que lo veas al instante
        raise HTTPException(status_code=500, detail=error_completo)