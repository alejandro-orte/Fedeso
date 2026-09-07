import streamlit as st
import pandas as pd
import time

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
    except:
        return 0.0

def cargar_pestana(nombre_pestana):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    df = pd.read_csv(url)
    # Convierte encabezados a texto, elimina espacios invisibles y los pasa a minúsculas
    df.columns = [str(col).strip().lower() for col in df.columns]

    # El parámetro 'nocache' obliga a Google a enviar los datos recién guardados
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}&nocache={int(time.time())}"
    df = pd.read_csv(url)
    df.columns = [str(col).strip().lower() for col in df.columns]
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
            user_input = st.text_input("Usuario").strip().lower()
            pass_input = st.text_input("Contraseña", type="password").strip()
            submit = st.form_submit_button("Ingresar a mi Fondo", use_container_width=True)
            
            if submit:
                try:
                    df_users = cargar_pestana("Usuarios")

                      
                    # Diagnóstico en pantalla si la columna 'usuario' sigue sin aparecer
                    if "usuario" not in df_users.columns:
                        st.error(f"❌ No se encontró la columna 'usuario' en la pestaña Usuarios.")
                        st.warning(f"Columnas leídas por la app: {list(df_users.columns)}")
                    else:
                        df_users["usuario"] = df_users["usuario"].astype(str).str.strip().str.lower()
                        df_users["contrasena"] = df_users["contrasena"].astype(str).str.strip()
                        
                        valido = df_users[(df_users["usuario"] == user_input) & (df_users["contrasena"] == pass_input)]
                        
                        if not valido.empty:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario"] = user_input
                            st.session_state["nombre"] = valido["nombre"].iloc[0] if "nombre" in valido.columns else user_input
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")
                except Exception as e:
                    st.error(f"Error al conectar con Google Sheets: {e}")

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
        df_resumen = cargar_pestana("Resumen")
        if "usuario" in df_resumen.columns:
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
        
        df_amort = cargar_pestana("Amortizacion")
        if "usuario" in df_amort.columns:
            df_amort["usuario"] = df_amort["usuario"].astype(str).str.strip().str.lower()
            amort_user = df_amort[df_amort["usuario"] == usuario_key].copy()
            
            if not amort_user.empty:
                st.subheader("📋 Plan de Pagos Programado")
                for col in ["intereses", "capital", "saldo"]:
                    if col in amort_user.columns:
                        amort_user[col] = amort_user[col].apply(limpiar_numero)
                
                cols_existentes = [c for c in ["cuota_num", "mes_ano", "intereses", "capital", "saldo"] if c in amort_user.columns]
                tabla_mostrar = amort_user[cols_existentes].copy()
                
                st.dataframe(
                    tabla_mostrar.style.format({
                        col: "${:,.0f}" for col in ["intereses", "capital", "saldo"] if col in tabla_mostrar.columns
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("No hay registros de amortización para este usuario.")
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
