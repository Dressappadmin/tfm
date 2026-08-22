from typing import Any
import httpx

from core.api_client import cliente_api
from core.config import OUTFITS_TABLA

async def registrar_outfit_bd(
    ids_prendas: list[int | str],
    user_id: str | None = None,
    nombre: str | None = None
) -> int | str | None:
    """
    Registra un nuevo outfit mediante una llamada a la API externa de datos.

    Parameters
    ----------
    ids_prendas : list[int | str]
        Lista de IDs de las prendas que componen el outfit (ej. [102, 450, 891]).
    user_id : str | None, opcional
        ID del usuario (UUID o texto) propietario del conjunto, por defecto None.
    nombre : str | None, opcional
        Nombre asignado al outfit (ej. "Casual de Verano"), por defecto None.

    Returns
    -------
    int | str | None
        El ID del registro insertado (puede ser entero o UUID string) si fue exitoso, o None si falló.
    """
    if not ids_prendas:
        print("⚠️ Advertencia: No se puede registrar un outfit sin prendas.")
        return None

    try:
        # 1. Construir el objeto/payload a insertar
        datos_outfit: dict[str, Any] = {
            "items_ids": ids_prendas,
        }

        if user_id is not None:
            datos_outfit["user_id"] = user_id
            
        if nombre is not None:
            datos_outfit["nombre"] = nombre

        # 2. Definimos la URL (Endpoint).
        # En las APIs REST estándar, para crear un recurso se hace un POST a la raíz de la entidad
        url_endpoint = f"/{OUTFITS_TABLA}"

        # 3. Ejecutar la inserción mediante POST
        respuesta = await cliente_api.post(url_endpoint, json=datos_outfit)
        
        # Validar si hubo algún error HTTP (400 Bad Request, 500 Server Error)
        respuesta.raise_for_status()

        # 4. Extraer el ID generado de la respuesta JSON
        # Supabase devolvía siempre una lista en respuesta.data, pero las APIs REST 
        # a menudo devuelven directamente un único diccionario al hacer POST.
        outfit_creado = respuesta.json()
        
        # Manejamos ambos casos (por si la API imita la estructura de Supabase o no)
        if isinstance(outfit_creado, list) and len(outfit_creado) > 0:
            outfit_id = outfit_creado[0].get('id')
        elif isinstance(outfit_creado, dict):
            outfit_id = outfit_creado.get('id')
        else:
            outfit_id = None

        if outfit_id:
            print(f"✅ Outfit registrado con éxito (ID generado: {outfit_id})")
            return outfit_id
        
        print("⚠️ La API no devolvió un ID válido tras la inserción.")
        return None

    except httpx.HTTPError as error:
        print(f"❌ Error de red o en la API al registrar el outfit: {error}")
        return None
    except Exception as error:
        print(f"❌ Error inesperado: {error}")
        return None