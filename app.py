import streamlit as st
import pandas as pd

# =========================================================
# CONFIGURACIÓN Y RECURSOS
# =========================================================
SHEET_ID = "12A0vnk-mUz2PaQpBmXnOPWtjzvOr7CXpUHLMn9ioLNQ"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdBFMIqAXxKNis9O29AbqPheXlfZqUdsUlUolERBICgTwWEsw/viewform"
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"

st.set_page_config(
    page_title="FEDESO - Mi Estado de Cuenta",
    page_icon="💰",
    layout="wide"
)

# =========================================================
# ESTILOS CSS PERSONALIZADOS (ESTILO DASHBOARD SOFTR)
# =========================================================
st.markdown("""
    <style>
    /* Fondo oscuro de la aplicación */
    .stApp { 
        background: linear-gradient(135deg, #0e0720 0%, #1b123a 100%) !important; 
    }
    
    /* Ocultar barra lateral por defecto si se prefiere dashboard completo */
    [data-testid="stSidebar"] {
        background-color: #120b2d !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Ocultar elementos nativos innecesarios de Streamlit */
    #MainMenu, header, footer {visibility: hidden;}

    /* Título principal centrado estilo Softr */
    .dashboard-title {
        color: #ffffff;
        font-family: 'Inter', sans-serif;
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 25px;
    }

    /* Tarjetas blancas estilo Softr */
    .softr-card {
        background-color: #ffffff;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        margin-bottom: 25px;
        color: #0f172a;
    }

    /* Encabezado de tarjeta */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 12px;
        margin-bottom: 20px;
    }

    .card-title {
        font-size: 1.1rem;
        font-weight: 800;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .card-user-email {
        font-size: 0.95rem;
        font-weight: 600;
        color: #334155;
    }

    /* Cuadrícula de métricas en la tarjeta */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px 30px;
    }

    .metric-item-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 4px;
    }

    .metric-item-val {
        font-size: 1.5rem;
        font-weight: 800;
        color: #000000;
    }

    /* Ajustes para la tabla en Streamlit */
    div[data-testid="stDataFrame"] {
        background-color: #ffffff;
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stForm"] {
        background-color: #ffffff;
        border-radius: 18px;
        padding: 30px;
    }
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
        st.write("")
        st.write("")
        st.image(LOGO_URL, width=80)
        st.markdown("<h2 style='color: white;'>FEDESO</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #cbd5e1;'>Fondo Empresarial de Solidaridad</p>", unsafe_allow_html=True)

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
# 2. PANTALLA INTERNA (DASHBOARD OSCURO ESTILO SOFTR)
# =========================================================
else:
    # --- BARRA SUPERIOR DE NAVEGACIÓN ---
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px;">
                <img src="{LOGO_URL}" width="40"/>
                <span style="color: white; font-weight: 800; font-size: 1.2rem;">FEDESO</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with header_col2:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = ""
            st.session_state["nombre"] = ""
            st.rerun()

    # --- TÍTULO PRINCIPAL ---
    st.markdown('<div class="dashboard-title">Mi Estado de Cuenta FEDESO</div>', unsafe_allow_html=True)

    usuario_key = st.session_state["usuario"]

    try:
        with st.spinner("Cargando tu estado de cuenta..."):
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

                    # Tasa formateada
                    tasa_fmt = f"{tasa*100:.2f}%" if tasa < 1 else f"{tasa:.2f}%"

                    # TARJETA BLANCA DE RESUMEN (REPLICANDO LA IMAGEN)
                    st.markdown(f"""
                    <div class="softr-card">
                        <div class="card-header">
                            <span class="card-title">RESUMEN DE PRÉSTAMO</span>
                            <span class="card-user-email">👤 {st.session_state['nombre']}</span>
                        </div>
                        <div class="metrics-grid">
                            <div>
                                <div class="metric-item-label">Monto del Préstamo:</div>
                                <div class="metric-item-val">${monto:,.0f}</div>
                            </div>
                            <div>
                                <div class="metric-item-label">Plazo (Meses):</div>
                                <div class="metric-item-val">{plazo}</div>
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
                                <div class="metric-item-val">{(tasa*12)*100 if tasa < 1 else tasa*12:.2f}%</div>
                            </div>
                            <div>
                                <div class="metric-item-label">Estado de Cuenta:</div>
                                <div class="metric-item-val" style="color: #16a34a;">Al día</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No se encontró resumen para este usuario.")

            # --- TABLA DE AMORTIZACIÓN (PLAN DE PAGOS) ---
            if "usuario" in df_amort.columns:
                df_amort["usuario"] = normalizar_texto(df_amort["usuario"])
                amort_user = df_amort[df_amort["usuario"] == usuario_key].copy()

                if not amort_user.empty:
                    st.markdown("""
                    <div style="background-color: #ffffff; border-radius: 18px 18px 0 0; padding: 18px 24px; margin-top: 10px;">
                        <span style="font-size: 1.1rem; font-weight: 800; color: #0f172a;">📅 PLAN DE PAGOS (AMORTIZACIONES)</span>
                    </div>
                    """, unsafe_allow_html=True)

                    columnas_num = ["intereses", "capital", "saldo"]
                    for col in columnas_num:
                        if col in amort_user.columns:
                            amort_user[col] = amort_user[col].apply(limpiar_numero)

                    if "estado" in amort_user.columns:
                        amort_user["estado"] = amort_user["estado"].fillna("Pendiente")

                    cols_existentes = [c for c in ["cuota_num", "mes_año", "estado", "intereses", "capital", "saldo"] if c in amort_user.columns]
                    tabla_mostrar = amort_user[cols_existentes].copy()

                    # Renombrar columnas para calcar la imagen
                    renombrar = {
                        "cuota_num": "Nº",
                        "mes_año": "Mes/Año",
                        "estado": "Estado",
                        "intereses": "Intereses",
                        "capital": "Capital",
                        "saldo": "Saldo"
                    }
                    tabla_mostrar = tabla_mostrar.rename(columns=renombrar)

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
