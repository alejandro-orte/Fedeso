import streamlit as st
import pandas as pd
import base64
import os
import datetime
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import gspread
from google.oauth2.service_account import Credentials

# =========================================================
# CONFIGURACIÓN DE PÁGINA (DEBE SER EL PRIMER COMANDO ST)
# =========================================================
st.set_page_config(
    page_title="FEDESO - Mi Estado de Cuenta",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CONFIGURACIÓN Y CONSTANTES
# =========================================================
SHEET_ID = "12A0vnk-mUz2PaQpBmXnOPWtjzvOr7CXpUHLMn9ioLNQ"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdBFMIqAXxKNis9O29AbqPheXlfZqUdsUlUolERBICgTwWEsw/viewform"

TASA_MENSUAL_DEFAULT = 0.0069865  # 0.7% Mensual Vencido

MESES_MAP = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}

# =========================================================
# ESTILOS CSS - ACCESIBILIDAD Y OCULTAMIENTO DE MENÚS/OPCIONES
# =========================================================
st.markdown("""
<style>
    /* 1. OCULTAR BARRA SUPERIOR COMPLETA (Share, GitHub, editar, opciones) */
    header[data-testid="stHeader"], 
    [data-testid="stHeaderToolbar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* 2. OCULTAR BARRA FLOTANTE SOBRE LAS TABLAS (descarga, búsqueda, pantalla completa) */
    [data-testid="stElementToolbar"] {
        display: none !important;
    }

    /* 3. BARRA LATERAL ANCHA Y DESTACADA PARA PERSONAS MAYORES */
    [data-testid="stSidebar"] {
        width: 340px !important;
        background-color: #f8fafc !important;
        border-right: 3px solid #cbd5e1 !important;
    }
    
    /* 4. BOTONES DE MENÚ GRANDES, CLAROS E INTUITIVOS */
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 56px !important;
        font-size: 1.10rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
        border: 2px solid #2563eb !important;
        background-color: #ffffff !important;
        color: #1e3a8a !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-color: #1d4ed8 !important;
        transform: translateY(-2px);
    }

    /* BOTÓN ESPECIAL DE CERRAR SESIÓN */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        border-color: #dc2626 !important;
        background-color: #fef2f2 !important;
        color: #991b1b !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #dc2626 !important;
        color: #ffffff !important;
    }

    /* TARJETAS Y CONTENEDORES PRINCIPALES */
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 22px;
        border: 1px solid #e5e7eb;
    }
    .metric-container {
        display: flex;
        flex-direction: column;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 800;
        color: #111827;
    }
    .status-tag-green {
        display: inline-block;
        background-color: #dcfce7;
        color: #15803d;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.90rem;
        font-weight: 800;
    }
    .status-tag-yellow {
        display: inline-block;
        background-color: #fef3c7;
        color: #b45309;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.90rem;
        font-weight: 800;
    }
    .status-tag-red {
        display: inline-block;
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.90rem;
        font-weight: 800;
    }
    .header-box {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 10px rgba(30, 58, 138, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# CONEXIÓN A GOOGLE SHEETS PARA LECTURA Y ESCRITURA
# =========================================================
def obtener_cliente_gspread():
    """Conecta con la API de Google Sheets mediante Secrets de Streamlit o archivo local."""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(credentials)
        elif os.path.exists("service_account.json"):
            credentials = Credentials.from_service_account_file("service_account.json", scopes=scopes)
            return gspread.authorize(credentials)
        else:
            return None
    except Exception as e:
        st.error(f"Error al autenticar Google Sheets API: {e}")
        return None

def agregar_fila_sheet(nombre_pestana: str, fila: list):
    """Agrega una fila nueva al final de la pestaña especificada en Google Sheets."""
    gc = obtener_cliente_gspread()
    if gc:
        try:
            sh = gc.open_by_key(SHEET_ID)
            worksheet = sh.worksheet(nombre_pestana)
            worksheet.append_row(fila)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Error al escribir en Google Sheets: {e}")
            return False
    else:
        st.error("No se configuraron las credenciales de escritura en Google Sheets.")
        return False

def agregar_filas_sheet(nombre_pestana: str, filas: list):
    """Agrega múltiples filas al final de la pestaña en Google Sheets."""
    gc = obtener_cliente_gspread()
    if gc:
        try:
            sh = gc.open_by_key(SHEET_ID)
            worksheet = sh.worksheet(nombre_pestana)
            worksheet.append_rows(filas)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"Error al realizar la inserción masiva en Google Sheets: {e}")
            return False
    else:
        st.error("No se configuraron las credenciales de escritura en Google Sheets.")
        return False

@st.cache_data(ttl=2, show_spinner=False)
def cargar_pestana(nombre_pestana: str) -> pd.DataFrame:
    """Carga datos en tiempo real mediante API gspread con fallback a CSV."""
    gc = obtener_cliente_gspread()
    if gc:
        try:
            sh = gc.open_by_key(SHEET_ID)
            worksheet = sh.worksheet(nombre_pestana)
            data = worksheet.get_all_values()
            if data:
                headers = [str(h).replace('\xa0', '').strip().lower() for h in data[0]]
                df = pd.DataFrame(data[1:], columns=headers)
                return df
        except Exception:
            pass
    
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
        df = pd.read_csv(url, dtype=str)
        df.columns = [str(col).replace('\xa0', '').strip().lower() for col in df.columns]
        return df
    except Exception:
        return pd.DataFrame()

def cargar_usuarios() -> pd.DataFrame:
    return cargar_pestana("Usuarios")

# =========================================================
# FUNCIONES AUXILIARES DE DATOS
# =========================================================
def parsear_fecha_flexible(texto):
    """Convierte libremente strings a fecha de inicio de mes."""
    if pd.isna(texto) or not str(texto).strip():
        return None
    
    val = str(texto).strip().lower()
    for sep in ['/', '.', ' ', '_']:
        val = val.replace(sep, '-')
    
    parts = [p for p in val.split('-') if p]
    
    if len(parts) >= 2:
        mes_cand = parts[0]
        anio_cand = parts[-1]
        if mes_cand in MESES_MAP and anio_cand.isdigit():
            m = MESES_MAP[mes_cand]
            y_int = int(anio_cand)
            if y_int < 100:
                y = dt.now().year if y_int < 24 else 2000 + y_int
            else:
                y = y_int
            return datetime.date(y, m, 1)

    res = pd.to_datetime(val, errors="coerce", dayfirst=True)
    if pd.notna(res):
        return datetime.date(res.year, res.month, 1)
            
    return None

def get_image_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return "https://raw.githubusercontent.com/alejandro-orte/Fedeso/main/fedeso%20imagen%20web.png"

LOGO_URL = get_image_base64("fedeso imagen web.png")

def limpiar_numero(valor):
    if pd.isna(valor) or valor is None:
        return 0.0
    texto = str(valor).replace('$', '').replace(',', '').replace('%', '').replace(' ', '').strip()
    try:
        return float(texto)
    except ValueError:
        return 0.0

def normalizar_texto(serie: pd.Series, minusculas: bool = True) -> pd.Series:
    res = (
        serie.fillna("")
        .astype(str)
        .str.replace(r'\xa0', '', regex=True)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )
    return res.str.lower() if minusculas else res

# =========================================================
# CONTROL DE SESIÓN
# =========================================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nombre"] = ""
    st.session_state["rol"] = "asociado"
if "pantalla" not in st.session_state:
    st.session_state["pantalla"] = "dashboard"

# =========================================================
# LOGIN DE USUARIOS
# =========================================================
if not st.session_state["autenticado"]:
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.write("")
        st.write("")
        st.markdown(
            f"""<div style="text-align: center;"><img src="{LOGO_URL}" width="200"></div>""",
            unsafe_allow_html=True
        )
        with st.form("login_form"):
            st.subheader("🔑 Iniciar Sesión")
            user_input = st.text_input("Usuario (Cédula)").strip().lower()
            pass_input = st.text_input("Contraseña", type="password").strip()
            submit = st.form_submit_button("Ingresar a mi Fondo", use_container_width=True)

            if submit:
                if not user_input or not pass_input:
                    st.warning("Por favor ingrese usuario y contraseña.")
                else:
                    with st.spinner("Verificando credenciales..."):
                        try:
                            df_users = cargar_usuarios()
                            if "usuario" not in df_users.columns or "contrasena" not in df_users.columns:
                                st.error("❌ Estructura de tabla no válida.")
                            else:
                                df_users["usuario"] = normalizar_texto(df_users["usuario"], minusculas=True)
                                df_users["contrasena"] = normalizar_texto(df_users["contrasena"], minusculas=False)
                                valido = df_users[
                                    (df_users["usuario"] == user_input) & (df_users["contrasena"] == pass_input)
                                ]
                                if not valido.empty:
                                    st.session_state["autenticado"] = True
                                    st.session_state["usuario"] = user_input
                                    st.session_state["nombre"] = (
                                        valido["nombre"].iloc[0] if "nombre" in valido.columns else user_input
                                    )
                                    st.session_state["rol"] = (
                                        valido["rol"].iloc[0].lower().strip() if "rol" in valido.columns else "asociado"
                                    )
                                    st.rerun()
                                else:
                                    st.error("Usuario o contraseña incorrectos.")
                        except Exception as e:
                            st.error(f"Error al conectar: {e}")

# =========================================================
# DASHBOARD PRINCIPAL
# =========================================================
else:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0;">
                <img src="{LOGO_URL}" width="160"><br><br>
                <div style="background-color: #ffffff; padding: 14px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 15px;">
                    <span style="font-size: 0.85rem; color: #6b7280; font-weight: 600;">Bienvenido(a)</span><br>
                    <strong style="color: #111827; font-size: 1.1rem;">👤 {st.session_state['nombre']}</strong><br>
                    <small style="color: #2563eb; font-weight: 700;">Rol: {st.session_state['rol'].capitalize()}</small>
                </div>
            </div>
            
            <div style="background-color: #e0f2fe; border-left: 5px solid #0284c7; padding: 10px 12px; border-radius: 8px; margin-bottom: 16px;">
                <strong style="color: #0369a1; font-size: 0.95rem;">📌 MENÚ DE NAVEGACIÓN</strong><br>
                <span style="color: #0c4a6e; font-size: 0.85rem;">Toque cualquier botón para cambiar de sección:</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        txt_dash = "▶️ 📊 Mi Estado de Cuenta" if st.session_state["pantalla"] == "dashboard" else "📊 Mi Estado de Cuenta"
        txt_sim = "▶️ 🧮 Simulador de Crédito" if st.session_state["pantalla"] == "simulador" else "🧮 Simulador de Crédito"
        txt_adm = "▶️ 🛠️ Panel de Administración" if st.session_state["pantalla"] == "admin" else "🛠️ Panel de Administración"

        if st.button(txt_dash, use_container_width=True, key="btn_dashboard"):
            st.session_state["pantalla"] = "dashboard"
            st.rerun()

        if st.button(txt_sim, use_container_width=True, key="btn_simulador"):
            st.session_state["pantalla"] = "simulador"
            st.rerun()

        if st.session_state["rol"] == "admin":
            st.divider()
            if st.button(txt_adm, use_container_width=True, key="btn_admin"):
                st.session_state["pantalla"] = "admin"
                st.rerun()

        st.divider()
        st.link_button("📝 Solicitud de Crédito", FORM_URL, use_container_width=True)
        st.write("")
        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True, key="btn_logout"):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = ""
            st.session_state["nombre"] = ""
            st.session_state["rol"] = "asociado"
            st.session_state["pantalla"] = "dashboard"
            st.rerun()

    st.markdown(
        f"""
        <div class="header-box" style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin:0; color:white; font-size: 1.7rem; font-weight:800;">FEDESO</h2>
                <span style="font-size: 1rem; opacity: 0.95;">Fondo Empresarial de Solidaridad</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.95rem; font-weight: 600; opacity: 0.9;">Portal de Asociados</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.session_state["pantalla"] == "dashboard":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">Mi Estado de Cuenta FEDESO</h3>', unsafe_allow_html=True)
        usuario_key = st.session_state["usuario"]

        try:
            with st.spinner("Cargando tu información..."):
                df_resumen = cargar_pestana("Resumen")
                df_amort = cargar_pestana("Amortizacion")

                num_pagadas = 0
                total_cuotas = 0
                estado_proxima_str = "N/A"
                saldo_pendiente_est = 0.0
                porcentaje_progreso = 0.0
                amort_user = pd.DataFrame()
                
                badge_estado_credito = '<span class="status-tag-green">🟢 Al día</span>'

                if "usuario" in df_amort.columns:
                    df_amort["usuario"] = normalizar_texto(df_amort["usuario"])
                    amort_user = df_amort[df_amort["usuario"] == usuario_key].copy()

                if not amort_user.empty:
                    columnas_num = ["intereses", "capital", "saldo"]
                    for col in columnas_num:
                        if col in amort_user.columns:
                            amort_user[col] = amort_user[col].apply(limpiar_numero)

                    if "estado" not in amort_user.columns:
                        amort_user["estado"] = "Pendiente"
                    else:
                        amort_user["estado"] = amort_user["estado"].fillna("Pendiente").astype(str).str.strip()

                    amort_cuotas = amort_user[
                        ~amort_user["cuota_num"].astype(str).str.strip().isin(["0", "0.0"])
                    ].copy()
                    total_cuotas = len(amort_cuotas)

                    estados_limpios = amort_cuotas["estado"].astype(str).str.lower().str.strip()
                    cuotas_pagadas_df = amort_cuotas[estados_limpios.isin(["pagado", "pagada", "al dia", "al día"])]
                    num_pagadas = len(cuotas_pagadas_df)

                    proxima_cuota = amort_cuotas[~estados_limpios.isin(["pagado", "pagada", "al dia", "al día"])]
                    
                    if not proxima_cuota.empty:
                        mes_proximo = proxima_cuota.iloc[0].get("mes_año", "N/A")
                        num_cuota_actual = proxima_cuota.iloc[0].get("cuota_num", "N/A")
                        estado_proxima_str = f"Cuota #{num_cuota_actual} ({mes_proximo})"
                    else:
                        estado_proxima_str = "🎉 Completado"

                    if not cuotas_pagadas_df.empty:
                        saldo_pendiente_est = cuotas_pagadas_df.iloc[-1].get("saldo", 0.0)
                    else:
                        cuota_0 = amort_user[amort_user["cuota_num"].astype(str).str.strip().isin(["0", "0.0"])]
                        if not cuota_0.empty:
                            saldo_pendiente_est = cuota_0.iloc[0].get("saldo", 0.0)
                        elif "usuario" in df_resumen.columns and not df_resumen[df_resumen["usuario"] == usuario_key].empty:
                            saldo_pendiente_est = limpiar_numero(df_resumen[df_resumen["usuario"] == usuario_key]["monto"].iloc[0])

                    if total_cuotas > 0:
                        porcentaje_progreso = min(1.0, num_pagadas / total_cuotas)

                    hoy = datetime.date.today()
                    mes_actual_inicio = datetime.date(hoy.year, hoy.month, 1)

                    if total_cuotas > 0 and num_pagadas >= total_cuotas:
                        badge_estado_credito = '<span class="status-tag-green">🟢 Finalizado</span>'
                    elif proxima_cuota.empty:
                        badge_estado_credito = '<span class="status-tag-green">🟢 Al día</span>'
                    else:
                        texto_fecha_prox = str(proxima_cuota.iloc[0].get("mes_año", "")).strip()
                        fecha_prox_dt = parsear_fecha_flexible(texto_fecha_prox)

                        if fecha_prox_dt:
                            if fecha_prox_dt < mes_actual_inicio:
                                badge_estado_credito = '<span class="status-tag-red">🔴 En Mora</span>'
                            elif fecha_prox_dt == mes_actual_inicio:
                                badge_estado_credito = '<span class="status-tag-yellow">🟡 Pendiente</span>'
                            else:
                                badge_estado_credito = '<span class="status-tag-green">🟢 Al día</span>'
                        else:
                            badge_estado_credito = '<span class="status-tag-green">🟢 Al día</span>'

                if "usuario" in df_resumen.columns:
                    df_resumen["usuario"] = normalizar_texto(df_resumen["usuario"])
                    resumen_user = df_resumen[df_resumen["usuario"] == usuario_key]

                    if not resumen_user.empty:
                        monto = limpiar_numero(resumen_user["monto"].iloc[0])
                        plazo = int(limpiar_numero(resumen_user["plazo"].iloc[0]))
                        tasa_raw = limpiar_numero(resumen_user["tasa_mv"].iloc[0])
                        cuota = limpiar_numero(resumen_user["cuota"].iloc[0])

                        tasa_porcentaje_mv = tasa_raw / 100 if tasa_raw >= 1 else (tasa_raw * 100 if tasa_raw < 0.01 else tasa_raw)
                        tasa_fmt = f"{tasa_porcentaje_mv:.2f}%"
                        tasa_anual_fmt = f"{(tasa_porcentaje_mv * 12):.2f}%"

                        st.markdown(f"""
                        <div class="card">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e5e7eb; padding-bottom: 12px; margin-bottom: 16px;">
                                <h4 style="margin:0; color:#1e3a8a; font-weight:700;">📊 RESUMEN DE PRÉSTAMO</h4>
                                <span style="font-size: 0.95rem; color:#4b5563;">Asociado: <strong>{st.session_state['nombre']}</strong></span>
                            </div>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px;">
                                <div class="metric-container">
                                    <span class="metric-label">Monto del Préstamo</span>
                                    <span class="metric-value">${monto:,.0f}</span>
                                </div>
                                <div class="metric-container">
                                    <span class="metric-label">Plazo (Meses)</span>
                                    <span class="metric-value">{plazo} meses</span>
                                </div>
                                <div class="metric-container">
                                    <span class="metric-label">Tasa M.V.</span>
                                    <span class="metric-value">{tasa_fmt}</span>
                                </div>
                                <div class="metric-container">
                                    <span class="metric-label">Cuota Mensual</span>
                                    <span class="metric-value" style="color:#1e3a8a;">${cuota:,.0f}</span>
                                </div>
                                <div class="metric-container">
                                    <span class="metric-label">Tasa Anual Nominal</span>
                                    <span class="metric-value">{tasa_anual_fmt}</span>
                                </div>
                                <div class="metric-container">
                                    <span class="metric-label">Estado del Crédito</span>
                                    <div style="margin-top: 4px;">{badge_estado_credito}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                pct_val = porcentaje_progreso * 100
                st.markdown(f"""
                <div class="card">
                    <h4 style="margin-top:0; color:#1e3a8a; font-weight:700; border-bottom: 1px solid #e5e7eb; padding-bottom: 12px; margin-bottom: 16px;">
                        📊 ESTADO DE PAGOS Y PROGRESO
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px;">
                        <div class="metric-container">
                            <span class="metric-label">Progreso de Pago</span>
                            <span class="metric-value">{num_pagadas} <span style="font-size:0.95rem; font-weight:normal; color:#6b7280;">de {total_cuotas} cuotas</span></span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Próximo Mes a Pagar</span>
                            <span class="metric-value" style="font-size: 1.2rem; color: #b45309;">{estado_proxima_str}</span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Saldo Pendiente Estimado</span>
                            <span class="metric-value">${saldo_pendiente_est:,.0f}</span>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.90rem; color: #4b5563; font-weight: 700; margin-bottom: 6px;">
                            <span>Progreso Actual de Amortización</span>
                            <span>{pct_val:.1f}% Pagado</span>
                        </div>
                        <div style="background-color: #e5e7eb; border-radius: 10px; height: 12px; width: 100%; overflow: hidden;">
                            <div style="background-color: #2563eb; width: {pct_val}%; height: 100%; border-radius: 10px;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if not amort_user.empty:
                    st.markdown('<h4 style="color:#1e3a8a; margin-top:25px; margin-bottom:10px;">📅 PLAN DE PAGOS (AMORTIZACIONES)</h4>', unsafe_allow_html=True)
                    cols_existentes = [c for c in ["cuota_num", "mes_año", "intereses", "capital", "saldo", "estado"] if c in amort_user.columns]
                    tabla_mostrar = amort_user[cols_existentes].copy()
                    renombrar = {
                        "cuota_num": "Nº",
                        "mes_año": "Mes/Año",
                        "intereses": "Intereses",
                        "capital": "Capital",
                        "saldo": "Saldo",
                        "estado": "Estado de Pago"
                    }
                    tabla_mostrar = tabla_mostrar.rename(columns=renombrar)

                    def formato_estado_badge(val):
                        val_str = str(val).lower()
                        if "pagad" in val_str or "al dia" in val_str or "al día" in val_str:
                            return "🟢 Pagado"
                        elif "mora" in val_str or "atras" in val_str:
                            return "🔴 En Mora"
                        elif "pendiente" in val_str or "curso" in val_str:
                            return "🟡 Pendiente"
                        return val

                    if "Estado de Pago" in tabla_mostrar.columns:
                        tabla_mostrar["Estado de Pago"] = tabla_mostrar["Estado de Pago"].apply(formato_estado_badge)

                    st.dataframe(
                        tabla_mostrar.style.format({
                            "Intereses": "${:,.0f}",
                            "Capital": "${:,.0f}",
                            "Saldo": "${:,.0f}"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("No hay registros de plan de pagos programado.")
        except Exception as e:
            st.error(f"Error al procesar la información: {e}")

    # =========================================================
    # SIMULADOR DE CRÉDITO
    # =========================================================
    elif st.session_state["pantalla"] == "simulador":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">🧮 Simulador de Crédito FEDESO</h3>', unsafe_allow_html=True)
        tasa_display = f"{TASA_MENSUAL_DEFAULT * 100:.2f}% M.V."

        st.markdown(f"""
        <div class="card" style="background-color: #eff6ff; border-color: #bfdbfe;">
            <span style="color: #1e40af; font-size: 1rem;">💡 <strong>CALCULADORA DE CUOTAS:</strong> Diseña tu plan de crédito ideal. Tasa de interés mensual aplicada: <strong>{tasa_display}</strong></span>
        </div>
        """, unsafe_allow_html=True)

        col_monto, col_plazo = st.columns(2)
        with col_monto:
            monto_sim = st.number_input(
                "Monto del préstamo ($)", min_value=100000, max_value=100000000, value=5000000, step=500000, format="%d"
            )
        with col_plazo:
            plazo_sim = st.number_input(
                "Plazo deseado (Meses)", min_value=1, max_value=120, value=24, step=1
            )

        i = TASA_MENSUAL_DEFAULT
        n = int(plazo_sim)
        P = float(monto_sim)

        if i > 0:
            factor = (1 + i)**n
            cuota_exacta = P * (i * factor) / (factor - 1)
        else:
            cuota_exacta = P / n

        cuota_sim = round(cuota_exacta)
        fecha_inicio = dt.now()
        fecha_fin = fecha_inicio + relativedelta(months=n)
        meses_esp = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha_fin_str = f"{meses_esp[fecha_fin.month - 1]} de {fecha_fin.year}"

        st.markdown(f"""
        <div class="card" style="background-color: #f8fafc; border-left: 5px solid #2563eb;">
            <h4 style="margin-top:0; color:#1e3a8a; font-weight:700; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">📊 RESULTADO DE LA SIMULACIÓN</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 12px;">
                <div class="metric-container">
                    <span class="metric-label">Cuota Mensual Estimada</span>
                    <span class="metric-value" style="color:#2563eb; font-size: 1.5rem;">${cuota_sim:,.0f}</span>
                </div>
                <div class="metric-container">
                    <span class="metric-label">Fecha de Finalización</span>
                    <span class="metric-value" style="font-size: 1.15rem;">{fecha_fin_str}</span>
                </div>
                <div class="metric-container">
                    <span class="metric-label">Total a Pagar Estimado</span>
                    <span class="metric-value">${cuota_sim * n:,.0f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<h4 style="color:#1e3a8a; margin-top:20px; margin-bottom:10px;">📅 PROYECCIÓN PASO A PASO</h4>', unsafe_allow_html=True)
        
        saldo = P
        cronograma = []

        for cuota_n in range(1, n + 1):
            fecha_cuota = fecha_inicio + relativedelta(months=cuota_n)
            mes_txt = f"{meses_esp[fecha_cuota.month - 1][:3]}-{str(fecha_cuota.year)[2:]}"
            interes_cuota = round(saldo * i)

            if cuota_n == n:
                capital_cuota = round(saldo)
                cuota_aplicada = capital_cuota + interes_cuota
                saldo = 0.0
            else:
                capital_cuota = cuota_sim - interes_cuota
                saldo -= capital_cuota
                cuota_aplicada = cuota_sim

            cronograma.append({
                "Nº": cuota_n,
                "Mes/Año": mes_txt,
                "Cuota Fija": cuota_aplicada,
                "Intereses": interes_cuota,
                "Capital": capital_cuota,
                "Saldo Restante": max(0.0, saldo)
            })

        df_cronograma = pd.DataFrame(cronograma)
        st.dataframe(
            df_cronograma.style.format({
                "Cuota Fija": "${:,.0f}",
                "Intereses": "${:,.0f}",
                "Capital": "${:,.0f}",
                "Saldo Restante": "${:,.0f}"
            }),
            use_container_width=True,
            hide_index=True
        )
        st.write("")
        st.link_button("📝 Solicitar este Crédito", FORM_URL, use_container_width=True)

    # =========================================================
    # PANEL DE ADMINISTRACIÓN
    # =========================================================
    elif st.session_state["pantalla"] == "admin" and st.session_state["rol"] == "admin":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">🛠️ Panel de Administración FEDESO</h3>', unsafe_allow_html=True)
        
        tab_user, tab_prestamo, tab_cuota = st.tabs(["👤 Crear Usuario", "💵 Registrar Préstamo", "📅 Registrar Pago / Cuota"])

        # TAB 1: CREAR USUARIOS
        with tab_user:
            st.subheader("Registrar Nuevo Usuario")
            with st.form("form_crear_usuario"):
                col1, col2 = st.columns(2)
                with col1:
                    new_user = st.text_input("Usuario (Cédula o ID)").strip().lower()
                    new_nombre = st.text_input("Nombre Completo").strip()
                with col2:
                    new_pass = st.text_input("Contraseña").strip()
                    new_rol = st.selectbox("Rol", ["asociado", "admin"])
                
                btn_crear_u = st.form_submit_button("Guardar Usuario en Google Sheets", use_container_width=True)

                if btn_crear_u:
                    if new_user and new_pass and new_nombre:
                        fila = [new_user, new_pass, new_nombre, new_rol]
                        if agregar_fila_sheet("Usuarios", fila):
                            st.success(f"✅ Usuario **{new_user}** registrado con éxito.")
                    else:
                        st.warning("Por favor complete todos los campos.")

        # TAB 2: REGISTRAR PRÉSTAMO
        with tab_prestamo:
            st.subheader("Asignar Préstamo a Asociado")
            with st.form("form_crear_prestamo"):
                user_p = st.text_input("Usuario del Asociado").strip().lower()
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    monto_p = st.number_input("Monto del Préstamo ($)", value=5000000, step=500000)
                with col_p2:
                    plazo_p = st.number_input("Plazo en Meses", value=24, step=1)
                with col_p3:
                    fecha_inicio_p = st.date_input("Fecha de Primera Cuota", value=dt.now().date())

                i_p = TASA_MENSUAL_DEFAULT
                n_p = int(plazo_p)
                P_p = float(monto_p)
                
                if i_p > 0 and n_p > 0:
                    factor_p = (1 + i_p)**n_p
                    cuota_calc = round(P_p * (i_p * factor_p) / (factor_p - 1))
                else:
                    cuota_calc = round(P_p / max(1, n_p))

                st.info(f"Cuota mensual calculada: **${cuota_calc:,.0f}** | Se generarán **{n_p + 1} filas** (Cuota 0 de desembolso + {n_p} cuotas).")

                btn_crear_p = st.form_submit_button("Guardar Préstamo y Generar Amortización", use_container_width=True)

                if btn_crear_p:
                    if user_p:
                        with st.spinner("Guardando préstamo y generando plan de pagos completo..."):
                            fila_resumen = [user_p, str(monto_p), str(plazo_p), f"{TASA_MENSUAL_DEFAULT:.7f}", str(cuota_calc)]
                            exito_resumen = agregar_fila_sheet("Resumen", fila_resumen)

                            filas_amortizacion = []
                            filas_amortizacion.append([
                                user_p, "0", "", "$0", "$0", f"${P_p:,.0f}", "Pendiente"
                            ])

                            fecha_base = datetime.date(fecha_inicio_p.year, fecha_inicio_p.month, 1)
                            meses_cortos = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

                            saldo_acc = P_p
                            for idx_c in range(1, n_p + 1):
                                f_cuota = fecha_base + relativedelta(months=idx_c - 1)
                                mes_txt_c = f"{meses_cortos[f_cuota.month - 1]}-{str(f_cuota.year)[2:]}"
                                
                                interes_c = round(saldo_acc * i_p)
                                
                                if idx_c == n_p:
                                    capital_c = round(saldo_acc)
                                    saldo_acc = 0.0
                                else:
                                    capital_c = cuota_calc - interes_c
                                    saldo_acc -= capital_c

                                filas_amortizacion.append([
                                    user_p,
                                    str(idx_c),
                                    mes_txt_c,
                                    f"${interes_c:,.0f}",
                                    f"${capital_c:,.0f}",
                                    f"${max(0.0, saldo_acc):,.0f}",
                                    "Pendiente"
                                ])

                            exito_amort = agregar_filas_sheet("Amortizacion", filas_amortizacion)

                            if exito_resumen and exito_amort:
                                st.success(f"🎉 ¡Préstamo registrado exitosamente! Se han guardado las {len(filas_amortizacion)} cuotas de **{user_p}** en Google Sheets.")
                    else:
                        st.warning("Por favor ingrese el usuario del asociado.")

        # TAB 3: REGISTRAR CUOTAS INDIVIDUALES
        with tab_cuota:
            st.subheader("Registrar / Modificar Cuota Individual")
            with st.form("form_crear_cuota"):
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    user_c = st.text_input("Usuario").strip().lower()
                    num_cuota = st.number_input("Número de Cuota", min_value=1, value=1)
                with col_c2:
                    mes_c = st.text_input("Mes/Año (Ej: sep-26)", value="sep-26").strip()
                    estado_c = st.selectbox("Estado", ["Pagado", "Pendiente", "En Mora"])
                with col_c3:
                    interes_c = st.number_input("Intereses ($)", value=0)
                    capital_c = st.number_input("Capital ($)", value=0)
                    saldo_c = st.number_input("Saldo Restante ($)", value=0)

                btn_crear_c = st.form_submit_button("Guardar Cuota en Google Sheets", use_container_width=True)

                if btn_crear_c:
                    if user_c:
                        fila = [user_c, str(num_cuota), mes_c, f"${interes_c:,.0f}", f"${capital_c:,.0f}", f"${saldo_c:,.0f}", estado_c]
                        if agregar_fila_sheet("Amortizacion", fila):
                            st.success(f"✅ Cuota #{num_cuota} guardada para **{user_c}**.")
                    else:
                        st.warning("Ingrese el usuario del asociado.")
