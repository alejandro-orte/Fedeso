import streamlit as st
import pandas as pd
import base64
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# =========================================================
# CONFIGURACIÓN Y RECURSOS
# =========================================================
SHEET_ID = "12A0vnk-mUz2PaQpBmXnOPWtjzvOr7CXpUHLMn9ioLNQ"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdBFMIqAXxKNis9O29AbqPheXlfZqUdsUlUolERBICgTwWEsw/viewform"

# Tasa de interés mensual predeterminada (0.007% M.V.)
TASA_MENSUAL_DEFAULT = 0.00007

def get_image_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return "https://raw.githubusercontent.com/alejandro-orte/Fedeso/main/fedeso%20imagen%20web.png"

LOGO_URL = get_image_base64("fedeso imagen web.png")

st.set_page_config(
    page_title="FEDESO - Mi Estado de Cuenta",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILOS CSS PERSONALIZADOS Y MEJORAS DE VISUALIZACIÓN
# =========================================================
st.markdown("""
    <style>
    /* Fondo oscuro principal */
    .stApp { 
        background: linear-gradient(135deg, #0d0722 0%, #170e38 50%, #1f1147 100%) !important; 
    }
    
    #MainMenu, header, footer {visibility: hidden;}

    /* ESTILO BARRA LATERAL IZQUIERDA (SIDEBAR) */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }

    .sidebar-box {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 24px 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.4);
        margin-bottom: 20px;
        text-align: center;
    }

    .sidebar-user-title {
        color: #0f172a;
        font-weight: 800;
        font-size: 1.1rem;
        margin-bottom: 4px;
    }

    .sidebar-user-sub {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 15px;
    }

    /* Título principal centrado */
    .dashboard-title {
        color: #ffffff;
        font-family: 'Inter', -apple-system, sans-serif;
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 25px;
        text-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    /* Subtítulo de sección */
    .section-header-title {
        color: #ffffff !important;
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
        margin-top: 25px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }

    /* Tarjetas blancas principales */
    .softr-card {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 28px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.35);
        margin-bottom: 25px;
        color: #0f172a;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 14px;
        margin-bottom: 22px;
    }

    .card-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .card-user-badge {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1e293b;
        background: #f1f5f9;
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
    }

    .metrics-grid-3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 22px 35px;
    }

    .metric-item-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-item-val {
        font-size: 1.55rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }

    .status-tag-green {
        display: inline-block;
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 700;
    }

    .status-tag-red {
        display: inline-block;
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 700;
    }

    /* CAMPOS DE ENTRADA Y TABLA */
    div[data-testid="stNumberInput"] label {
        color: #0f172a !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        margin-bottom: 6px !important;
    }

    div[data-testid="stNumberInput"] input {
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        background-color: #f8fafc !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        height: 50px !important;
    }

    div[data-testid="stNumberInput"] input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2) !important;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.25);
    }

    div[data-testid="stDataFrame"] th {
        background-color: #1e293b !important;
        padding: 14px 16px !important;
    }

    div[data-testid="stDataFrame"] th p,
    div[data-testid="stDataFrame"] th span {
        color: #ffffff !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* Login */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 35px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }

    .login-logo-container {
        text-align: center;
        margin-bottom: 15px;
    }

    .login-logo-container img {
        width: 240px;
        height: 240px;
        object-fit: contain;
        border-radius: 50%;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
    }
    </style>
""", unsafe_allow_html=True)


# =========================================================
# FUNCIONES DE UTILIDAD Y CARGA DE DATOS
# =========================================================
def limpiar_numero(valor):
    if pd.isna(valor):
        return 0.0
    texto = str(valor).replace('$', '').replace(',', '').replace('%', '').strip()
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


@st.cache_data(ttl=60, show_spinner=False)
def cargar_usuarios() -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Usuarios"
    df = pd.read_csv(url, dtype=str)
    df.columns = [str(col).replace('\xa0', '').strip().lower() for col in df.columns]
    return df


@st.cache_data(ttl=300, show_spinner=False)
def cargar_pestana(nombre_pestana: str) -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    df = pd.read_csv(url, dtype=str)
    df.columns = [str(col).replace('\xa0', '').strip().lower() for col in df.columns]
    return df


if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nombre"] = ""

if "pantalla" not in st.session_state:
    st.session_state["pantalla"] = "dashboard"

# =========================================================
# 1. PANTALLA DE LOGIN
# =========================================================
if not st.session_state["autenticado"]:
    col_a, col_b, col_c = st.columns([1, 2, 1])

    with col_b:
        st.write("")
        st.write("")
        st.markdown(
            f"""
            <div class="login-logo-container">
                <img src="{LOGO_URL}"/>
            </div>
            """, 
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
                            df_users = cargar_usuarios()

                            if "usuario" not in df_users.columns or "contrasena" not in df_users.columns:
                                st.error("❌ Estructura de tabla no válida.")
                            else:
                                df_users["usuario"] = normalizar_texto(df_users["usuario"], minusculas=True)
                                df_users["contrasena"] = normalizar_texto(df_users["contrasena"], minusculas=False)

                                valido = df_users[
                                    (df_users["usuario"] == user_input) & 
                                    (df_users["contrasena"] == pass_input)
                                ]

                                if not valido.empty:
                                    st.session_state["autenticado"] = True
                                    st.session_state["usuario"] = user_input
                                    st.session_state["nombre"] = (
                                        valido["nombre"].iloc[0] if "nombre" in valido.columns else user_input
                                    )
                                    st.rerun()
                                else:
                                    st.error("Usuario o contraseña incorrectos.")
                        except Exception as e:
                            st.error(f"Error al conectar: {e}")

# =========================================================
# 2. PANTALLA INTERNA
# =========================================================
else:
    # BARRA LATERAL IZQUIERDA
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-box">
                <img src="{LOGO_URL}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 50%; margin-bottom: 12px; border: 2px solid #e2e8f0;"/>
                <div class="sidebar-user-title">👤 {st.session_state['nombre']}</div>
                <div class="sidebar-user-sub">Panel de Asociado</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        st.subheader("⚙️ Menú Principal")

        if st.button("📊 Mi Estado de Cuenta", use_container_width=True, key="btn_dashboard"):
            st.session_state["pantalla"] = "dashboard"
            st.rerun()

        if st.button("🧮 Simulador de Crédito", use_container_width=True, key="btn_simulador"):
            st.session_state["pantalla"] = "simulador"
            st.rerun()

        st.link_button(
            "📝 Solicitud de Crédito", 
            FORM_URL, 
            use_container_width=True
        )

        st.divider()

        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True, key="btn_logout"):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = ""
            st.session_state["nombre"] = ""
            st.session_state["pantalla"] = "dashboard"
            st.rerun()

    # ENCABEZADO SUPERIOR COMÚN
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 25px;">
            <img src="{LOGO_URL}" style="width: 90px; height: 90px; object-fit: cover; border-radius: 50%; border: 3px solid rgba(255, 255, 255, 0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.4);"/>
            <div>
                <span style="color: white; font-weight: 800; font-size: 2.2rem; letter-spacing: 0.5px; display: block; line-height: 1;">FEDESO</span>
                <span style="color: #cbd5e1; font-size: 1rem; font-weight: 500;">Fondo Empresarial de Solidaridad</span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # OPCIÓN A: DASHBOARD / ESTADO DE CUENTA
    # ---------------------------------------------------------
    if st.session_state["pantalla"] == "dashboard":
        st.markdown('<div class="dashboard-title">Mi Estado de Cuenta FEDESO</div>', unsafe_allow_html=True)

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
                proxima_cuota = pd.DataFrame()

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

                        amort_cuotas = amort_user[amort_user["cuota_num"].astype(str) != "0"]
                        total_cuotas = len(amort_cuotas)

                        cuotas_pagadas_df = amort_cuotas[
                            amort_cuotas["estado"].str.lower().isin(["pagado", "al dia", "al día"])
                        ]
                        num_pagadas = len(cuotas_pagadas_df)

                        proxima_cuota = amort_cuotas[
                            ~amort_cuotas["estado"].str.lower().isin(["pagado", "al dia", "al día"])
                        ]
                        if not proxima_cuota.empty:
                            mes_actual = proxima_cuota.iloc[0].get("mes_año", "N/A")
                            num_cuota_actual = proxima_cuota.iloc[0].get("cuota_num", "N/A")
                            estado_proxima_str = f"Cuota #{num_cuota_actual} ({mes_actual})"
                            saldo_pendiente_est = proxima_cuota.iloc[0].get("saldo", 0.0)
                        else:
                            estado_proxima_str = "🎉 Completado"
                            saldo_pendiente_est = 0.0

                        if total_cuotas > 0:
                            porcentaje_progreso = min(1.0, num_pagadas / total_cuotas)

                # --- TARJETA 1: RESUMEN DEL PRÉSTAMO ---
                if "usuario" in df_resumen.columns:
                    df_resumen["usuario"] = normalizar_texto(df_resumen["usuario"])
                    resumen_user = df_resumen[df_resumen["usuario"] == usuario_key]

                    if not resumen_user.empty:
                        monto = limpiar_numero(resumen_user["monto"].iloc[0])
                        plazo = int(limpiar_numero(resumen_user["plazo"].iloc[0]))
                        tasa_raw = limpiar_numero(resumen_user["tasa_mv"].iloc[0])
                        cuota = limpiar_numero(resumen_user["cuota"].iloc[0])

                        # CORRECCIÓN DE TASA:
                        # Si viene en decimal (ej. 0.00007 o 0.007) o en porcentaje (0.7)
                        if tasa_raw < 0.01:
                            tasa_porcentaje_mv = tasa_raw * 100
                        else:
                            tasa_porcentaje_mv = tasa_raw

                        tasa_fmt = f"{tasa_porcentaje_mv:.3f}%"
                        tasa_anual_fmt = f"{(tasa_porcentaje_mv * 12):.3f}%"

                        # CORRECCIÓN DE ESTADO DEL CRÉDITO DINÁMICO:
                        if estado_proxima_str != "🎉 Completado" and not proxima_cuota.empty:
                            estado_credito_html = '<span class="status-tag-red">🔴 Pendiente / Mora</span>'
                        else:
                            estado_credito_html = '<span class="status-tag-green">🟢 Al día</span>'

                        st.markdown(f"""
                        <div class="softr-card">
                            <div class="card-header">
                                <span class="card-title">📊 RESUMEN DE PRÉSTAMO</span>
                                <span class="card-user-badge">👤 {st.session_state['nombre']}</span>
                            </div>
                            <div class="metrics-grid-3">
                                <div>
                                    <div class="metric-item-label">Monto del Préstamo:</div>
                                    <div class="metric-item-val">${monto:,.0f}</div>
                                </div>
                                <div>
                                    <div class="metric-item-label">Plazo (Meses):</div>
                                    <div class="metric-item-val">{plazo} meses</div>
                                </div>
                                <div>
                                    <div class="metric-item-label">Tasa M.V.:</div>
                                    <div class="metric-item-val">{tasa_fmt}</div>
                                </div>
                                <div>
                                    <div class="metric-item-label">Cuota Mensual:</div>
                                    <div class="metric-item-val">${cuota:,.0f}</div>
                                </div>
                                <div>
                                    <div class="metric-item-label">Tasa Anual Estimada:</div>
                                    <div class="metric-item-val">{tasa_anual_fmt}</div>
                                </div>
                                <div>
                                    <div class="metric-item-label">Estado del Crédito:</div>
                                    <div class="metric-item-val">{estado_credito_html}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # --- TARJETA 2: ESTADO DE PAGOS Y PROGRESO ---
                pct_val = porcentaje_progreso * 100
                st.markdown(f"""
                <div class="softr-card">
                    <div class="card-header">
                        <span class="card-title">📊 ESTADO DE PAGOS Y PROGRESO</span>
                    </div>
                    <div class="metrics-grid-3">
                        <div>
                            <div class="metric-item-label">Progreso de Pago</div>
                            <div class="metric-item-val">{num_pagadas} de {total_cuotas} cuotas</div>
                        </div>
                        <div>
                            <div class="metric-item-label">Próximo Mes a Pagar</div>
                            <div class="metric-item-val">{estado_proxima_str}</div>
                        </div>
                        <div>
                            <div class="metric-item-label">Saldo Pendiente Estimado</div>
                            <div class="metric-item-val">${saldo_pendiente_est:,.0f}</div>
                        </div>
                    </div>
                    <div class="progress-section" style="margin-top:20px;">
                        <div class="progress-header" style="display:flex; justify-content:space-between; margin-bottom:8px;">
                            <span class="progress-title-text" style="font-weight:700; color:#0f172a;">Progreso Actual de Amortización</span>
                            <span class="progress-badge" style="font-weight:800; color:#2563eb;">{pct_val:.1f}% Pagado</span>
                        </div>
                        <div class="progress-track" style="background:#e2e8f0; height:12px; border-radius:6px; overflow:hidden;">
                            <div class="progress-fill" style="width: {pct_val:.1f}%; background:#2563eb; height:100%;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --- TARJETA 3: TABLA PLAN DE PAGOS (AMORTIZACIÓN) ---
                if not amort_user.empty:
                    st.markdown('<div class="section-header-title">📅 PLAN DE PAGOS (AMORTIZACIONES)</div>', unsafe_allow_html=True)

                    cols_existentes = [c for c in ["cuota_num", "mes_año", "estado", "intereses", "capital", "saldo"] if c in amort_user.columns]
                    tabla_mostrar = amort_user[cols_existentes].copy()

                    renombrar = {
                        "cuota_num": "Nº",
                        "mes_año": "Mes/Año",
                        "estado": "Estado de Pago",
                        "intereses": "Intereses",
                        "capital": "Capital",
                        "saldo": "Saldo"
                    }
                    tabla_mostrar = tabla_mostrar.rename(columns=renombrar)

                    def formato_estado_badge(val):
                        val_str = str(val).lower()
                        if "pagad" in val_str or "al dia" in val_str or "al día" in val_str:
                            return "🟢 Pagado"
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

    # ---------------------------------------------------------
    # OPCIÓN B: SIMULADOR DE CRÉDITO INTERACTIVO
    # ---------------------------------------------------------
    elif st.session_state["pantalla"] == "simulador":
        st.markdown('<div class="dashboard-title">🧮 Simulador de Crédito FEDESO</div>', unsafe_allow_html=True)

        tasa_display = "0.007% M.V."

        st.markdown(f"""
        <div class="softr-card" style="margin-bottom: 20px;">
            <div class="card-header" style="margin-bottom: 15px;">
                <span class="card-title">💡 CALCULADORA DE CUOTAS</span>
                <span class="card-user-badge">Tasa de interés: {tasa_display}</span>
            </div>
        """, unsafe_allow_html=True)

        col_monto, col_plazo = st.columns(2)

        with col_monto:
            monto_sim = st.number_input(
                "Monto del préstamo ($)", 
                min_value=100000, 
                max_value=100000000, 
                value=5000000, 
                step=500000, 
                format="%d"
            )

        with col_plazo:
            plazo_sim = st.number_input(
                "Plazo deseado (Meses)", 
                min_value=1, 
                max_value=120, 
                value=24, 
                step=1
            )

        st.markdown("</div>", unsafe_allow_html=True)

        i = TASA_MENSUAL_DEFAULT
        n = plazo_sim
        P = monto_sim

        if i > 0:
            cuota_exacta = P * (i * (1 + i)**n) / ((1 + i)**n - 1)
        else:
            cuota_exacta = P / n
        cuota_sim = round(cuota_exacta)

        fecha_inicio = datetime.now()
        fecha_fin = fecha_inicio + relativedelta(months=n)

        meses_esp = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha_fin_str = f"{meses_esp[fecha_fin.month - 1]} de {fecha_fin.year}"

        # Resultado de la simulación
        st.markdown(f"""
        <div class="softr-card">
            <div class="card-header">
                <span class="card-title">📊 RESULTADO DE LA SIMULACIÓN</span>
            </div>
            <div class="metrics-grid-3">
                <div>
                    <div class="metric-item-label">Cuota Mensual Estimada:</div>
                    <div class="metric-item-val" style="color: #2563eb;">${cuota_sim:,.0f}</div>
                </div>
                <div>
                    <div class="metric-item-label">Fecha de Finalización:</div>
                    <div class="metric-item-val">{fecha_fin_str}</div>
                </div>
                <div>
                    <div class="metric-item-label">Total a Pagar:</div>
                    <div class="metric-item-val">${cuota_sim * n:,.0f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabla proyectada ajustada
        st.markdown('<div class="section-header-title">📅 PROYECCIÓN PASO A PASO</div>', unsafe_allow_html=True)

        saldo = float(P)
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
        st.link_button("📝 Solicitar este Crédito Ahora", FORM_URL, use_container_width=True, type="primary")
