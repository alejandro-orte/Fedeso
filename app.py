import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    page_title="FEDESO - Estado de Cuenta",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

SHEET_ID = "1SvdJ5Y_Rz9oH-fInaV-LIn1yMvdM2wN3_qBwL3P3-k8" # ID de tu Google Sheet
TASA_MENSUAL_DEFAULT = 0.007 # 0.70% M.V.

# =========================================================
# ESTILOS CSS PERSONALIZADOS
# =========================================================
st.markdown("""
<style>
    /* Estilos globales */
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
    }
    
    /* Títulos */
    .dashboard-title {
        color: #ffffff;
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }
    
    .section-header-title {
        color: #ffffff;
        font-size: 20px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* Tarjetas principales estilo Softr */
    .softr-card {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        color: #1e293b;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }

    .card-title {
        font-size: 16px;
        font-weight: 700;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .card-user-badge {
        background-color: #f1f5f9;
        color: #334155;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }

    /* Cuadrícula de métricas */
    .metrics-grid-3 {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
    }

    .metric-item-label {
        font-size: 12px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .metric-item-val {
        font-size: 22px;
        font-weight: 800;
        color: #0f172a;
    }

    /* Badges de estado */
    .status-tag-green {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 700;
        display: inline-block;
    }

    /* Ajustes generales de Streamlit */
    div[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNCIONES DE APOYO Y CARGA DE DATOS
# =========================================================
def limpiar_numero(val) -> float:
    """ Convierte texto formateado ($1,000.00 o $1.000,00) a float puro. """
    if pd.isna(val) or val is None:
        return 0.0
    val_str = str(val).strip()
    if not val_str:
        return 0.0
    # Remover símbolos de moneda y espacios
    val_str = re.sub(r"[^\d,\.-]", "", val_str)
    
    # Manejo de separadores
    if "," in val_str and "." in val_str:
        if val_str.rfind(".") > val_str.rfind(","):
            val_str = val_str.replace(",", "")
        else:
            val_str = val_str.replace(".", "").replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")
        
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def normalizar_texto(series: pd.Series, minusculas: bool = True) -> pd.Series:
    """ Limpia espacios, tildes y caracteres invisibles en series de pandas. """
    s = series.astype(str).str.replace('\xa0', '').str.strip()
    if minusculas:
        s = s.str.lower()
    return s

@st.cache_data(ttl=1, show_spinner=False)
def cargar_pestana(nombre_pestana: str) -> pd.DataFrame:
    """ Lee una pestaña del Google Sheet público vía exportación CSV. """
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    df = pd.read_csv(url, dtype=str)
    df.columns = [str(col).replace('\xa0', '').strip().lower() for col in df.columns]
    return df

# =========================================================
# GESTIÓN DE SESIÓN Y AUTENTICACIÓN
# =========================================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""
if "nombre" not in st.session_state:
    st.session_state["nombre"] = ""
if "pantalla" not in st.session_state:
    st.session_state["pantalla"] = "dashboard"

# --- PANTALLA DE LOGIN ---
if not st.session_state["autenticado"]:
    st.markdown('<div class="dashboard-title">🏦 Portal de Asociados FEDESO</div>', unsafe_allow_html=True)
    
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        st.markdown("""
        <div class="softr-card">
            <h3 style="text-align: center; color: #0f172a; margin-bottom: 20px;">Iniciar Sesión</h3>
        """, unsafe_allow_html=True)
        
        usuario_input = st.text_input("Usuario / Cédula")
        clave_input = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", use_container_width=True, type="primary"):
            if usuario_input and clave_input:
                try:
                    df_users = cargar_pestana("Usuarios")
                    if "usuario" in df_users.columns and "clave" in df_users.columns:
                        df_users["u_clean"] = normalizar_texto(df_users["usuario"], minusculas=True)
                        u_key = normalizar_texto(pd.Series([usuario_input])).iloc[0]
                        
                        user_match = df_users[(df_users["u_clean"] == u_key) & (df_users["clave"].astype(str).str.strip() == clave_input.strip())]
                        
                        if not user_match.empty:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario"] = usuario_input.strip()
                            nombre_val = user_match.iloc[0].get("nombre", usuario_input.strip())
                            st.session_state["nombre"] = str(nombre_val).strip()
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")
                    else:
                        st.error("Error en la estructura de la pestaña Usuarios.")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
            else:
                st.warning("Por favor ingrese usuario y contraseña.")
                
        st.markdown("</div>", unsafe_allow_html=True)

# --- APLICACIÓN PRINCIPAL (AUTENTICADO) ---
else:
    # MENÚ LATERAL (SIDEBAR)
    with st.sidebar:
        st.markdown(f"### 👋 Hola, {st.session_state['nombre']}")
        st.markdown("---")
        
        if st.button("📊 Mi Estado de Cuenta", use_container_width=True):
            st.session_state["pantalla"] = "dashboard"
            st.rerun()
            
        if st.button("🧮 Simulador de Crédito", use_container_width=True):
            st.session_state["pantalla"] = "simulador"
            st.rerun()
            
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = ""
            st.session_state["nombre"] = ""
            st.rerun()

    # ---------------------------------------------------------
    # OPCIÓN A: DASHBOARD / ESTADO DE CUENTA
    # ---------------------------------------------------------
    if st.session_state["pantalla"] == "dashboard":
        st.markdown('<div class="dashboard-title">Mi Estado de Cuenta FEDESO</div>', unsafe_allow_html=True)

        usuario_key = normalizar_texto(pd.Series([st.session_state["usuario"]])).iloc[0]

        try:
            with st.spinner("Cargando tu información..."):
                cargar_pestana.clear()
                df_resumen = cargar_pestana("Resumen")
                df_amort = cargar_pestana("Amortizacion")

                num_pagadas = 0
                total_cuotas = 0
                estado_proxima_str = "N/A"
                saldo_pendiente_est = 0.0
                porcentaje_progreso = 0.0
                amort_user = pd.DataFrame()

                if "usuario" in df_amort.columns:
                    df_amort["u_clean"] = normalizar_texto(df_amort["usuario"], minusculas=True)
                    amort_user = df_amort[df_amort["u_clean"] == usuario_key].copy()

                    if not amort_user.empty:
                        for col in ["intereses", "capital", "saldo"]:
                            if col in amort_user.columns:
                                amort_user[col] = amort_user[col].apply(limpiar_numero)

                        if "estado" not in amort_user.columns:
                            amort_user["estado"] = "Pendiente"
                        else:
                            amort_user["estado"] = amort_user["estado"].fillna("Pendiente").astype(str).str.strip()

                        if "cuota_num" in amort_user.columns:
                            amort_user["cuota_num_clean"] = amort_user["cuota_num"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
                            amort_cuotas = amort_user[amort_user["cuota_num_clean"] != "0"]
                        else:
                            amort_cuotas = amort_user.copy()

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
                            num_cuota_actual = proxima_cuota.iloc[0].get("cuota_num_clean", "N/A")
                            estado_proxima_str = f"Cuota #{num_cuota_actual} ({mes_actual})"
                            saldo_pendiente_est = proxima_cuota.iloc[0].get("saldo", 0.0)
                        else:
                            estado_proxima_str = "🎉 Completado"
                            saldo_pendiente_est = 0.0

                        if total_cuotas > 0:
                            porcentaje_progreso = min(1.0, num_pagadas / total_cuotas)

                # --- TARJETA 1: RESUMEN DEL PRÉSTAMO ---
                if "usuario" in df_resumen.columns:
                    df_resumen["u_clean"] = normalizar_texto(df_resumen["usuario"], minusculas=True)
                    resumen_user = df_resumen[df_resumen["u_clean"] == usuario_key]

                    if not resumen_user.empty:
                        monto = limpiar_numero(resumen_user["monto"].iloc[0])
                        plazo = int(limpiar_numero(resumen_user["plazo"].iloc[0]))
                        tasa_raw = limpiar_numero(resumen_user["tasa_mv"].iloc[0])
                        cuota = limpiar_numero(resumen_user["cuota"].iloc[0])

                        # AJUSTE AUTOMÁTICO DE TASA (0.007 -> 0.70%)
                        if tasa_raw >= 1.0:
                            tasa = tasa_raw / 1000
                        elif tasa_raw >= 0.05:
                            tasa = tasa_raw / 100
                        else:
                            tasa = tasa_raw

                        tasa_fmt = f"{tasa * 100:.2f}%"
                        tasa_anual_fmt = f"{(tasa * 12) * 100:.2f}%"

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
                                    <div class="metric-item-val"><span class="status-tag-green">🟢 Al día</span></div>
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
                    <div class="progress-section" style="margin-top: 20px;">
                        <div class="progress-header" style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span class="progress-title-text" style="font-weight: 700; color: #0f172a;">Progreso Actual de Amortización</span>
                            <span class="progress-badge" style="font-weight: 800; color: #2563eb;">{pct_val:.1f}% Pagado</span>
                        </div>
                        <div class="progress-track" style="background-color: #e2e8f0; height: 12px; border-radius: 6px; overflow: hidden;">
                            <div class="progress-fill" style="width: {pct_val:.1f}%; background-color: #2563eb; height: 100%;"></div>
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
                        val_str = str(val).lower().strip()
                        if "pagad" in val_str or "al dia" in val_str or "al día" in val_str:
                            return "🟢 Pagado"
                        elif "curso" in val_str:
                            return "🔵 En curso"
                        elif "pendiente" in val_str or val_str in ["nan", "", "none"]:
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
                    st.warning(f"No se encontraron registros de amortización para el usuario '{usuario_key}'.")

        except Exception as e:
            st.error(f"Error al procesar la información: {e}")

    # ---------------------------------------------------------
    # OPCIÓN B: SIMULADOR DE CRÉDITO
    # ---------------------------------------------------------
    elif st.session_state["pantalla"] == "simulador":
        st.markdown('<div class="dashboard-title">🧮 Simulador de Crédito FEDESO</div>', unsafe_allow_html=True)

        tasa_display = f"{TASA_MENSUAL_DEFAULT * 100:.2f}% M.V."

        st.markdown(f"""
        <div class="softr-card">
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
                value=12, 
                step=1
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # Cálculo matemático exacto de la cuota
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
        total_pagar = cuota_sim * n

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
                    <div class="metric-item-val">${total_pagar:,.0f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
