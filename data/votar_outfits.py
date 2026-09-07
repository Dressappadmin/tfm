import os
from supabase import create_client, Client
import streamlit as st
import random
import time

SLOTS = { 
    'SUPERIOR':        ['camisetas', 'camisas y blusas', 'tops y bodies', 'jerseys y cardigans', 'sudaderas', 'blazers y chalecos'],
    'INFERIOR':        ['pantalones', 'jeans', 'faldas', 'shorts y bermudas'],
    'CUERPO_COMPLETO': ['vestidos', 'monos y petos'],
    'ABRIGO':          ['abrigos', 'chaquetas y cazadoras'],
    'CALZADO':         ['zapatos'],
    'ACCESORIO':       ['accesorios', 'bolsos']
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
    mapa_prendas = {prenda.strip().lower(): slot for slot, prendas in SLOTS.items() for prenda in prendas}
    conteos = {slot: 0 for slot in SLOTS.keys()}
    
    tiene_monos_petos = False

    for item in tipos_prendas:
        item_norm = item.strip().lower()
        item_upper = item.strip().upper()

        if item_upper in conteos:
            conteos[item_upper] += 1
        elif item_norm in mapa_prendas:
            slot = mapa_prendas[item_norm]
            conteos[slot] += 1
            
        if item_norm == 'monos y petos':
            tiene_monos_petos = True

    if conteos['CALZADO'] > 1:
        return False, "¡Ups! No puedes incluir más de un par de calzado en un mismo outfit."
    if conteos['CALZADO'] == 0:
        return False, "Todo outfit debe llevar calzado."
        
    if conteos['CUERPO_COMPLETO'] > 0:
        if conteos['CUERPO_COMPLETO'] > 1:
            return False, "No puedes incluir más de una prenda de cuerpo completo a la vez."
            
        if tiene_monos_petos:
            if conteos['INFERIOR'] > 0:
                return False, "Si llevas un mono o peto, no puedes añadir partes inferiores extra."
            if conteos['SUPERIOR'] > 2:
                return False, "Con un mono o peto puedes llevar como máximo dos partes superiores (ej. camiseta y sudadera)."
        else:
            if conteos['SUPERIOR'] > 0 or conteos['INFERIOR'] > 0:
                return False, "Si has elegido un vestido, no debes añadir partes superiores ni inferiores extra."

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
@st.cache_data(ttl=60)
def obtener_ids_defectuosos():
    try:
        res = supabase.table("defectuosos").select("prenda_id").execute()
        return [str(r["prenda_id"]) for r in res.data]
    except:
        return []

def obtener_prenda_aleatoria(slot_buscado: str, categoria_fija: str = None) -> dict:
    categoria_elegida = categoria_fija if categoria_fija else random.choice(SLOTS[slot_buscado])
    ids_malos = obtener_ids_defectuosos()
    
    query_conteo = supabase.table("vista_ropa_unificada") \
        .select("id", count="exact") \
        .ilike("family_unificada", categoria_elegida)
        
    query_datos = supabase.table("vista_ropa_unificada") \
        .select("id, img_url, marca") \
        .ilike("family_unificada", categoria_elegida)
        
    if ids_malos:
        filtro_excluir = f"({','.join(ids_malos)})"
        query_conteo = query_conteo.filter("id", "not.in", filtro_excluir)
        query_datos = query_datos.filter("id", "not.in", filtro_excluir)
    
    try:
        conteo = query_conteo.limit(1).execute()
        total_prendas = conteo.count
    except Exception as e:
        total_prendas = 0
    
    if total_prendas == 0 or total_prendas is None:
        return {
            "id": "ERROR",
            "url": "https://placehold.co/300x400?text=SIN+FOTOS",
            "categoria": categoria_elegida,
            "slot": slot_buscado
        }
    
    posicion_aleatoria = random.randint(0, total_prendas - 1)
    
    try:
        respuesta = query_datos.range(posicion_aleatoria, posicion_aleatoria).execute()
        prenda_seleccionada = respuesta.data[0]
        url_bruta = prenda_seleccionada["img_url"]
        marca = prenda_seleccionada["marca"]
    except Exception:
        return {
            "id": "ERROR",
            "url": "https://placehold.co/300x400?text=ERROR+BBDD",
            "categoria": categoria_elegida,
            "slot": slot_buscado
        }
    
    if marca == 'zara' and "{width}" in url_bruta:
        url_limpia = url_bruta.replace("{width}", "400")
    elif url_bruta.startswith("http"):
        url_limpia = url_bruta
    else:
        mapa_buckets = {
            'bershka': 'nombre_bucket_bershka',
            'mango': 'nombre_bucket_mango',
            'hym': 'nombre_bucket_hym'
        }
        nombre_bucket = mapa_buckets.get(marca, marca)
        url_limpia = supabase.storage.from_(nombre_bucket).get_public_url(url_bruta)
    
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
if "form_reset" not in st.session_state:
    st.session_state.form_reset = 0

# --- PANTALLA DE LOGIN ---
if st.session_state.username is None:
    st.title("👗 Ayúdame con mi TFM: Outfit Rater")
    st.write("Crea un usuario y ayúdame a generar el mejor dataset de moda.")
    
    try:
        resp_conteo = supabase.rpc("contar_usuarios_unicos").execute()
        total_usuarios = resp_conteo.data
    except:
        total_usuarios = 0

    st.metric("👥 Amigos colaborando actualmente", total_usuarios)
    st.divider()

    user_input = st.text_input("Tu nombre o apodo:")
    es_retorno = st.checkbox("Ya estuve aquí antes (continuar donde lo dejé)")
    
    if st.button("¡Empezar a valorar!", type="primary"):
        if user_input.strip():
            usuario = user_input.strip()
            
            try:
                res_usuario = supabase.table("datos_sinteticos").select("id").ilike("username", usuario).limit(1).execute()
                usuario_existe = len(res_usuario.data) > 0
                
                if not es_retorno and usuario_existe:
                    st.error("Ese nombre ya está cogido por otro amigo. ¡Elige otro o añade tu apellido!")
                elif es_retorno and not usuario_existe:
                    st.error("No encuentro ese nombre en la base de datos. Si eres nuevo, desmarca la casilla de arriba.")
                else:
                    st.session_state.username = usuario
                    
                    res_buenos = supabase.table("datos_sinteticos").select("id", count="exact").eq("username", usuario).eq("is_good", True).execute()
                    st.session_state.good_count = res_buenos.count if res_buenos.count is not None else len(res_buenos.data)
                    
                    st.rerun()
            except Exception as e:
                st.error(f"Error conectando a la base de datos: {e}")
        else:
            st.warning("Por favor, introduce un nombre.")

# --- PANTALLA PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write("### Tu progreso")
    
    progreso_buenos = min(st.session_state.good_count / 50.0, 1.0)
    st.sidebar.metric("🔥 Outfits Buenos", f"{st.session_state.good_count} / 50")
    st.sidebar.progress(progreso_buenos)
    
    if st.session_state.good_count >= 50:
        st.balloons()
        st.success("## ¡Misión cumplida! 🎉")
        st.write("Has completado tus 50 valoraciones. Muchísimas gracias por ayudarme a generar los datos para mi TFM. ¡Ya puedes cerrar esta pestaña!")
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
            st.caption(f"ID: {prenda['id']}")
            
            checkbox_key = f"defect_{prenda['id']}"
            es_defectuosa = st.checkbox("⚠️ Imagen rota/defectuosa", key=checkbox_key)
            
            if st.button(f"🔄 Cambiar", key=f"btn_swap_{idx}", use_container_width=True):
                if es_defectuosa and prenda['id'] != "ERROR":
                    try:
                        supabase.table("defectuosos").insert({
                            "prenda_id": prenda['id'],
                            "username": st.session_state.username
                        }).execute()
                    except Exception:
                        pass

                ids_actuales = [p['id'] for p in st.session_state.outfit if p['id'] != "ERROR"]
                if ids_actuales:
                    try:
                        supabase.table("datos_sinteticos").insert({
                            "username": st.session_state.username,
                            "prendas_ids": ids_actuales,
                            "is_good": False,
                            "temporalidad": None,
                            "ocasion": None
                        }).execute()
                    except Exception as e:
                        pass # Silencioso, no bloquea la experiencia del usuario
                
                st.session_state.outfit[idx] = obtener_prenda_aleatoria(prenda['slot'])
                st.rerun()

            categorias_sin_esta_prenda = [p['categoria'] for i, p in enumerate(st.session_state.outfit) if i != idx]
            es_valido_sin_prenda, _ = validar_reglas_outfit(categorias_sin_esta_prenda)
            
            if es_valido_sin_prenda:
                if st.button(f"❌ Quitar", key=f"btn_del_{idx}", use_container_width=True):
                    ids_actuales = [p['id'] for p in st.session_state.outfit if p['id'] != "ERROR"]
                    if ids_actuales:
                        try:
                            supabase.table("datos_sinteticos").insert({
                                "username": st.session_state.username,
                                "prendas_ids": ids_actuales,
                                "is_good": False,
                                "temporalidad": None,
                                "ocasion": None
                            }).execute()
                        except Exception as e:
                            pass
                    
                    st.session_state.outfit.pop(idx)
                    st.rerun()
                
    st.divider()
    
    st.write("### ➕ Añadir otra prenda al outfit")
    
    todas_las_categorias = [categoria for lista in SLOTS.values() for categoria in lista]
    categorias_actuales = [p['categoria'] for p in st.session_state.outfit]
    
    categorias_permitidas = []
    for cat in todas_las_categorias:
        outfit_simulado = categorias_actuales + [cat]
        es_valido, _ = validar_reglas_outfit(outfit_simulado)
        if es_valido:
            categorias_permitidas.append(cat.title())
            
    if categorias_permitidas:
        col_cat, col_btn = st.columns([3, 1])
        with col_cat:
            cat_seleccionada = st.selectbox(
                "Selecciona el tipo de prenda:", 
                categorias_permitidas,
                index=None,
                placeholder="Elige una categoría (ej. Sudaderas)...",
                key=f"sel_add_{st.session_state.form_reset}"
            )
        with col_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Añadir prenda", use_container_width=True):
                if cat_seleccionada:
                    cat_lower = cat_seleccionada.lower()
                    
                    slot_encontrado = None
                    for s, prendas_list in SLOTS.items():
                        if cat_lower in prendas_list:
                            slot_encontrado = s
                            break
                            
                    if slot_encontrado:
                        # 1. Guardamos el outfit ACTUAL (antes de añadir, como falso)
                        ids_actuales = [p['id'] for p in st.session_state.outfit if p['id'] != "ERROR"]
                        if ids_actuales:
                            try:
                                supabase.table("datos_sinteticos").insert({
                                    "username": st.session_state.username,
                                    "prendas_ids": ids_actuales,
                                    "is_good": False,
                                    "temporalidad": None,
                                    "ocasion": None
                                }).execute()
                            except Exception:
                                pass
                        
                        # 2. Añadimos la prenda nueva y recargamos
                        nueva_prenda = obtener_prenda_aleatoria(slot_encontrado, categoria_fija=cat_lower)
                        st.session_state.outfit.append(nueva_prenda)
                        st.rerun()
                else:
                    st.warning("Selecciona una categoría primero.")
    else:
        st.info("💡 Según las reglas, este outfit ya no admite más prendas (ya tiene base completa y calzado).")

    st.divider()
    
    st.write("### 🏷️ ¿Para cuándo y para qué es este outfit?")
    col_temp, col_ocas = st.columns(2)
    
    key_temporalidad = f"sel_temp_{st.session_state.form_reset}"
    key_ocasion = f"sel_ocas_{st.session_state.form_reset}"
    
    with col_temp:
        st.selectbox(
            "Temporalidad", 
            ["Invierno", "Verano", "Entretiempo"],
            index=None,
            placeholder="Selecciona temporalidad...",
            key=key_temporalidad
        )
        
    with col_ocas:
        st.selectbox(
            "Ocasión", 
            ["Casual", "Formal-Oficina", "Fiesta-Discoteca", "Fiesta-Elegante", "Deporte", "Otros"],
            index=None,
            placeholder="Selecciona ocasión...",
            key=key_ocasion
        )

    st.divider()
    
    ya_tiene_50_buenos = st.session_state.good_count >= 50
    
    if st.button("🔥 ¡Me encanta! (Guardar como BUENO)", use_container_width=True, type="primary", disabled=ya_tiene_50_buenos):
        temp_elegida = st.session_state[key_temporalidad]
        ocas_elegida = st.session_state[key_ocasion]
        
        if temp_elegida is None or ocas_elegida is None:
            st.error("⚠️ ¡Espera! Debes seleccionar la **Temporalidad** y la **Ocasión** antes de guardar el outfit.")
        else:
            ids_finales = [p['id'] for p in st.session_state.outfit if p['id'] != "ERROR"]
            
            try:
                # Intentar hacer el guardado en base de datos
                supabase.table("datos_sinteticos").insert({
                    "username": st.session_state.username,
                    "prendas_ids": ids_finales,
                    "is_good": True,
                    "temporalidad": temp_elegida,
                    "ocasion": ocas_elegida
                }).execute()
                
                # Si llegamos aquí, el guardado fue exitoso
                st.session_state.good_count += 1
                st.success("¡Outfit guardado correctamente!")
                time.sleep(1)
                
                st.session_state.outfit = generar_nuevo_outfit()
                st.session_state.form_reset += 1
                
                st.rerun()
                
            except Exception as e:
                # Si hay cualquier error al guardar, mostramos aviso sin romper la app ni avanzar
                st.error(f"❌ Ocurrió un error al guardar en la base de datos: {e}")