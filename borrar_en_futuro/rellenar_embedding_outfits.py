import numpy as np
from utils.normalize_vector import normalize_vector
from data.db_loader import supabase
from config import OUTFITS, PRENDAS
from utils.get_embedding import get_embedding
from utils.load_image_from_url import load_image_from_url
from modulos.cargar_modelos import cargar_modelos

# AHORA MISMO SE CALCULA EL EMBEDDING DE TODOS LOS OUTFITS NO PROCESADOS
# EN EL FUTURO, AL CREAR UN OUTFIT, SE DEBERÁ LLAMAR A ESTA FUNCIÓN PARA UN OUTFIT CONCRETO

processor, model, remover = cargar_modelos() ## No hará falta cuando guardemos el embedding en la tabla

def calcular_y_actualizar_embeddings_pendientes(
    supabase: SBClient,
    batch_size: int = 50
) -> dict[str, int]:
    """
    Busca los outfits con revisado_ia=False, calcula su embedding promedio a partir
    de sus prendas en la tabla 'items' y actualiza la tabla 'outfits'.
    """
    stats = {"procesados": 0, "actualizados": 0, "errores": 0}
    
    # 1. Obtener outfits pendientes por lotes (para no saturar memoria)
    try:
        respuesta = (
            supabase.table(OUTFITS)
            .select("id, ids_prendas")
            .eq("revisado_ia", False)
            .limit(batch_size)
            .execute()
        )
        outfits_pendientes = respuesta.data or []
    except Exception as e:
        print(f"❌ Error al consultar outfits pendientes: {e}")
        return stats

    if not outfits_pendientes:
        print("✅ No hay outfits pendientes de procesar.")
        return stats

    print(f"🔍 Procesando lote de {len(outfits_pendientes)} outfits pendientes...")

    for outfit in outfits_pendientes:
        outfit_id = outfit["id"]
        ids_prendas = outfit.get("ids_prendas") or []
        stats["procesados"] += 1

        # Si el outfit está vacío por algún motivo, marcamos como revisado para no atascar el bucle
        if not ids_prendas:
            supabase.table(OUTFITS).update({"revisado_ia": True}).eq("id", outfit_id).execute()
            continue

        try:
            # 2. Consultar los embeddings de las prendas en la tabla 'items'
            res_items = (
                supabase.table(PRENDAS)
                .select("id, img_url")
                .in_("id", ids_prendas)
                .execute()
            )
            items_data = res_items.data or []

            # cálculo del embedding, en el futuro se sutituye por emb = item["embedding"] \n embeddings_validos.append(emb)
            embeddings_validos = []
            for item in items_data:
                url_img = item["img_url"]
                img = load_image_from_url(url_img)
                emb = get_embedding(img, processor, model)
                embeddings_validos.append(emb)
            
            if not embeddings_validos:
                print(f"⚠️ Outfit {outfit_id}: ninguna de sus prendas tiene embedding válido.")
                stats["errores"] += 1
                continue

            # 3. Calcular la media vectorial y normalizar
            matriz_embeddings = np.array(embeddings_validos, dtype=np.float32)
            embedding_outfit = normalize_vector(np.mean(matriz_embeddings, axis=0))

            # 4. Actualizar la base de datos (sustituir embedding y marcar revisado_ia = True)
            (
                supabase.table(OUTFITS)
                .update({
                    "embedding": embedding_outfit,
                    "revisado_ia": True
                })
                .eq("id", outfit_id)
                .execute()
            )
            stats["actualizados"] += 1

        except Exception as e:
            print(f"❌ Error procesando el outfit {outfit_id}: {e}")
            stats["errores"] += 1

    print(f"🏁 Lote finalizado -> Actualizados: {stats['actualizados']} | Errores: {stats['errores']}")
    return stats

print(calcular_y_actualizar_embeddings_pendientes(supabase))