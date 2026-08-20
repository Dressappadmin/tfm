import numpy as np
from fastapi import APIRouter, HTTPException, Body

# Importamos tu cliente de base de datos y utilidades
from data.supabase import supabase
from config import PRENDAS_TABLA, ID_PRENDA, TIPO_PRENDA, SLOT_PRENDA

# Asumo que tienes una función de validación ya creada (ajusta la importación a tu ruta real)
from modulos.validar_reglas_outfit import validar_reglas_outfit 
from schemas.ValidarOutfitRequest import ValidarOutfitRequest

router = APIRouter(
    prefix="/outfits", 
    tags=["Gestión de Outfits"]
)

# Definimos el esquema de lo que va a recibir el endpoint


# ---------------------------------------------------------
# ENDPOINT 1: VALIDAR COMBINACIÓN DE PRENDAS
# ---------------------------------------------------------
@router.post("/validar_outfit") # Cambiamos a POST para recibir el JSON en el body
async def validar_outfit(request: ValidarOutfitRequest):
    """
    Dada una lista de IDs de prendas, extrae sus tipos (family) 
    y comprueba si forman un conjunto válido.
    """
    try:
        prendas_ids = request.prendas_ids

        # 1. Validación básica
        if not prendas_ids or len(prendas_ids) == 0:
            raise HTTPException(status_code=400, detail="La lista de prendas está vacía.")

        # 2. Recuperar el tipo (family) de cada prenda directamente
        # Usamos el operador 'in' para traer todas las prendas de una sola consulta
        resp_prendas = supabase.table(PRENDAS_TABLA).select(ID_PRENDA, SLOT_PRENDA).in_(ID_PRENDA, prendas_ids).execute()
        
        if not resp_prendas.data:
            raise HTTPException(status_code=404, detail="No se encontraron las prendas en la BD.")

        # Extraemos la lista de categorías detectadas
        slots_prendas = [prenda[SLOT_PRENDA] for prenda in resp_prendas.data if prenda.get(SLOT_PRENDA)]

        # 3. Validar utilizando tu lógica ya creada
        es_valido = validar_reglas_outfit(slots_prendas)
        mensaje = "Outfit válido" if es_valido else "Faltan prendas básicas (Top/Bottom o Vestido)."

        # -------------------------------------------------------------------------

        if not es_valido:
            return {"status": "invalid", "mensaje": mensaje, "categorias": slots_prendas}

        return {
            "status": "success",
            "mensaje": "El outfit cumple con las reglas de moda.",
            "categorias": slots_prendas
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=traceback.format_exc())