from typing import Any
from modulos.cargar_bd import outfits

def registrar_outfit_bd(
    ids_prendas: list[int | str],
    user_id: str | None = None,
    nombre: str | None = None
) -> dict[str, Any] | None:
    """
    Registra un nuevo outfit en la tabla 'outfits' de la base de datos de Supabase.

    Parameters
    ----------
    supabase : Client
        Cliente inicializado de Supabase.
    ids_prendas : list[int | str]
        Lista de IDs de las prendas que componen el outfit (ej. [102, 450, 891]).
    user_id : str | None, opcional
        ID del usuario (UUID o texto) propietario del conjunto, por defecto None.
    nombre : str | None, opcional
        Nombre asignado al outfit (ej. "Casual de Verano"), por defecto None.

    Returns
    -------
    dict[str, Any] | None
        Diccionario con el registro insertado si fue exitoso, o None si falló.
    """
    if not ids_prendas:
        print("⚠️ Advertencia: No se puede registrar un outfit sin prendas.")
        return None

    try:
        # 1. Construir el objeto/payload a insertar
        # NOTA: Ajusta las claves según el nombre exacto de tus columnas en Supabase
        datos_outfit: dict[str, Any] = {
            "items_ids": ids_prendas,  # Columna de tipo array (int8[] o text[]) o jsonb
        }

        # Añadir campos opcionales si vienen informados
        if user_id is not None:
            datos_outfit["user_id"] = user_id
            
        if nombre is not None:
            datos_outfit["nombre"] = nombre

        # 2. Ejecutar la inserción en Supabase
        respuesta = outfits.insert(datos_outfit).execute()

        # 3. Validar el resultado
        if respuesta.data and len(respuesta.data) > 0:
            outfit_creado = respuesta.data[0]
            print(f"✅ Outfit registrado con éxito (ID generado: {outfit_creado.get('id')})")
            return outfit_creado

        print("⚠️ La base de datos no devolvió datos tras la inserción.")
        return None

    except Exception as error:
        print(f"❌ Error al registrar el outfit en Supabase: {error}")
        return None