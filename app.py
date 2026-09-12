import streamlit as st
import pandas as pd
import base64
import os
import datetime
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

# =========================================================
# CONFIGURACIÓN Y RECURSOS
# =========================================================
SHEET_ID = "12A0vnk-mUz2PaQpBmXnOPWtjzvOr7CXpUHLMn9ioLNQ"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdBFMIqAXxKNis9O29AbqPheXlfZqUdsUlUolERBICgTwWEsw/viewform"

TASA_MENSUAL_DEFAULT = 0.00697686  # 0.7% Mensual Vencido

MESES_MAP = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}

def parsear_fecha_flexible(texto):
    """Convierte libremente strings como 'oct-26', '10/2026', 'octubre 2026', '2026-10-15' a fecha de inicio de mes."""
    if pd.isna(texto) or not str(texto).strip():
        return None
    
    val = str(texto).strip().lower()
    for sep in ['/', '.', ' ']:
        val = val.replace(sep, '-')
    
    parts = [p for p in val.split('-') if p]
    
    # Intento 1: Reconocimiento por nombre de mes (ej: 'oct-26', '15-oct-2026', 'octubre-2026')
    if len(parts) >= 2:
        mes_cand = parts[0]
        anio_cand = parts[-1]
        if mes_cand in MESES_MAP and anio_cand.isdigit():
            m = MESES_MAP[mes_cand]
            y = int(anio_cand) if len(anio_cand) == 4 else 2000 + int(anio_cand)
            return datetime.date(y, m, 1)
        elif len(parts) >= 3 and parts[1] in MESES_MAP and anio_cand.isdigit():
            m = MESES_MAP[parts[1]]
            y = int(anio_cand) if len(anio_cand) == 4 else 2000 + int(anio_cand)
            return datetime.date(y, m, 1)

    # Intento 2: Parseo estándar numérico de fecha
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

st.set_page_config(
    page_title="FEDESO - Mi Estado de Cuenta",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# ESTILOS CSS - INTERFAZ LIMPIA Y MODERNA
# =========================================================
st.markdown("""
<style>
    /* Estructura general de tarjetas */
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 22px;
        border: 1px solid #e5e7eb;
    }
    
    /* Indicadores numéricos */
    .metric-container {
        display: flex;
        flex-direction: column;
    }
    .metric-label {
        font-size: 0.80rem;
        color: #6b7280;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.30rem;
        font-weight: 700;
        color: #111827;
    }

    /* Badges de Estado */
    .status-tag-green {
        display: inline-block;
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .status-tag-yellow {
        display: inline-block;
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .status-tag-red {
        display: inline-block;
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 700;
    }

    /* Header principal */
    .header-box {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white;
        padding: 18px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 10px rgba(30, 58, 138, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNCIONES AUXILIARES DE DATOS
# =========================================================
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
# LOGIN DE USUARIOS
# =========================================================
if not st.session_state["autenticado"]:
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.write("")
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
                <img src="{LOGO_URL}" width="140"><br><br>
                <div style="background-color: #f3f4f6; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
                    <span style="font-size: 0.80rem; color: #6b7280;">Bienvenido(a)</span><br>
                    <strong style="color: #111827; font-size: 1rem;">👤 {st.session_state['nombre']}</strong>
                </div>
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
            "📝 Solicitud de Crédito", FORM_URL, use_container_width=True
        )
        st.divider()
        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True, key="btn_logout"):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = ""
            st.session_state["nombre"] = ""
            st.session_state["pantalla"] = "dashboard"
            st.rerun()

    st.markdown(
        f"""
        <div class="header-box" style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin:0; color:white; font-size: 1.5rem; font-weight:700;">FEDESO</h2>
                <span style="font-size: 0.9rem; opacity: 0.9;">Fondo Empresarial de Solidaridad</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.85rem; opacity: 0.8;">Portal de Asociados</span>
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

                    # Excluir la cuota 0
                    amort_cuotas = amort_user[
                        ~amort_user["cuota_num"].astype(str).str.strip().isin(["0", "0.0"])
                    ].copy()
                    total_cuotas = len(amort_cuotas)

                    # Filtrar pagadas
                    estados_limpios = amort_cuotas["estado"].astype(str).str.lower().str.strip()
                    cuotas_pagadas_df = amort_cuotas[estados_limpios.isin(["pagado", "pagada", "al dia", "al día"])]
                    num_pagadas = len(cuotas_pagadas_df)

                    proxima_cuota = amort_cuotas[~estados_limpios.isin(["pagado", "pagada", "al dia", "al día"])]
                    
                    if not proxima_cuota.empty:
                        mes_proximo = proxima_cuota.iloc[0].get("mes_año", "N/A")
                        num_cuota_actual = proxima_cuota.iloc[0].get("cuota_num", "N/A")
                        estado_proxima_str = f"Cuota #{num_cuota_actual} ({mes_proximo})"
                        saldo_pendiente_est = proxima_cuota.iloc[0].get("saldo", 0.0)
                    else:
                        estado_proxima_str = "🎉 Completado"
                        saldo_pendiente_est = 0.0

                    if total_cuotas > 0:
                        porcentaje_progreso = min(1.0, num_pagadas / total_cuotas)

                    # Evaluación dinámica del estado del crédito
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

                # --- TARJETA 1: RESUMEN DEL PRÉSTAMO ---
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
                                <span style="font-size: 0.85rem; color:#6b7280;">Asociado: <strong>{st.session_state['nombre']}</strong></span>
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

                # --- TARJETA 2: ESTADO DE PAGOS Y PROGRESO ---
                pct_val = porcentaje_progreso * 100
                st.markdown(f"""
                <div class="card">
                    <h4 style="margin-top:0; color:#1e3a8a; font-weight:700; border-bottom: 1px solid #e5e7eb; padding-bottom: 12px; margin-bottom: 16px;">
                        📊 ESTADO DE PAGOS Y PROGRESO
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px;">
                        <div class="metric-container">
                            <span class="metric-label">Progreso de Pago</span>
                            <span class="metric-value">{num_pagadas} <span style="font-size:0.9rem; font-weight:normal; color:#6b7280;">de {total_cuotas} cuotas</span></span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Próximo Mes a Pagar</span>
                            <span class="metric-value" style="font-size: 1.1rem; color: #b45309;">{estado_proxima_str}</span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Saldo Pendiente Estimado</span>
                            <span class="metric-value">${saldo_pendiente_est:,.0f}</span>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #6b7280; font-weight: 600; margin-bottom: 6px;">
                            <span>Progreso Actual de Amortización</span>
                            <span>{pct_val:.1f}% Pagado</span>
                        </div>
                        <div style="background-color: #e5e7eb; border-radius: 10px; height: 10px; width: 100%; overflow: hidden;">
                            <div style="background-color: #2563eb; width: {pct_val}%; height: 100%; border-radius: 10px;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # --- TARJETA 3: TABLA PLAN DE PAGOS ---
                if not amort_user.empty:
                    st.markdown('<h4 style="color:#1e3a8a; margin-top:25px; margin-bottom:10px;">📅 PLAN DE PAGOS (AMORTIZACIONES)</h4>', unsafe_allow_html=True)
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
    # SIMULADOR DE CRÉDITO (AMORTIZACIÓN EXACTA)
    # =========================================================
    elif st.session_state["pantalla"] == "simulador":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">🧮 Simulador de Crédito FEDESO</h3>', unsafe_allow_html=True)
        tasa_display = f"{TASA_MENSUAL_DEFAULT * 100:.2f}% M.V."

        st.markdown(f"""
        <div class="card" style="background-color: #eff6ff; border-color: #bfdbfe;">
            <span style="color: #1e40af; font-size: 0.95rem;">💡 <strong>CALCULADORA DE CUOTAS:</strong> Diseña tu plan de crédito ideal. Tasa de interés mensual aplicada: <strong>{tasa_display}</strong></span>
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

        # Cálculo exacto de amortización bajo sistema francés
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
        <div class="card" style="background-color: #f8fafc; border-left: 4px solid #2563eb;">
            <h4 style="margin-top:0; color:#1e3a8a; font-weight:700; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">📊 RESULTADO DE LA SIMULACIÓN</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 12px;">
                <div class="metric-container">
                    <span class="metric-label">Cuota Mensual Estimada</span>
                    <span class="metric-value" style="color:#2563eb; font-size: 1.4rem;">${cuota_sim:,.0f}</span>
                </div>
                <div class="metric-container">
                    <span class="metric-label">Fecha de Finalización</span>
                    <span class="metric-value" style="font-size: 1.1rem;">{fecha_fin_str}</span>
                </div>
                <div class="metric-container">
                    <span class="metric-label">Total a Pagar Estimado</span>
                    <span class="metric-value">${cuota_sim * n:,.0f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<h4 style="color:#1e3a8a; margin-top:20px; margin-bottom:10px;">📅 PROYECCIÓN PASO A PASO</h4>', unsafe_allow_html=True)
        
        # Generación paso a paso de la tabla de amortización con cuadre exacto de última cuota
        saldo = P
        cronograma = []

        for cuota_n in range(1, n + 1):
            fecha_cuota = fecha_inicio + relativedelta(months=cuota_n)
            mes_txt = f"{meses_esp[fecha_cuota.month - 1][:3]}-{str(fecha_cuota.year)[2:]}"
            interes_cuota = round(saldo * i)

            if cuota_n == n:
                # Cierre exacto para garantización de Saldo $0
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
