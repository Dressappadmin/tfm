import os
from supabase import create_client, Client
import streamlit as st
import random
import time

SLOTS = { 
    'SUPERIOR':        ['camiseta', 'camisa', 'tops y otras p.', 'jersey', 'sudadera', 'body', 'chaleco'],
    'INFERIOR':        ['pantalon', 'falda', 'short', 'bermuda', 'leggings'],
    'CUERPO_COMPLETO': ['vestido', 'mono', 'peto'],
    'ABRIGO':          ['abrigo', 'anorak', 'chaqueta', 'cazadora', 'gabardina impermea', 'blazer'],
    'CALZADO':         ['bambas', 'bota plana', 'bota tacon', 'botin plano', 'botin tacon', 'zapato tacon', 'zapato plano', 'sandalia tacon', 'sandalia plana', 'calzado deportivo'],
    'ACCESORIO':       ['bisuteria', 'bolsos', 'cinturones', 'pañoletas/foulard', 'gorro', 'paraguas', 'monedero billetera', 'complementos', 'accesorios', 'guante'],
}

# Inicializar cliente de Supabase
@st.cache_resource
def init_connection() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ==========================================
# 1. DICCIONARIO Y REGLAS DE NEGOCIO
# ==========================================
def validar_reglas_outfit(tipos_prendas: list[str]) -> tuple[bool, str]:
    mapa_prendas = {prenda: slot for slot, prendas in SLOTS.items() for prenda in prendas}
    conteos = {slot: 0 for slot in SLOTS.keys()}

    for item in tipos_prendas:
        item_norm = item.strip().lower()
        item_upper = item.strip().upper()

        if item_upper in conteos:
            conteos[item_upper] += 1
        elif item_norm in mapa_prendas:
            slot = mapa_prendas[item_norm]
            conteos[slot] += 1

    if conteos['CALZADO'] > 1:
        return False, "¡Ups! No puedes incluir más de un par de calzado en un mismo outfit."
    if conteos['CALZADO'] == 0:
        return False, "Todo outfit debe llevar calzado."
    if conteos['CUERPO_COMPLETO'] > 0 and (conteos['SUPERIOR'] > 0 or conteos['INFERIOR'] > 0):
        return False, "Si has elegido una prenda de cuerpo entero, no debes añadir partes superiores ni inferiores extra."

    tiene_base_valida = (conteos['SUPERIOR'] >= 1 and conteos['INFERIOR'] >= 1) or (conteos['CUERPO_COMPLETO'] == 1)
    
    if not tiene_base_valida:
        if conteos['CUERPO_COMPLETO'] == 0:
            if conteos['SUPERIOR'] >= 1 and conteos['INFERIOR'] == 0:
                return False, "Te falta añadir una parte inferior."
            elif conteos['INFERIOR'] >= 1 and conteos['SUPERIOR'] == 0:
                return False, "Te falta añadir una parte superior."
            else:
                return False, "El outfit está incompleto."

    if conteos['INFERIOR'] > 1:
        return False, "Has seleccionado demasiadas partes inferiores."
    if conteos['SUPERIOR'] > 3:
        return False, "Has seleccionado demasiadas partes superiores."

    return True, "¡Outfit validado correctamente!"

# ==========================================
# 2. SIMULADOR DE BASE DE DATOS
# ==========================================
def obtener_prenda_aleatoria(slot_buscado: str) -> dict:
    categoria_elegida = random.choice(SLOTS[slot_buscado])
    
    respuesta = supabase.table("zara_imgs_wback").select("id, img_url").ilike("family", categoria_elegida).execute()
    prendas_disponibles = respuesta.data
    
    if not prendas_disponibles:
        return {
            "id": "ERROR",
            "url": "https://placehold.co/300x400?text=SIN+FOTOS",
            "categoria": categoria_elegida,
            "slot": slot_buscado
        }
        
    prenda_seleccionada = random.choice(prendas_disponibles)
    url_limpia = prenda_seleccionada["img_url"].replace("{width}", "400")
    
    return {
        "id": prenda_seleccionada["id"],
        "url": url_limpia,
        "categoria": categoria_elegida,
        "slot": slot_buscado
    }

def generar_nuevo_outfit() -> list:
    valido = False
    outfit_candidato = []
    
    while not valido:
        outfit_candidato = []
        usar_cuerpo_completo = random.choice([True, False])
        
        if usar_cuerpo_completo:
            outfit_candidato.append(obtener_prenda_aleatoria('CUERPO_COMPLETO'))
        else:
            num_superiores = random.randint(1, 2) 
            for _ in range(num_superiores):
                outfit_candidato.append(obtener_prenda_aleatoria('SUPERIOR'))
            outfit_candidato.append(obtener_prenda_aleatoria('INFERIOR'))
            
        outfit_candidato.append(obtener_prenda_aleatoria('CALZADO'))
        
        if random.random() > 0.7:
            outfit_candidato.append(obtener_prenda_aleatoria('ABRIGO'))
        
        categorias_candidatas = [p['categoria'] for p in outfit_candidato]
        valido, _ = validar_reglas_outfit(categorias_candidatas)
        
    return outfit_candidato

# ==========================================
# 3. INTERFAZ GRÁFICA (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Outfit Rater", layout="wide")

if "username" not in st.session_state:
    st.session_state.username = None
if "outfit" not in st.session_state:
    st.session_state.outfit = None
if "good_count" not in st.session_state:
    st.session_state.good_count = 0
if "bad_count" not in st.session_state:
    st.session_state.bad_count = 0

# --- PANTALLA DE LOGIN ---
if st.session_state.username is None:
    st.title("👗 Ayúdame con mi TFM: Outfit Rater")
    st.write("Crea un usuario y ayúdame a generar el mejor dataset de moda.")
    
    try:
        resp = supabase.table("datos_sinteticos").select("username").execute()
        usuarios_unicos = set([r["username"].lower() for r in resp.data])
        total_usuarios = len(usuarios_unicos)
    except:
        usuarios_unicos = set()
        total_usuarios = 0

    st.metric("👥 Amigos colaborando actualmente", total_usuarios)
    st.divider()

    user_input = st.text_input("Tu nombre o apodo:")
    es_retorno = st.checkbox("Ya estuve aquí antes (continuar donde lo dejé)")
    
    if st.button("¡Empezar a valorar!", type="primary"):
        if user_input.strip():
            usuario = user_input.strip()
            usuario_lower = usuario.lower()
            
            if not es_retorno and usuario_lower in usuarios_unicos:
                st.error("Ese nombre ya está cogido por otro amigo. ¡Elige otro o añade tu apellido!")
            elif es_retorno and usuario_lower not in usuarios_unicos:
                st.error("No encuentro ese nombre en la base de datos. Si eres nuevo, desmarca la casilla de arriba.")
            else:
                st.session_state.username = usuario
                
                res_buenos = supabase.table("datos_sinteticos").select("id", count="exact").eq("username", usuario).eq("is_good", True).execute()
                res_malos = supabase.table("datos_sinteticos").select("id", count="exact").eq("username", usuario).eq("is_good", False).execute()
                
                st.session_state.good_count = res_buenos.count if res_buenos.count is not None else len(res_buenos.data)
                st.session_state.bad_count = res_malos.count if res_malos.count is not None else len(res_malos.data)
                
                st.rerun()
        else:
            st.warning("Por favor, introduce un nombre.")

# --- PANTALLA PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write("### Tu progreso")
    
    progreso_buenos = min(st.session_state.good_count / 50.0, 1.0)
    st.sidebar.metric("🔥 Outfits Buenos", f"{st.session_state.good_count} / 50")
    st.sidebar.progress(progreso_buenos)
    
    progreso_malos = min(st.session_state.bad_count / 50.0, 1.0)
    st.sidebar.metric("🤮 Outfits Malos (Descartes)", f"{st.session_state.bad_count} / 50")
    st.sidebar.progress(progreso_malos)
    
    if st.session_state.good_count >= 50 and st.session_state.bad_count >= 50:
        st.balloons()
        st.success("## ¡Misión cumplida! 🎉")
        st.write("Has completado tus 100 valoraciones. Muchísimas gracias por ayudarme a generar los datos para mi TFM. ¡Ya puedes cerrar esta pestaña!")
        st.stop()

    if st.session_state.outfit is None:
        st.session_state.outfit = generar_nuevo_outfit()

    st.title(f"¡Hola, {st.session_state.username}!")
    st.write("Cambia (o quita) las prendas que no te convenzan y valora el conjunto final.")
    st.divider()
    
    num_prendas = len(st.session_state.outfit)
    columnas = st.columns(num_prendas)
    
    for idx, col in enumerate(columnas):
        prenda = st.session_state.outfit[idx]
        with col:
            st.image(prenda["url"], use_container_width=True)
            st.caption(f"{prenda['categoria'].title()} ({prenda['slot']})")
            
            # --- BOTÓN DE CAMBIAR (Mantiene la jugada del feedback implícito) ---
            if st.button(f"🔄 Cambiar", key=f"btn_swap_{idx}", use_container_width=True):
                if st.session_state.bad_count < 50:
                    ids_actuales = [p['id'] for p in st.session_state.outfit]
                    supabase.table("datos_sinteticos").insert({
                        "username": st.session_state.username,
                        "prendas_ids": ids_actuales,
                        "is_good": False,
                        "temporalidad": None,
                        "ocasion": None
                    }).execute()
                    st.session_state.bad_count += 1
                
                st.session_state.outfit[idx] = obtener_prenda_aleatoria(prenda['slot'])
                st.rerun()

            # --- NUEVO: BOTÓN DE ELIMINAR PRENDA ---
            # Simulamos el outfit sin esta prenda concreta
            categorias_sin_esta_prenda = [p['categoria'] for i, p in enumerate(st.session_state.outfit) if i != idx]
            # Validamos si el outfit sobrante es legal
            es_valido_sin_prenda, _ = validar_reglas_outfit(categorias_sin_esta_prenda)
            
            if es_valido_sin_prenda:
                # Solo mostramos el botón si quitarla no rompe el outfit
                if st.button(f"❌ Quitar", key=f"btn_del_{idx}", use_container_width=True):
                    # Quitar algo también cuenta como que el conjunto anterior no le gustaba
                    if st.session_state.bad_count < 50:
                        ids_actuales = [p['id'] for p in st.session_state.outfit]
                        supabase.table("datos_sinteticos").insert({
                            "username": st.session_state.username,
                            "prendas_ids": ids_actuales,
                            "is_good": False,
                            "temporalidad": None,
                            "ocasion": None
                        }).execute()
                        st.session_state.bad_count += 1
                        
                    # Eliminamos la prenda de la lista y recargamos
                    st.session_state.outfit.pop(idx)
                    st.rerun()
                
    st.divider()
    
    st.write("### 🏷️ ¿Para cuándo y para qué es este outfit?")
    col_temp, col_ocas = st.columns(2)
    
    with col_temp:
        temporalidad = st.selectbox(
            "Temporalidad", 
            ["Invierno", "Verano", "Entretiempo"]
        )
        
    with col_ocas:
        ocasion = st.selectbox(
            "Ocasión", 
            ["Casual", "Formal-Oficina", "Fiesta-Discoteca", "Fiesta-Elegante", "Deporte", "Otros"]
        )

    st.divider()
    
    ya_tiene_50_buenos = st.session_state.good_count >= 50
    
    if st.button("🔥 ¡Me encanta! (Guardar como BUENO)", use_container_width=True, type="primary", disabled=ya_tiene_50_buenos):
        ids_finales = [p['id'] for p in st.session_state.outfit]
        
        supabase.table("datos_sinteticos").insert({
            "username": st.session_state.username,
            "prendas_ids": ids_finales,
            "is_good": True,
            "temporalidad": temporalidad,
            "ocasion": ocasion
        }).execute()
        
        st.session_state.good_count += 1
        st.success("¡Outfit guardado correctamente!")
        time.sleep(1)
        st.session_state.outfit = generar_nuevo_outfit()
        st.rerun()