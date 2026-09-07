import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración de página estilo app móvil
st.set_page_config(
    page_title="FEDESO - Fondo de Solidaridad",
    page_icon="💰",
    layout="wide"
)

# Estilo visual moderno
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-header { color: #1F4E78; text-align: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Estado de la sesión (Login)
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nombre"] = ""

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# -------------------------------------------------------------
# 1. PANTALLA DE LOGIN
# -------------------------------------------------------------
if not st.session_state["autenticado"]:
    st.markdown("<h2 class='main-header'>FEDESO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Fondo Empresarial de Solidaridad</p>", unsafe_allow_html=True)
    
    st.subheader("🔑 Iniciar Sesión")
    
    with st.form("login_form"):
        user_input = st.text_input("Usuario").strip().lower()
        pass_input = st.text_input("Contraseña", type="password").strip()
        submit = st.form_submit_button("Ingresar a mi Fondo")
        
        if submit:
            try:
                # Leer usuarios desde Google Sheets
                df_users = conn.read(worksheet="Usuarios")
                df_users["usuario"] = df_users["usuario"].astype(str).str.strip().str.lower()
                df_users["contrasena"] = df_users["contrasena"].astype(str).str.strip()
                
                # Validar credenciales
                valido = df_users[(df_users["usuario"] == user_input) & (df_users["contrasena"] == pass_input)]
                
                if not valido.empty:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario"] = user_input
                    st.session_state["nombre"] = valido["nombre"].iloc[0]
                    st.success(f"¡Bienvenido(a) {st.session_state['nombre']}!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos. Verifica tus datos.")
            except Exception as e:
                st.error("Error al conectar con la base de datos. Verifica el enlace de Google Sheets.")

# -------------------------------------------------------------
# 2. PANTALLA PRINCIPAL (DASHBOARD)
# -------------------------------------------------------------
else:
    # Menú lateral
    st.sidebar.markdown(f"### 👤 {st.session_state['nombre']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state["nombre"] = ""
        st.rerun()

    st.markdown(f"<h2 class='main-header'>Simulación {st.session_state['nombre']}</h2>", unsafe_allow_html=True)
    
    usuario_key = st.session_state["usuario"]
    
    try:
        # Cargar datos de Resumen
        df_resumen = conn.read(worksheet="Resumen")
        df_resumen["usuario"] = df_resumen["usuario"].astype(str).str.strip().str.lower()
        resumen_user = df_resumen[df_resumen["usuario"] == usuario_key]
        
        if not resumen_user.empty:
            monto = float(resumen_user["monto"].iloc[0])
            plazo = int(resumen_user["plazo"].iloc[0])
            tasa = float(resumen_user["tasa_mv"].iloc[0])
            cuota = float(resumen_user["cuota"].iloc[0])
            
            # Mostrar Tarjetas de Resumen
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Monto", f"${monto:,.0f}")
            col2.metric("Plazo", f"{plazo} meses")
            col3.metric("Tasa MV", f"{tasa*100:.1f}%" if tasa < 1 else f"{tasa}%")
            col4.metric("Cuota", f"${cuota:,.0f}")
        
        st.write("---")
        
        # Cargar Tabla de Amortización (Plan de Pagos)
        df_amort = conn.read(worksheet="Amortizacion")
        df_amort["usuario"] = df_amort["usuario"].astype(str).str.strip().str.lower()
        amort_user = df_amort[df_amort["usuario"] == usuario_key].copy()
        
        if not amort_user.empty:
            st.subheader("📋 Tabla de Amortización")
            
            tabla_mostrar = amort_user[["cuota_num", "mes_ano", "intereses", "capital", "saldo"]].copy()
            tabla_mostrar.columns = ["#", "Mes/Año", "Intereses", "Capital", "Saldo"]
            
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
            st.warning("No hay tabla de amortización registrada para este usuario.")
            
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
