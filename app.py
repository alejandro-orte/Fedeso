import streamlit as st
import pandas as pd

# =========================================================
# CONFIGURACIÓN Y RECURSOS
# =========================================================
SHEET_ID = "12A0vnk-mUz2PaQpBmXnOPWtjzvOr7CXpUHLMn9ioLNQ"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdBFMIqAXxKNis9O29AbqPheXlfZqUdsUlUolERBICgTwWEsw/viewform"

# Puedes cambiar este enlace por el logo real de tu fondo (URL de imagen pública o icono PNG/SVG)
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"

st.set_page_config(
    page_title="FEDESO - Fondo Empresarial",
    page_icon="💰",
    layout="wide"
)

# =========================================================
# ESTILOS CSS PERSONALIZADOS (Diseño Visual)
# =========================================================
st.markdown("""
    <style>
    /* Fondo general de la app */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Estilo de las tarjetas de métricas */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
    }
    div[data-testid="stMetricValue"] {
        color: #1f4e78 !important;
        font-weight: 700 !important;
    }

    /* Personalización de botones */
    .stButton>button, .stLinkButton>a {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    /* Encabezados y títulos */
    h1, h2, h3 {
        color: #0f172a !important;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Estilo del formulario de Login */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# FUNCIONES DE DATOS
# =========================================================
def limpiar_numero(valor):
    if pd.isna(valor):
        return 0.0
    texto = str(valor).replace('$', '').replace(',', '').replace('%', '').strip()
    try:
        return float(texto)
    except:
        return 0.0

def cargar_pestana(nombre_pestana):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    df = pd.read_csv(url)
    # Limpia mayúsculas y espacios en los encabezados automáticamente
    df.columns = df.columns.astype(str).str.strip().str.lower()
    return df

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
            user_input = st.text_input("usuario").strip().lower()
            pass_input = st.text_input("contraseña", type="password").strip()
            submit = st.form_submit_button("Ingresar a mi Fondo", use_container_width=True)
            
            if submit:
                try:
                    df_users = cargar_pestana("Usuarios")
                    df_users["usuario"] = df_users["usuario"].astype(str).str.strip().str.lower()
                    df_users["contrasena"] = df_users["contrasena"].astype(str).str.strip()
                    
                    valido = df_users[(df_users["usuario"] == user_input) & (df_users["contrasena"] == pass_input)]
                    
                    if not valido.empty:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario"] = user_input
                        st.session_state["nombre"] = valido["nombre"].iloc[0]
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
                except Exception as e:
                    st.error("Error al conectar. Verifica que el ID del Google Sheet sea correcto y el archivo sea público.")
                    
                    # Por esta otra:
                    st.error(f"Detalle del error: {e}")

# =========================================================
# 2. PANTALLA INTERNA DEL USUARIO
# =========================================================
else:
    # Menú lateral
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

    # Encabezado principal
    st.title(f"Resumen de Crédito")
    st.caption(f"Bienvenido(a), **{st.session_state['nombre']}**")
    
    usuario_key = st.session_state["usuario"]
    
    try:
        # Métricas principales
        df_resumen = cargar_pestana("Resumen")
        df_resumen["usuario"] = df_resumen["usuario"].astype(str).str.strip().str.lower()
        resumen_user = df_resumen[df_resumen["usuario"] == usuario_key]
        
        if not resumen_user.empty:
            monto = limpiar_numero(resumen_user["monto"].iloc[0])
            plazo = int(limpiar_numero(resumen_user["plazo"].iloc[0]))
            tasa = limpiar_numero(resumen_user["tasa_mv"].iloc[0])
            cuota = limpiar_numero(resumen_user["cuota"].iloc[0])
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Monto Aprobado", f"${monto:,.0f}")
            col2.metric("Plazo Total", f"{plazo} meses")
            col3.metric("Tasa de Interés", f"{tasa*100:.1f}% MV" if tasa < 1 else f"{tasa}% MV")
            col4.metric("Cuota Mensual", f"${cuota:,.0f}")
        
        st.markdown("---")
        
        # Tabla de Amortización
        df_amort = cargar_pestana("Amortizacion")
        df_amort["usuario"] = df_amort["usuario"].astype(str).str.strip().str.lower()
        amort_user = df_amort[df_amort["usuario"] == usuario_key].copy()
        
        if not amort_user.empty:
            st.subheader("📋 Plan de Pagos Programado")
            for col in ["intereses", "capital", "saldo"]:
                if col in amort_user.columns:
                    amort_user[col] = amort_user[col].apply(limpiar_numero)
            
            tabla_mostrar = amort_user[["cuota_num", "mes_ano", "intereses", "capital", "saldo"]].copy()
            tabla_mostrar.columns = ["# Cuota", "Mes / Año", "Intereses", "Abono a Capital", "Saldo Pendiente"]
            
            st.dataframe(
                tabla_mostrar.style.format({
                    "Intereses": "${:,.0f}",
                    "Abono a Capital": "${:,.0f}",
                    "Saldo Pendiente": "${:,.0f}"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("No hay registros de amortización asociados a esta cuenta.")
    except Exception as e:
        st.error(f"Error al cargar la información: {e}")
