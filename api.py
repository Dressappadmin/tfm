from typing import Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from PIL import Image
import io
import base64

# IMPORTAMOS LIBRERÍAS Y MÓDULOS INTERNOS
from config import *
from modulos.cargar_bd import catalog, supabase
from modulos.cargar_modelos import cargar_modelos
from modulos.procesar_imagen import procesar_imagen
from modulos.completar_outfit import completar_outfit

# INTRODUCIMOS LOS MÓDULOS DEL FLUJO SOLICITADO
from modulos.buscar_prendas_similares import buscar_prendas_similares
from modulos.cargar_imagen_url_bucket import cargar_imagen_url_bucket
from modulos.subir_imagen_bucket import subir_imagen_bucket
from modulos.registrar_prenda_bd import registrar_prenda_bd
from modulos.registrar_outfit_bd import registrar_outfit_bd

# =====================================================================
# [PRUEBAS] MÓDULOS PARA EL BORRADO TEMPORAL (LUEGO LO QUITARÁS)
# =====================================================================
from modulos.eliminar_imagen_bucket import eliminar_imagen_bucket
from modulos.eliminar_prenda_bd import eliminar_prenda_bd

# =====================================================================
# ESQUEMAS PYDANTIC PARA RECIBIR RESPUESTAS DEL USUARIO EN LA API
# =====================================================================

class Paso2Request(BaseModel):
    # Imagen procesada en Base64 o token temporal
    url_imagen: str
    tipo_prenda: str
    color: str | list[str]
    embedding: list[float]
    
    # Paso 3 (Pregunta: ¿Es tu imagen alguna de estas?)
    es_prenda_existente: bool = Field(description="True si el usuario eligió alguna del top 3")
    id_prenda_seleccionada: int | str | None = None
    metadata: dict[str, Any] | list[Any] = Field(
        default_factory=list,
        description="Metadata de la fila seleccionada, o [] si no existía"
    )

    top_n: int = 5
    temperatura: float = 0.15
    
    # [PRUEBAS] Campo temporal para decidir si borrar la imagen al terminar el paso 2
    borrar_prenda_tras_prueba: bool = Field(
        default=False, 
        description="SOLO PRUEBAS: Si es True, borra del bucket y BD al terminar"
    )


class Paso3Request(BaseModel):
    ids_outfit: list[int | str] = Field(description="Lista de IDs del outfit que el usuario quiere guardar")
    usuario_id: str | None = None


# =====================================================================
# FUNCIÓN AUXILIAR: TOP 3 SIMILARES
# =====================================================================
def top_similares(embedding: list[float], catalogo: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Devuelve las 3 prendas más similares del catálogo con sus metadatos y URL."""
    resultados = buscar_prendas_similares(
        embedding,
        catalogo
    )
    return resultados


# =====================================================================
# CICLO DE VIDA Y CONFIGURACIÓN DE FASTAPI
# =====================================================================
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Arrancando servidor: Cargando modelos en memoria RAM...")
    processor, model, remover = cargar_modelos()
    
    ml_models["processor"] = processor
    ml_models["model"] = model
    ml_models["remover"] = remover
    print("Modelos cargados. API lista para recibir peticiones.")
    
    yield
    
    ml_models.clear()


app = FastAPI(
    title="OutfitAI API - Flujo Guiado",
    description="Motor visual para análisis, deduplicación y generación de outfits",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# PASO 1 y 2: PROCESAR FOTO + BUSCAR TOP 3 SIMILARES
# =====================================================================
@app.post("/paso1-analizar-prenda")
async def paso1_analizar_prenda(file: UploadFile = File(...)):
    """
    1. El usuario sube una foto.
    2. La procesamos: eliminamos fondo, sacamos color, embedding y tipo de prenda.
    3. Buscamos id1, id2, id3 = top_similares(embedding) y devolvemos sus imágenes para preguntar.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen válida.")

    try:
        image_bytes = await file.read()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((1024, 1024))

        processor = ml_models["processor"]
        model = ml_models["model"]
        remover = ml_models["remover"]

        # PASO 2: Procesamiento de IA
        embedding, tipo_prenda, color = procesar_imagen(img, processor, model, remover)

        # PASO 3: Top 3 Similares
        similares = top_similares(embedding, catalog)
        
        # Subimos la imagen al bucket
        try:
            # 1. Subida al storage de Supabase (pasándole la imagen y el cliente)
            url = subir_imagen_bucket(
                imagen=img,
                supabase=supabase,  # O como se llame tu variable del cliente de Supabase en config.py (ej: supabase_client)
                usuario_id=None,
                bucket_name="fotos_usuarios"
            )
            if not url:
                raise ValueError("subir_imagen_bucket devolvió una URL vacía.")

            # 2. Subida relacional a la base de datos con TODOS los argumentos que pide tu función
            exito_bd = registrar_prenda_bd(
                supabase=supabase,        # Cliente de Supabase
                imagen=img,               # Imagen PIL de la prenda
                nombre=tipo_prenda,     # Nombre por defecto para pruebas
                precio=0,                 # Precio por defecto
                marca="Desconocida",      # Marca por defecto
                año_venta=2026,           # Año actual
                temporada="AtemporaL",    # Temporada por defecto
                seccion="OTHERS",         # Seccion ("WOMAN", "MAN", "OTHERS")
                family=tipo_prenda,       # Asignamos el tipo detectado a la familia
                processor=processor,      # Modelo procesador cargado en ml_models
                model=model,              # Modelo IA cargado en ml_models
                ocasion=[],               # Opcional
                estilo_estetico=[],       # Opcional
                bucket_name="fotos_usuarios",
                usuario_id=None
            )

            # Como devuelve un dict[str, Any], verificamos que contenga datos
            if not exito_bd or not isinstance(exito_bd, dict):
                raise ValueError("registrar_prenda_bd no pudo completar el registro en la tabla.")

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Fallo en el proceso de guardado (ninguna o solo una operación tuvo éxito): {str(e)}"
            )

        return {
            "status": "success",
            "datos_prenda": {
                "tipo_prenda": tipo_prenda,
                "color": color['hex'],
                "embedding": embedding.tolist() if hasattr(embedding, "tolist") else embedding,
                "url_imagen": url
            },
            "top_3_similares": [
                {
                    "id": s.get("id"),
                    "name": s.get("name")
                }
                for s in similares
            ],
            "pregunta_usuario": "¿Es tu imagen alguna de estas? (Selecciona una o indica 'no')"
        }

    except Exception as e:
        import traceback
        error_completo = traceback.format_exc()
        print(error_completo)
        raise HTTPException(status_code=500, detail=error_completo)


# =====================================================================
# PASO 3, 4 y 5: CONFIRMAR PRENDA -> SUBIR A BD -> GENERAR OUTFIT
# =====================================================================
@app.post("/paso2-generar-outfit")
async def paso2_generar_outfit(datos: Paso2Request = Body(...)):
    """
    4. Evaluamos '¿Es tu imagen alguna de estas?':
       - sí -> metadata = el de esa fila
       - no -> metadata = []
    5. generar_outfit(imagen)
    """
    try:
        # PASO 3: Asignar metadata según la respuesta del usuario
        if datos.es_prenda_existente and datos.id_prenda_seleccionada:
            metadata = datos.metadata  # El diccionario con los datos de esa fila
        else:
            metadata = []

        # CORRECCIÓN: usamos datos.url_imagen en lugar de una variable 'url' indefinida
        imagen_actual = cargar_imagen_url_bucket(datos.url_imagen)

        # PASO 5: generar_outfit(imagen)
        # Llamamos al motor de recomendación híbrido para completar el conjunto
        outfit_generado = completar_outfit(
            datos.tipo_prenda,
            datos.top_n,
            datos.temperatura,
            datos.color,
            datos.embedding,
            catalog
        )

        ids_outfit = [m.get("id") for m in outfit_generado]

        # [PRUEBAS] Borramos temporalmente si el flag está activo en el Request
        if datos.borrar_prenda_tras_prueba:
            print("[PRUEBAS] Eliminando prenda automáticamente del bucket y base de datos...")
            eliminar_imagen_bucket(datos.url_imagen)
            eliminar_prenda_bd(datos.url_imagen)

        return {
            "status": "success",
            "outfit": outfit_generado,
            "ids_outfit": ids_outfit,
            "pregunta_usuario": "¿Quieres guardar este outfit?"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_completo = traceback.format_exc()
        print(error_completo)
        raise HTTPException(status_code=500, detail=error_completo)


# =====================================================================
# PASO 6: GUARDADO FIN DEL OUTFIT EN BD
# =====================================================================
@app.post("/paso3-guardar-outfit")
async def paso3_guardar_outfit(datos: Paso3Request = Body(...)):
    """
    6. ¿Quieres guardar este outfit?
       - no -> Fin (la app no llama a este endpoint).
       - sí -> guardar_outfit([ids]). Fin.
    """
    try:
        exito = registrar_outfit_bd(datos.ids_outfit, usuario_id=datos.usuario_id)
        if not exito:
            raise HTTPException(status_code=500, detail="No se pudo guardar el outfit en la base de datos.")
            
        return {
            "status": "success",
            "mensaje": "Outfit guardado correctamente. Fin del proceso."
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_completo = traceback.format_exc()
        print(error_completo)
        raise HTTPException(status_code=500, detail=error_completo)


# =====================================================================
# [PRUEBAS] ENDPOINT DEDICADO PARA BORRAR PRENDAS (LUEGO LO QUITARÁS)
# =====================================================================
@app.delete("/test-eliminar-prenda")
async def test_eliminar_prenda(url_imagen: str = Body(..., embed=True)):
    """
    ENDPOINT SOLO PARA PRUEBAS:
    Elimina una imagen creada en el paso 1 tanto del Storage Bucket como de la BD.
    """
    try:
        exito_bucket = eliminar_imagen_bucket(url_imagen)
        exito_bd = eliminar_prenda_bd(url_imagen)
        
        if not exito_bucket or not exito_bd:
            raise HTTPException(
                status_code=500, 
                detail="Ocurrió un error al intentar eliminar la imagen del bucket o la BD."
            )
            
        return {
            "status": "success",
            "mensaje": f"La imagen con URL '{url_imagen}' ha sido borrada con éxito de BD y Bucket."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))