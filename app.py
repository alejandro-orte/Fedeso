import streamlit as st
import pandas as pd
import requests
import datetime

# PEGA AQUÍ LA URL QUE TE DIO GOOGLE APPS SCRIPT
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwXsXGtkEBQLdoWQQxZLgT6ghJuviieLu-XBMk0uWvKeJUHcH7yBbgW5hlqVzmR4uP3/exec"

# ... (Mantiene tu función cargar_pestana y código de login aquí) ...

# DENTRO DE LA PANTALLA PRINCIPAL (después de mostrar la amortización):

st.divider()

# Formulario para enviar nuevo abono
st.subheader("💵 Registrar Nuevo Abono")

with st.form("form_abono"):
    col_f, col_m = st.columns(2)
    fecha_pago = col_f.date_input("Fecha de pago", datetime.date.today())
    monto_pago = col_m.number_input("Monto abonado ($)", min_value=0.0, step=10000.0)
    nota_pago = st.text_input("Nota o comprobante (ej. N° Nequi, Transfiya o Banco)")
    btn_guardar = st.form_submit_button("Guardar Abono")
    
    if btn_guardar:
        if monto_pago > 0:
            datos_envio = {
                "usuario": st.session_state["usuario"],
                "fecha": str(fecha_pago),
                "monto": monto_pago,
                "nota": nota_pago
            }
            respuesta = requests.post(WEBHOOK_URL, json=datos_envio)
            if respuesta.status_code == 200:
                st.success("¡Abono registrado correctamente!")
                st.rerun()
            else:
                st.error("No se pudo guardar el abono en la base de datos.")
        else:
            st.warning("Ingresa un monto mayor a 0.")

# Mostrar historial de abonos acumulados
try:
    df_abonos = cargar_pestana("Abonos")
    df_abonos["usuario"] = df_abonos["usuario"].astype(str).str.strip().str.lower()
    abonos_user = df_abonos[df_abonos["usuario"] == st.session_state["usuario"]].copy()
    
    if not abonos_user.empty:
        st.subheader("📜 Historial de Abonos Realizados")
        abonos_user["monto"] = abonos_user["monto"].apply(limpiar_numero)
            
        tabla_abonos = abonos_user[["fecha", "monto", "nota"]].copy()
        tabla_abonos.columns = ["Fecha", "Monto Abonado", "Comprobante / Nota"]
        
        st.dataframe(
            tabla_abonos.style.format({"Monto Abonado": "${:,.0f}"}),
            use_container_width=True,
            hide_index=True
        )
        
        total_abonado = abonos_user["monto"].sum()
        st.info(f"**Total abonado acumulado:** ${total_abonado:,.0f}")
except Exception:
    st.info("Aún no hay abonos registrados para este usuario.")
    
# PEGA AQUÍ TU ID DE GOOGLE SHEETS
SHEET_ID = "1d77IinY-qGRbOn_ZuE0bLQQTjtrAR3tE"

# Función para convertir textos con '$', ',' o '%' a números
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
            monto = limpiar_numero(resumen_user["monto"].iloc[0])
            plazo = int(limpiar_numero(resumen_user["plazo"].iloc[0]))
            tasa = limpiar_numero(resumen_user["tasa_mv"].iloc[0])
            cuota = limpiar_numero(resumen_user["cuota"].iloc[0])
            
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
            
            # Limpiar columnas numéricas de la tabla
            for col in ["intereses", "capital", "saldo"]:
                if col in amort_user.columns:
                    amort_user[col] = amort_user[col].apply(limpiar_numero)
            
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
