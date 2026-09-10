import streamlit as st
import pandas as pd

# =========================================================
# CONFIGURACIÓN Y RECURSOS
# =========================================================
SHEET_ID = "12A0vnk-mUz2PaQpBmXnOPWtjzvOr7CXpUHLMn9ioLNQ"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdBFMIqAXxKNis9O29AbqPheXlfZqUdsUlUolERBICgTwWEsw/viewform"
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"

st.set_page_config(
    page_title="FEDESO - Fondo Empresarial",
    page_icon="💰",
    layout="wide"
)

# Estilos CSS
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricValue"] { color: #1f4e78 !important; font-weight: 700 !important; }
    .stButton>button, .stLinkButton>a { border-radius: 8px !important; font-weight: 600 !important; }
    h1, h2, h3 { color: #0f172a !important; font-family: 'Segoe UI', Roboto, sans-serif; }
    div[data-testid="stForm"] { background-color: #ffffff; border-radius: 12px; padding: 25px; border: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)


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


def cargar_usuarios() -> pd.DataFrame:
    """Carga los usuarios en tiempo real sin caché."""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Usuarios"
    df = pd.read_csv(url, dtype=str)
    df.columns = [str(col).replace('\xa0', '').strip().lower() for col in df.columns]
    return df


@st.cache_data(ttl=300, show_spinner=False)
def cargar_pestana(nombre_pestana: str) -> pd.DataFrame:
    """Carga las pestañas de Resumen y Amortizacion usando caché de 5 minutos."""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    df = pd.read_csv(url, dtype=str)
    df.columns = [str(col).replace('\xa0', '').strip().lower() for col in df.columns]
    return df


# Inicialización de estado de sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nombre"] = ""

# =========================================================
# 1. PANTALLA DE LOGIN
# =========================================================
if not st.session_state["autenticado"]:
    col_a, col_b, col_c = st.columns([1, 2, 1])

    with col_b:
        st.image(LOGO_URL, width=90)
        st.title("FEDESO")
        st.caption("Fondo Empresarial de Solidaridad")

        st.link_button("📝 Ir al Simulador de Crédito", FORM_URL, use_container_width=True)
        st.write("")

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
                                st.error("❌ Estructura de tabla no válida. Faltan columnas 'usuario' o 'contrasena'.")
                                st.warning(f"Columnas detectadas: {list(df_users.columns)}")
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
                            st.error(f"Error al conectar con el servidor de datos: {e}")

# =========================================================
# 2. PANTALLA INTERNA DEL USUARIO
# =========================================================
else:
    st.sidebar.image(LOGO_URL, width=80)
    st.sidebar.markdown(f"### 👤 {st.session_state['nombre']}")
    st.sidebar.markdown("---")

    st.sidebar.link_button("📝 Simulador de Crédito", FORM_URL, use_container_width=True)
    st.sidebar.write("")

    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state["nombre"] = ""
        st.rerun()

    st.title("Resumen de Crédito")
    st.caption(f"Bienvenido(a), **{st.session_state['nombre']}**")

    usuario_key = st.session_state["usuario"]

    try:
        with st.spinner("Cargando tu información..."):
            # --- SECCIÓN RESUMEN Y ESTADO GENERAL ---
            df_resumen = cargar_pestana("Resumen")
            df_amort = cargar_pestana("Amortizacion")

            if "usuario" in df_resumen.columns:
                df_resumen["usuario"] = normalizar_texto(df_resumen["usuario"])
                resumen_user = df_resumen[df_resumen["usuario"] == usuario_key]

                if not resumen_user.empty:
                    monto = limpiar_numero(resumen_user["monto"].iloc[0])
                    plazo = int(limpiar_numero(resumen_user["plazo"].iloc[0]))
                    tasa = limpiar_numero(resumen_user["tasa_mv"].iloc[0])
                    cuota = limpiar_numero(resumen_user["cuota"].iloc[0])

                    # Fila superior de información general
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Monto Aprobado", f"${monto:,.0f}")
                    col2.metric("Plazo Total", f"{plazo} meses")
                    col3.metric("Tasa de Interés", f"{tasa*100:.2f}% MV" if tasa < 1 else f"{tasa:.2f}% MV")
                    col4.metric("Cuota Mensual", f"${cuota:,.0f}")
                else:
                    st.info("No se encontró información de resumen para este usuario.")

            st.markdown("---")

            # --- SECCIÓN AMORTIZACIÓN Y PROGRESO DE PAGOS ---
            if "usuario" in df_amort.columns:
                df_amort["usuario"] = normalizar_texto(df_amort["usuario"])
                amort_user = df_amort[df_amort["usuario"] == usuario_key].copy()

                if not amort_user.empty:
                    # Limpieza numérica de la tabla
                    columnas_num = ["intereses", "capital", "saldo"]
                    for col in columnas_num:
                        if col in amort_user.columns:
                            amort_user[col] = amort_user[col].apply(limpiar_numero)

                    # Si no existe la columna 'estado' en el Sheet, la creamos vacía por defecto
                    if "estado" not in amort_user.columns:
                        amort_user["estado"] = "Pendiente"
                    else:
                        amort_user["estado"] = amort_user["estado"].fillna("Pendiente").astype(str).str.strip()

                    # Excluir la cuota 0 (desembolso inicial) para los cálculos de progreso
                    amort_cuotas = amort_user[amort_user["cuota_num"].astype(str) != "0"]
                    total_cuotas = len(amort_cuotas)

                    # Cálculo de cuotas pagadas
                    cuotas_pagadas_df = amort_cuotas[amort_cuotas["estado"].str.lower() == "pagado"]
                    num_pagadas = len(cuotas_pagadas_df)

                    # Próxima cuota a pagar / Mes actual
                    proxima_cuota = amort_cuotas[amort_cuotas["estado"].str.lower() != "pagado"]
                    if not proxima_cuota.empty:
                        mes_actual = proxima_cuota.iloc[0].get("mes_año", "N/A")
                        num_cuota_actual = proxima_cuota.iloc[0].get("cuota_num", "N/A")
                        estado_actual_str = f"Cuota #{num_cuota_actual} ({mes_actual})"
                    else:
                        estado_actual_str = "🎉 ¡Crédito Finalizado!"

                    # Métricas de avance
                    st.subheader("📊 Estado de Pagos y Progreso")
                    m_col1, m_col2, m_col3 = st.columns(3)
                    m_col1.metric("Progreso de Pago", f"{num_pagadas} de {total_cuotas} cuotas")
                    m_col2.metric("Próximo Mes a Pagar", estado_actual_str)
                    
                    # Saldo actual pendiente
                    saldo_actual = amort_user["saldo"].iloc[-1] if not cuotas_pagadas_df.empty else monto
                    if not proxima_cuota.empty and "saldo" in proxima_cuota.columns:
                        saldo_actual = proxima_cuota.iloc[0]["saldo"]
                    m_col3.metric("Saldo Pendiente Estimado", f"${saldo_actual:,.0f}")

                    # Barra visual de progreso
                    porcentaje_progreso = min(1.0, num_pagadas / total_cuotas) if total_cuotas > 0 else 0.0
                    st.progress(porcentaje_progreso, text=f"Progreso actual: {porcentaje_progreso*100:.1f}% pagado")

                    st.markdown("---")

                    # --- TABLA DE PLAN DE PAGOS ---
                    st.subheader("📋 Plan de Pagos Programado")

                    cols_existentes = [c for c in ["cuota_num", "mes_año", "estado", "intereses", "capital", "saldo"] if c in amort_user.columns]
                    tabla_mostrar = amort_user[cols_existentes].copy()

                    # Dar formato visual al estado con emojis
                    def formatear_estado(val):
                        val_str = str(val).lower()
                        if "pagad" in val_str:
                            return "🟢 Pagado"
                        elif "curso" in val_str or "pendiente" in val_str:
                            return "🟡 Pendiente"
                        return val

                    if "estado" in tabla_mostrar.columns:
                        tabla_mostrar["estado"] = tabla_mostrar["estado"].apply(formatear_estado)

                    st.dataframe(
                        tabla_mostrar.style.format({
                            col: "${:,.0f}" for col in columnas_num if col in tabla_mostrar.columns
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("No hay registros de plan de pagos programado para este usuario.")
    except Exception as e:
        st.error(f"Error al procesar la información del usuario: {e}")
