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
# CONFIGURACIÓN Y CONSTANTES
# =========================================================
SHEET_ID = "12A0vnk-mUz2PaQpBmXnOPWtjzvOr7CXpUHLMn9ioLNQ"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdBFMIqAXxKNis9O29AbqPheXlfZqUdsUlUolERBICgTwWEsw/viewform"

# Tasa exacta para $226,984 en $5.000.000 a 24 meses
TASA_MENSUAL_EXACTA = 0.00697686

MESES_MAP = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}

# =========================================================
# CONEXIÓN A GOOGLE SHEETS PARA ESCRITURA (gspread)
# =========================================================
def obtener_cliente_gspread():
    """Conecta con la API de Google Sheets mediante Secrets de Streamlit."""
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
    """Agrega una fila nueva al final de la pestaña especificada."""
    gc = obtener_cliente_gspread()
    if gc:
        try:
            sh = gc.open_by_key(SHEET_ID)
            worksheet = sh.worksheet(nombre_pestana)
            worksheet.append_row(fila)
            st.cache_data.clear() # Limpia caché para reflejar los datos inmediatamente
            return True
        except Exception as e:
            st.error(f"Error al escribir en Google Sheets: {e}")
            return False
    else:
        st.error("No se configuraron las credenciales de escritura en Google Sheets.")
        return False

# =========================================================
# FUNCIONES AUXILIARES DE CÁLCULO Y FORMATO
# =========================================================
def calcular_cuota_pago(tasa_mv: float, plazo: int, monto: float) -> int:
    if tasa_mv <= 0 or plazo <= 0:
        return round(monto / max(1, plazo))
    factor = (1 + tasa_mv) ** plazo
    cuota = monto * (tasa_mv * factor) / (factor - 1)
    return round(cuota)

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

@st.cache_data(ttl=10, show_spinner=False)
def cargar_pestana(nombre_pestana: str) -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    try:
        df = pd.read_csv(url, dtype=str)
        df.columns = [str(col).replace('\xa0', '').strip().lower() for col in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

def get_image_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return "https://raw.githubusercontent.com/alejandro-orte/Fedeso/main/fedeso%20imagen%20web.png"

LOGO_URL = get_image_base64("fedeso imagen web.png")

# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    page_title="FEDESO - Mi Estado de Cuenta",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Generales
st.markdown("""
<style>
    .stMetric {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar Estados en Session State
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
        st.markdown(
            f"""<div style="text-align: center;"><img src="{LOGO_URL}" width="180"></div>""",
            unsafe_allow_html=True
        )
        with st.form("login_form"):
            st.subheader("🔑 Iniciar Sesión")
            user_input = st.text_input("Usuario").strip().lower()
            pass_input = st.text_input("Contraseña", type="password").strip()
            submit = st.form_submit_button("Ingresar a mi Fondo", use_container_width=True)

            if submit:
                if not user_input or not pass_input:
                    st.warning("Por favor ingrese usuario y contraseña.")
                else:
                    with st.spinner("Verificando credenciales..."):
                        try:
                            df_users = cargar_pestana("Usuarios")
                            if df_users.empty or "usuario" not in df_users.columns or "contrasena" not in df_users.columns:
                                st.error("❌ Estructura de la tabla 'Usuarios' no válida o sin acceso.")
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
                            st.error(f"Error al conectar con la base de datos: {e}")

# =========================================================
# APLICACIÓN PRINCIPAL (SESIÓN INICIADA)
# =========================================================
else:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0;">
                <img src="{LOGO_URL}" width="140"><br><br>
                <div style="background-color: #f3f4f6; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
                    <span style="font-size: 0.80rem; color: #6b7280;">Bienvenido(a)</span><br>
                    <strong style="color: #111827; font-size: 1rem;">👤 {st.session_state['nombre']}</strong><br>
                    <small style="color: #2563eb; font-weight: 600;">Rol: {st.session_state['rol'].capitalize()}</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.subheader("⚙️ Menú Principal")
        if st.button("📊 Mi Estado de Cuenta", use_container_width=True):
            st.session_state["pantalla"] = "dashboard"
            st.rerun()
        if st.button("🧮 Simulador de Crédito", use_container_width=True):
            st.session_state["pantalla"] = "simulador"
            st.rerun()
        
        # Opción habilitada únicamente para ROL ADMIN
        if st.session_state["rol"] == "admin":
            st.divider()
            if st.button("🛠️ Panel de Administración", use_container_width=True):
                st.session_state["pantalla"] = "admin"
                st.rerun()
                
        st.divider()
        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = ""
            st.session_state["nombre"] = ""
            st.session_state["rol"] = "asociado"
            st.session_state["pantalla"] = "dashboard"
            st.rerun()

    # =========================================================
    # PANTALLA 1: DASHBOARD (ESTADO DE CUENTA COMPLETO)
    # =========================================================
    if st.session_state["pantalla"] == "dashboard":
        st.markdown('<h3 style="color:#1e3a8a; font-weight:700;">📊 Mi Estado de Cuenta FEDESO</h3>', unsafe_allow_html=True)
        usuario_actual = st.session_state["usuario"]

        # 1. Cargar Datos de Resumen
        df_resumen = cargar_pestana("Resumen")
        
        if not df_resumen.empty and "usuario" in df_resumen.columns:
            df_resumen["usuario"] = normalizar_texto(df_resumen["usuario"], minusculas=True)
            res_user = df_resumen[df_resumen["usuario"] == usuario_actual]

            if not res_user.empty:
                fila_p = res_user.iloc[0]
                
                monto_val = limpiar_numero(fila_p.get("monto", 0))
                plazo_val = int(limpiar_numero(fila_p.get("plazo", 0)))
                tasa_val = limpiar_numero(fila_p.get("tasa_mv", TASA_MENSUAL_EXACTA))
                cuota_val = limpiar_numero(fila_p.get("cuota", 0))

                if cuota_val == 0:
                    cuota_val = calcular_cuota_pago(tasa_val, plazo_val, monto_val)

                # Mostrar Tarjetas / Métricas Principales
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Monto Aprobado", f"${monto_val:,.0f}")
                with col2:
                    st.metric("Plazo Total", f"{plazo_val} Meses")
                with col3:
                    st.metric("Cuota Mensual", f"${cuota_val:,.0f}")
                with col4:
                    tasa_mostrar = tasa_val * 100 if tasa_val < 1 else tasa_val
                    st.metric("Tasa de Interés M.V.", f"{tasa_mostrar:.2f}%")

                st.markdown("<br>", unsafe_allow_html=True)

                # 2. Cargar Plan de Pagos / Amortización
                st.markdown('<h4 style="color:#1e3a8a;">📋 Plan de Pagos y Amortización</h4>', unsafe_allow_html=True)
                df_amort = cargar_pestana("Amortizacion")

                if not df_amort.empty and "usuario" in df_amort.columns:
                    df_amort["usuario"] = normalizar_texto(df_amort["usuario"], minusculas=True)
                    amort_user = df_amort[df_amort["usuario"] == usuario_actual].copy()

                    if not amort_user.empty:
                        # Crear versión limpia para mostrar en la tabla
                        tabla_mostrar = pd.DataFrame()
                        
                        if "cuota" in amort_user.columns:
                            tabla_mostrar["Cuota #"] = amort_user["cuota"]
                        if "mes" in amort_user.columns:
                            tabla_mostrar["Mes / Año"] = amort_user["mes"]
                        if "estado" in amort_user.columns:
                            tabla_mostrar["Estado"] = amort_user["estado"]
                        if "intereses" in amort_user.columns:
                            tabla_mostrar["Intereses"] = amort_user["intereses"].apply(lambda x: f"${limpiar_numero(x):,.0f}")
                        if "capital" in amort_user.columns:
                            tabla_mostrar["Capital"] = amort_user["capital"].apply(lambda x: f"${limpiar_numero(x):,.0f}")
                        if "saldo" in amort_user.columns:
                            tabla_mostrar["Saldo Restante"] = amort_user["saldo"].apply(lambda x: f"${limpiar_numero(x):,.0f}")

                        if tabla_mostrar.empty:
                            tabla_mostrar = amort_user.drop(columns=["usuario"], errors="ignore")

                        st.dataframe(tabla_mostrar, use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay registros de cuotas detalladas para este usuario aún.")
                else:
                    st.info("No se encontró información en la tabla de Amortización.")
            else:
                st.warning("⚠️ No se encontró un préstamo activo registrado para tu usuario.")
        else:
            st.error("No se pudo cargar la información general de créditos desde Google Sheets.")

    # =========================================================
    # PANTALLA 2: SIMULADOR DE CRÉDITO
    # =========================================================
    elif st.session_state["pantalla"] == "simulador":
        st.markdown('<h3 style="color:#1e3a8a; font-weight:700;">🧮 Simulador de Crédito FEDESO</h3>', unsafe_allow_html=True)
        st.write("Calcula la cuota aproximada para un nuevo crédito con la tasa preferencial.")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            monto_sim = st.number_input("Monto Solicitado ($)", value=5000000, step=500000, min_value=100000)
        with col_s2:
            plazo_sim = st.number_input("Plazo Deseado (Meses)", value=24, step=1, min_value=1)

        cuota_sim = calcular_cuota_pago(TASA_MENSUAL_EXACTA, int(plazo_sim), float(monto_sim))
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.success(f"💡 Para un crédito de **${monto_sim:,.0f}** a **{int(plazo_sim)} meses**, la cuota mensual estimada es: **${cuota_sim:,.0f}**")

    # =========================================================
    # PANTALLA 3: PANEL DE ADMINISTRACIÓN (SOLO ADMIN)
    # =========================================================
    elif st.session_state["pantalla"] == "admin" and st.session_state["rol"] == "admin":
        st.markdown('<h3 style="color:#1e3a8a; font-weight:700;">🛠️ Panel de Administración FEDESO</h3>', unsafe_allow_html=True)
        st.write("Gestiona la base de datos de usuarios, préstamos y pagos en Google Sheets.")

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

        # TAB 2: REGISTRAR PRÉSTAMO EN RESUMEN
        with tab_prestamo:
            st.subheader("Asignar Préstamo a Asociado")
            with st.form("form_crear_prestamo"):
                user_p = st.text_input("Usuario del Asociado").strip().lower()
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    monto_p = st.number_input("Monto del Préstamo ($)", value=5000000, step=500000)
                with col_p2:
                    plazo_p = st.number_input("Plazo en Meses", value=24, step=1)
                
                cuota_calc = calcular_cuota_pago(TASA_MENSUAL_EXACTA, int(plazo_p), float(monto_p))
                st.info(f"Cuota mensual calculada automáticamente: **${cuota_calc:,.0f}**")

                btn_crear_p = st.form_submit_button("Guardar Préstamo en Google Sheets", use_container_width=True)

                if btn_crear_p:
                    if user_p:
                        fila = [user_p, str(monto_p), str(plazo_p), f"{TASA_MENSUAL_EXACTA:.6f}", str(cuota_calc)]
                        if agregar_fila_sheet("Resumen", fila):
                            st.success(f"✅ Préstamo registrado para el usuario **{user_p}**.")
                    else:
                        st.warning("Ingrese el usuario del asociado.")

        # TAB 3: REGISTRAR CUOTAS EN AMORTIZACIÓN
        with tab_cuota:
            st.subheader("Registrar Cuota o Estado de Pago")
            with st.form("form_crear_cuota"):
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    user_c = st.text_input("Usuario").strip().lower()
                    num_cuota = st.number_input("Número de Cuota", min_value=1, value=1)
                with col_c2:
                    mes_c = st.text_input("Mes/Año (Ej: oct-26)", value="oct-26").strip()
                    estado_c = st.selectbox("Estado", ["Pagado", "Pendiente", "En Mora"])
                with col_c3:
                    interes_c = st.number_input("Intereses ($)", value=0)
                    capital_c = st.number_input("Capital ($)", value=0)
                    saldo_c = st.number_input("Saldo Restante ($)", value=0)

                btn_crear_c = st.form_submit_button("Guardar Cuota en Google Sheets", use_container_width=True)

                if btn_crear_c:
                    if user_c:
                        fila = [user_c, str(num_cuota), mes_c, estado_c, str(interes_c), str(capital_c), str(saldo_c)]
                        if agregar_fila_sheet("Amortizacion", fila):
                            st.success(f"✅ Cuota #{num_cuota} guardada para **{user_c}**.")
                    else:
                        st.warning("Ingrese el usuario del asociado.")
