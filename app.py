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
    /* Estilos globales y badges */
    .status-tag-green {
        display: inline-block;
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 700;
    }
    .status-tag-yellow {
        display: inline-block;
        background-color: #fef3c7;
        color: #b45309;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 700;
    }
    .status-tag-red {
        display: inline-block;
        background-color: #fee2e2;
        color: #dc2626;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.95rem;
        font-weight: 700;
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
# 2. PANTALLA INTERNA
# =========================================================
else:
    # BARRA LATERAL IZQUIERDA
    with st.sidebar:
        st.markdown(
            f"👤 **{st.session_state['nombre']}**\n\nPanel de Asociado",
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

    # ENCABEZADO SUPERIOR COMÚN
    st.markdown("FEDESO - Fondo Empresarial de Solidaridad")

    # ---------------------------------------------------------
    # OPCIÓN A: DASHBOARD / ESTADO DE CUENTA
    # ---------------------------------------------------------
    if st.session_state["pantalla"] == "dashboard":
        st.markdown("### Mi Estado de Cuenta FEDESO")
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

                    amort_cuotas = amort_user[amort_user["cuota_num"].astype(str) != "0"].copy()
                    total_cuotas = len(amort_cuotas)

                    # --- LÓGICA DE ESTADO DEL CRÉDITO POR MES ACTUAL ---
                    hoy = datetime.date.today()
                    mes_actual = hoy.month
                    anio_actual = hoy.year

                    # Convertir la columna de fechas a datetime si viene disponible (ej. mes_año o fecha_pago)
                    col_fecha = "fecha_pago" if "fecha_pago" in amort_cuotas.columns else ("mes_año" if "mes_año" in amort_cuotas.columns else None)
                    if col_fecha:
                        amort_cuotas["fecha_dt"] = pd.to_datetime(amort_cuotas[col_fecha], errors="coerce")
                        cuota_mes_actual = amort_cuotas[
                            (amort_cuotas["fecha_dt"].dt.month == mes_actual) & 
                            (amort_cuotas["fecha_dt"].dt.year == anio_actual)
                        ]
                    else:
                        cuota_mes_actual = pd.DataFrame()

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

                    # Determinar insignia de Estado de Crédito por Mes
                    if not cuota_mes_actual.empty:
                        est_mes = cuota_mes_actual["estado"].astype(str).str.lower().str.strip().iloc[0]
                        if est_mes in ["pagado", "pagada", "al dia", "al día"]:
                            badge_estado_credito = '<span class="status-tag-green">🟢 Al día</span>'
                        else:
                            badge_estado_credito = '<span class="status-tag-yellow">🟡 Pendiente</span>'
                    else:
                        todas_pagadas = estados_limpios.isin(["pagado", "pagada", "al dia", "al día"]).all()
                        if todas_pagadas and total_cuotas > 0:
                            badge_estado_credito = '<span class="status-tag-green">🟢 Finalizado</span>'
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

                        # Normalización de tasa (ej. 0.7 -> 0.7% o 0.007 -> 0.7%)
                        tasa_porcentaje_mv = tasa_raw / 100 if tasa_raw >= 1 else (tasa_raw * 100 if tasa_raw < 0.01 else tasa_raw)
                        tasa_fmt = f"{tasa_porcentaje_mv:.2f}%"
                        tasa_anual_fmt = f"{(tasa_porcentaje_mv * 12):.2f}%"

                        st.markdown(f"""
                        📊 RESUMEN DE PRÉSTAMO | 👤 {st.session_state['nombre']}

                        **Monto del Préstamo:** ${monto:,.0f}  
                        **Plazo (Meses):** {plazo} meses  
                        **Tasa M.V.:** {tasa_fmt}  
                        **Cuota Mensual:** ${cuota:,.0f}  
                        **Tasa Anual Estimada:** {tasa_anual_fmt}  
                        **Estado del Crédito:** {badge_estado_credito}
                        """, unsafe_allow_html=True)

                # --- TARJETA 2: ESTADO DE PAGOS Y PROGRESO ---
                pct_val = porcentaje_progreso * 100
                st.markdown(f"""
                📊 **ESTADO DE PAGOS Y PROGRESO**

                - **Progreso de Pago:** {num_pagadas} de {total_cuotas} cuotas
                - **Próximo Mes a Pagar:** {estado_proxima_str}
                - **Saldo Pendiente Estimado:** ${saldo_pendiente_est:,.0f}
                - **Progreso Actual de Amortización:** {pct_val:.1f}% Pagado
                """, unsafe_allow_html=True)

                # --- TARJETA 3: TABLA PLAN DE PAGOS (AMORTIZACIÓN) ---
                if not amort_user.empty:
                    st.markdown("📅 PLAN DE PAGOS (AMORTIZACIONES)")
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
        st.markdown("🧮 Simulador de Crédito FEDESO")
        tasa_display = "0.007% M.V."
        st.markdown(f"💡 CALCULADORA DE CUOTAS (Tasa de interés: {tasa_display})")

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
        n = plazo_sim
        P = monto_sim

        if i > 0:
            cuota_exacta = P * (i * (1 + i)**n) / ((1 + i)**n - 1)
        else:
            cuota_exacta = P / n

        cuota_sim = round(cuota_exacta)
        fecha_inicio = dt.now()
        fecha_fin = fecha_inicio + relativedelta(months=n)
        meses_esp = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha_fin_str = f"{meses_esp[fecha_fin.month - 1]} de {fecha_fin.year}"

        st.markdown(f"""
        📊 **RESULTADO DE LA SIMULACIÓN**

        - **Cuota Mensual Estimada:** ${cuota_sim:,.0f}
        - **Fecha de Finalización:** {fecha_fin_str}
        - **Total a Pagar:** ${cuota_sim * n:,.0f}
        """, unsafe_allow_html=True)

        st.markdown("📅 PROYECCIÓN PASO A PASO")
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
        st.link_button("📝 Solicitar este Crédito", FORM_URL, use_container_width=True)
