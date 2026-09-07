import streamlit as st
import pandas as pd

# PEGA AQUÍ ÚNICAMENTE TU ID DE GOOGLE SHEETS
SHEET_ID = "1d77IinY-qGRbOn_ZuE0bLQQTjtrAR3tE"

def cargar_pestana(nombre_pestana):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    return pd.read_csv(url)

st.set_page_config(
    page_title="FEDESO - Fondo de Solidaridad",
    page_icon="💰",
    layout="wide"
)

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nombre"] = ""

# 1. PANTALLA DE LOGIN
if not st.session_state["autenticado"]:
    st.title("FEDESO")
    st.caption("Fondo Empresarial de Solidaridad")
    st.subheader("🔑 Iniciar Sesión")
    
    with st.form("login_form"):
        user_input = st.text_input("Usuario").strip().lower()
        pass_input = st.text_input("Contraseña", type="password").strip()
        submit = st.form_submit_button("Ingresar a mi Fondo")
        
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

# 2. PANTALLA PRINCIPAL
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['nombre']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state["nombre"] = ""
        st.rerun()

    st.title(f"Simulación {st.session_state['nombre']}")
    usuario_key = st.session_state["usuario"]
    
    try:
        df_resumen = cargar_pestana("Resumen")
        df_resumen["usuario"] = df_resumen["usuario"].astype(str).str.strip().str.lower()
        resumen_user = df_resumen[df_resumen["usuario"] == usuario_key]
        
        if not resumen_user.empty:
            monto = float(resumen_user["monto"].iloc[0])
            plazo = int(resumen_user["plazo"].iloc[0])
            tasa = float(resumen_user["tasa_mv"].iloc[0])
            cuota = float(resumen_user["cuota"].iloc[0])
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Monto", f"${monto:,.0f}")
            col2.metric("Plazo", f"{plazo} meses")
            col3.metric("Tasa MV", f"{tasa*100:.1f}%" if tasa < 1 else f"{tasa}%")
            col4.metric("Cuota", f"${cuota:,.0f}")
        
        st.divider()
        
        df_amort = cargar_pestana("Amortizacion")
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
            st.warning("No hay registros para este usuario.")
    except Exception as e:
        st.error(f"Error al leer la información: {e}")
