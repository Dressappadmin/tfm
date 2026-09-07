import os
from supabase import create_client, Client
from .defectuosos import ids_a_borrar

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Ajusta los nombres exactos que tienen tus tablas originales en Supabase
# (Si tu tabla de Zara es 'zara_imgs_wback', cámbialo aquí)
MAPA_TABLAS = {
    'zara': 'zara_imgs_wback', 
    'mango': 'mango_productos',
    'bershka': 'bershka_productos',
    'hym': 'hym_productos'
}

# Ajusta los nombres exactos de tus buckets
MAPA_BUCKETS = {
    'bershka': 'bershka',
    'mango': 'mango',
    'hym': 'hym'
}

# Pon aquí la lista de IDs que quieres exterminar


# ==========================================
# 2. LÓGICA DE BORRADO
# ==========================================
def purgar_ids(ids: list):
    for item_id in ids:
        print(f"\n--- Procesando ID: {item_id} ---")
        
        # A) Obtener información de la prenda desde la vista unificada
        res_vista = supabase.table("vista_ropa_unificada").select("marca, img_url").eq("id", item_id).execute()
        
        if not res_vista.data:
            print(f"⚠️ No se encontró el ID {item_id} en la base de datos. Saltando...")
            continue
            
        marca = res_vista.data[0]['marca']
        ruta_imagen = res_vista.data[0]['img_url']
        
        # B) Eliminar los outfits afectados de 'datos_sinteticos'
        # Usamos .contains() para buscar el ID dentro del array/json de 'prendas_ids'
        try:
            res_outfits = supabase.table("datos_sinteticos").delete().contains("prendas_ids", [item_id]).execute()
            eliminados = len(res_outfits.data) if res_outfits.data else 0
            print(f"✅ Eliminados {eliminados} outfits contaminados en 'datos_sinteticos'.")
        except Exception as e:
            print(f"❌ Error al borrar outfits: {e}")

        # C) Eliminar la imagen del bucket (si procede)
        if marca != 'zara' and not ruta_imagen.startswith("http"):
            nombre_bucket = MAPA_BUCKETS.get(marca, marca)
            try:
                # Supabase requiere que se envíe una lista con las rutas a borrar
                supabase.storage.from_(nombre_bucket).remove([ruta_imagen])
                print(f"✅ Imagen borrada del bucket '{nombre_bucket}'.")
            except Exception as e:
                print(f"❌ Error al borrar la imagen del bucket: {e}")
        else:
            print("ℹ️ Imagen externa o de Zara; se omite el borrado en el Storage.")

        # D) Eliminar la fila de su tabla original
        tabla_origen = MAPA_TABLAS.get(marca)
        if tabla_origen:
            try:
                supabase.table(tabla_origen).delete().eq("id", item_id).execute()
                print(f"✅ Prenda borrada definitivamente de la tabla '{tabla_origen}'.")
            except Exception as e:
                print(f"❌ Error al borrar de la tabla original: {e}")

if __name__ == "__main__":
    purgar_ids(ids_a_borrar)
    print("\n¡Limpieza profunda terminada! 🧹✨")