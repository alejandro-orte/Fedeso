import base64
import os
from datetime import date

import pandas as pd
import streamlit as st

import db
import logica as L
from seguridad import hash_password, verificar_password

# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    page_title="FEDESO - Fondo Empresarial de Solidaridad",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

LINEAS_CREDITO = ["Crédito Express", "Crédito Ordinario", "Retanqueo"]
ESTADOS_SOLICITUD = ["Pendiente", "Aprobado", "Rechazado"]

# =========================================================
# ESTILOS CSS
# =========================================================
st.markdown("""
<style>
    header[data-testid="stHeader"],
    [data-testid="stHeaderToolbar"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }
    #MainMenu { display: none !important; visibility: hidden !important; }
    footer { display: none !important; visibility: hidden !important; }
    [data-testid="stElementToolbar"] { display: none !important; }
    [data-testid="stSidebar"] {
        width: 340px !important;
        background-color: #f8fafc !important;
        border-right: 3px solid #cbd5e1 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 56px !important;
        font-size: 1.10rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
        border: 2px solid #2563eb !important;
        background-color: #ffffff !important;
        color: #1e3a8a !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border-color: #1d4ed8 !important;
        transform: translateY(-2px);
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        border-color: #dc2626 !important;
        background-color: #fef2f2 !important;
        color: #991b1b !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #dc2626 !important;
        color: #ffffff !important;
    }
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 22px;
        border: 1px solid #e5e7eb;
    }
    .metric-container { display: flex; flex-direction: column; }
    .metric-label {
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value { font-size: 1.35rem; font-weight: 800; color: #111827; }
    .status-tag-green {
        display: inline-block; background-color: #dcfce7; color: #15803d;
        padding: 6px 14px; border-radius: 20px; font-size: 0.90rem; font-weight: 800;
    }
    .status-tag-yellow {
        display: inline-block; background-color: #fef3c7; color: #b45309;
        padding: 6px 14px; border-radius: 20px; font-size: 0.90rem; font-weight: 800;
    }
    .status-tag-red {
        display: inline-block; background-color: #fee2e2; color: #b91c1c;
        padding: 6px 14px; border-radius: 20px; font-size: 0.90rem; font-weight: 800;
    }
    .status-tag-gray {
        display: inline-block; background-color: #e5e7eb; color: #374151;
        padding: 6px 14px; border-radius: 20px; font-size: 0.90rem; font-weight: 800;
    }
    .header-box {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 10px rgba(30, 58, 138, 0.15);
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# UTILIDADES DE PRESENTACIÓN
# =========================================================
def get_image_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    return "https://raw.githubusercontent.com/alejandro-orte/Fedeso/main/fedeso%20imagen%20web.png"


LOGO_URL = get_image_base64("fedeso imagen web.png")


def dinero(valor) -> str:
    return f"${valor:,.0f}"


def badge_cuota(estado) -> str:
    texto = str(estado).lower()
    if "pagad" in texto or "al dia" in texto or "al día" in texto:
        return "🟢 Pagado"
    if "mora" in texto or "atras" in texto:
        return "🔴 En Mora"
    if "pendiente" in texto or "curso" in texto:
        return "🟡 Pendiente"
    return str(estado)


BADGES_CREDITO = {
    "finalizado": '<span class="status-tag-green">🟢 Finalizado</span>',
    "mora": '<span class="status-tag-red">🔴 En Mora</span>',
    "pendiente": '<span class="status-tag-yellow">🟡 Pendiente</span>',
    "al_dia": '<span class="status-tag-green">🟢 Al día</span>',
    "sin_plan": '<span class="status-tag-gray">Sin plan de pagos</span>',
}


def mensaje_db_error(e: Exception):
    st.error(f"No se pudo completar la operación en la base de datos: {e}")


# =========================================================
# CONTROL DE SESIÓN
# =========================================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["nombre"] = ""
    st.session_state["rol"] = "asociado"
if "pantalla" not in st.session_state:
    st.session_state["pantalla"] = "dashboard"

# =========================================================
# LOGIN
# =========================================================
if not st.session_state["autenticado"]:
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.write("")
        st.write("")
        st.markdown(
            f"""<div style="text-align: center;"><img src="{LOGO_URL}" width="200"></div>""",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            st.subheader("🔑 Iniciar Sesión")
            user_input = st.text_input("Usuario (Cédula)").strip().lower()
            pass_input = st.text_input("Contraseña", type="password").strip()
            submit = st.form_submit_button("Ingresar a mi Fondo", use_container_width=True)

            if submit:
                if not user_input or not pass_input:
                    st.warning("Por favor ingrese usuario y contraseña.")
                else:
                    entrar = None
                    try:
                        with st.spinner("Verificando credenciales..."):
                            u = db.get_usuario(user_input)
                        if u and verificar_password(pass_input, u["contrasena"]):
                            entrar = u
                        else:
                            st.error("Usuario o contraseña incorrectos.")
                    except Exception as e:
                        mensaje_db_error(e)
                    if entrar:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario"] = entrar["usuario"]
                        st.session_state["nombre"] = entrar["nombre"] or entrar["usuario"]
                        st.session_state["rol"] = entrar["rol"]
                        st.rerun()

# =========================================================
# APLICACIÓN (usuario autenticado)
# =========================================================
else:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px 0;">
                <img src="{LOGO_URL}" width="160"><br><br>
                <div style="background-color: #ffffff; padding: 14px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 15px;">
                    <span style="font-size: 0.85rem; color: #6b7280; font-weight: 600;">Bienvenido(a)</span><br>
                    <strong style="color: #111827; font-size: 1.1rem;">👤 {st.session_state['nombre']}</strong><br>
                    <small style="color: #2563eb; font-weight: 700;">Rol: {st.session_state['rol'].capitalize()}</small>
                </div>
            </div>
            <div style="background-color: #e0f2fe; border-left: 5px solid #0284c7; padding: 10px 12px; border-radius: 8px; margin-bottom: 16px;">
                <strong style="color: #0369a1; font-size: 0.95rem;">📌 MENÚ DE NAVEGACIÓN</strong><br>
                <span style="color: #0c4a6e; font-size: 0.85rem;">Toque cualquier botón para cambiar de sección:</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        pantalla = st.session_state["pantalla"]
        opciones_menu = [
            ("dashboard", "📊 Mi Estado de Cuenta", "btn_dashboard"),
            ("subir_comprobante", "📩 Notificar Pago", "btn_subir_side"),
            ("simulador", "🧮 Simulador de Crédito", "btn_simulador"),
            ("solicitud", "📝 Solicitud de Crédito", "btn_solicitud"),
        ]
        for clave, texto, key in opciones_menu:
            etiqueta = f"▶️ {texto}" if pantalla == clave else texto
            if st.button(etiqueta, use_container_width=True, key=key):
                st.session_state["pantalla"] = clave
                st.rerun()

        if st.session_state["rol"] == "admin":
            st.divider()
            etiqueta = "▶️ 🛠️ Panel de Administración" if pantalla == "admin" else "🛠️ Panel de Administración"
            if st.button(etiqueta, use_container_width=True, key="btn_admin"):
                st.session_state["pantalla"] = "admin"
                st.rerun()

        st.divider()
        st.write("")
        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True, key="btn_logout"):
            for clave in ["autenticado", "usuario", "nombre", "rol", "pantalla"]:
                st.session_state.pop(clave, None)
            st.rerun()

    st.markdown(
        """
        <div class="header-box" style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin:0; color:white; font-size: 1.7rem; font-weight:800;">FEDESO</h2>
                <span style="font-size: 1rem; opacity: 0.95;">Fondo Empresarial de Solidaridad</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.95rem; font-weight: 600; opacity: 0.9;">Portal de Asociados</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    usuario = st.session_state["usuario"]

    # -----------------------------------------------------
    # 1. ESTADO DE CUENTA
    # -----------------------------------------------------
    if st.session_state["pantalla"] == "dashboard":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">Mi Estado de Cuenta FEDESO</h3>', unsafe_allow_html=True)

        col_btn_dash, _ = st.columns([1.5, 1])
        with col_btn_dash:
            if st.button("📩 Notificar Pago de Cuota Realizado", type="primary", use_container_width=True, key="btn_subir_main"):
                st.session_state["pantalla"] = "subir_comprobante"
                st.rerun()
        st.write("")

        try:
            with st.spinner("Cargando tu información..."):
                prestamo = db.get_prestamo(usuario)
                plan = db.get_plan(usuario)

            if not prestamo:
                st.info("Aún no tienes un préstamo registrado en el fondo.")
            else:
                estado = L.estado_credito(plan, date.today())
                badge = BADGES_CREDITO.get(estado, BADGES_CREDITO["al_dia"])
                tasa_pct = prestamo["tasa_mv"] * 100
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e5e7eb; padding-bottom: 12px; margin-bottom: 16px;">
                        <h4 style="margin:0; color:#1e3a8a; font-weight:700;">📊 RESUMEN DE PRÉSTAMO</h4>
                        <span style="font-size: 0.95rem; color:#4b5563;">Asociado: <strong>{st.session_state['nombre']}</strong></span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px;">
                        <div class="metric-container">
                            <span class="metric-label">Monto del Préstamo</span>
                            <span class="metric-value">{dinero(prestamo['monto'])}</span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Plazo (Meses)</span>
                            <span class="metric-value">{prestamo['plazo']} meses</span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Tasa M.V.</span>
                            <span class="metric-value">{tasa_pct:.2f}%</span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Cuota Mensual</span>
                            <span class="metric-value" style="color:#1e3a8a;">{dinero(prestamo['cuota'])}</span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Tasa Anual Nominal</span>
                            <span class="metric-value">{tasa_pct * 12:.2f}%</span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Estado del Crédito</span>
                            <div style="margin-top: 4px;">{badge}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                cuotas = [r for r in plan if r["cuota_num"] > 0]
                total_cuotas = len(cuotas)
                pagadas = [r for r in cuotas if str(r["estado"]).lower() in L.ESTADOS_PAGADO]
                num_pagadas = len(pagadas)
                prox = L.cuota_actual(plan)
                prox_txt = f"Cuota #{prox['cuota_num']} ({prox['mes_anio']})" if prox else "🎉 Completado"
                if pagadas:
                    saldo_est = max(pagadas, key=lambda r: r["cuota_num"])["saldo"]
                else:
                    saldo_est = next((r["saldo"] for r in plan if r["cuota_num"] == 0), prestamo["monto"])
                pct = (num_pagadas / total_cuotas * 100) if total_cuotas else 0.0

                st.markdown(f"""
                <div class="card">
                    <h4 style="margin-top:0; color:#1e3a8a; font-weight:700; border-bottom: 1px solid #e5e7eb; padding-bottom: 12px; margin-bottom: 16px;">
                        📊 ESTADO DE PAGOS Y PROGRESO
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px;">
                        <div class="metric-container">
                            <span class="metric-label">Progreso de Pago</span>
                            <span class="metric-value">{num_pagadas} <span style="font-size:0.95rem; font-weight:normal; color:#6b7280;">de {total_cuotas} cuotas</span></span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Próximo Mes a Pagar</span>
                            <span class="metric-value" style="font-size: 1.2rem; color: #b45309;">{prox_txt}</span>
                        </div>
                        <div class="metric-container">
                            <span class="metric-label">Saldo Pendiente Estimado</span>
                            <span class="metric-value">{dinero(saldo_est)}</span>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.90rem; color: #4b5563; font-weight: 700; margin-bottom: 6px;">
                            <span>Progreso Actual de Amortización</span>
                            <span>{pct:.1f}% Pagado</span>
                        </div>
                        <div style="background-color: #e5e7eb; border-radius: 10px; height: 12px; width: 100%; overflow: hidden;">
                            <div style="background-color: #2563eb; width: {pct}%; height: 100%; border-radius: 10px;"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<h4 style="color:#1e3a8a; margin-top:25px; margin-bottom:10px;">📅 PLAN DE PAGOS (AMORTIZACIONES)</h4>', unsafe_allow_html=True)
                tabla = pd.DataFrame(plan)[["cuota_num", "mes_anio", "intereses", "capital", "saldo", "estado"]]
                tabla["estado"] = tabla["estado"].apply(badge_cuota)
                tabla = tabla.rename(columns={
                    "cuota_num": "Nº", "mes_anio": "Mes/Año", "intereses": "Intereses",
                    "capital": "Capital", "saldo": "Saldo", "estado": "Estado de Pago",
                })
                st.dataframe(
                    tabla.style.format({"Intereses": "${:,.0f}", "Capital": "${:,.0f}", "Saldo": "${:,.0f}"}),
                    use_container_width=True,
                    hide_index=True,
                )
        except Exception as e:
            mensaje_db_error(e)

    # -----------------------------------------------------
    # 2. NOTIFICAR PAGO
    # -----------------------------------------------------
    elif st.session_state["pantalla"] == "subir_comprobante":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">📩 Notificar Pago Realizado</h3>', unsafe_allow_html=True)
        try:
            plan = db.get_plan(usuario)
        except Exception as e:
            mensaje_db_error(e)
            plan = []

        opciones = [
            f"Cuota #{r['cuota_num']} ({r['mes_anio']}) - Estado actual: {r['estado']}"
            for r in plan if r["cuota_num"] > 0
        ] or ["General / Cuota Mes Actual"]

        st.markdown("""
        <div class="card" style="background-color: #f0fdf4; border-color: #bbf7d0;">
            <p style="color: #166534; font-size: 1.05rem; font-weight: 700; margin:0;">
                📌 Seleccione la cuota realizada y presione el botón para notificar directamente al administrador con un solo clic.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_notificar_pago"):
            cuota_seleccionada = st.selectbox("1. Seleccione la cuota que notifica:", opciones)
            comentarios = st.text_input("2. Observaciones adicionales o N° de transferencia (Opcional):").strip()
            submit_comp = st.form_submit_button("📩 Confirmar y Notificar Pago al Administrador", use_container_width=True)

            if submit_comp:
                try:
                    with st.spinner("Enviando notificación al administrador..."):
                        db.insertar_comprobante(
                            usuario, st.session_state["nombre"], cuota_seleccionada,
                            comentarios if comentarios else "Notificación rápida",
                        )
                    st.success("✅ ¡Notificación de pago enviada correctamente! El administrador la verificará y actualizará la cuota.")
                except Exception as e:
                    mensaje_db_error(e)

    # -----------------------------------------------------
    # 3. SIMULADOR
    # -----------------------------------------------------
    elif st.session_state["pantalla"] == "simulador":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">🧮 Simulador de Crédito FEDESO</h3>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card" style="background-color: #eff6ff; border-color: #bfdbfe;">
            <span style="color: #1e40af; font-size: 1rem;">💡 <strong>CALCULADORA DE CUOTAS:</strong> Diseña tu plan de crédito ideal. Tasa de interés mensual aplicada: <strong>{L.TASA_MENSUAL_DEFAULT * 100:.2f}% M.V.</strong></span>
        </div>
        """, unsafe_allow_html=True)

        col_monto, col_plazo = st.columns(2)
        with col_monto:
            monto_sim = st.number_input("Monto del préstamo ($)", min_value=100000, max_value=100000000,
                                        value=5000000, step=500000, format="%d")
        with col_plazo:
            plazo_sim = st.number_input("Plazo deseado (Meses)", min_value=1, max_value=120, value=24, step=1)

        n = int(plazo_sim)
        primera = L.sumar_meses(date.today().replace(day=1), 1)
        cuota_sim, plan_sim = L.generar_plan(float(monto_sim), n, L.TASA_MENSUAL_DEFAULT, primera)
        fin = L.sumar_meses(primera, n - 1)
        fecha_fin_str = f"{L.MESES_LARGOS[fin.month - 1]} de {fin.year}"

        st.markdown(f"""
        <div class="card" style="background-color: #f8fafc; border-left: 5px solid #2563eb;">
            <h4 style="margin-top:0; color:#1e3a8a; font-weight:700; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">📊 RESULTADO DE LA SIMULACIÓN</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 12px;">
                <div class="metric-container">
                    <span class="metric-label">Cuota Mensual Estimada</span>
                    <span class="metric-value" style="color:#2563eb; font-size: 1.5rem;">{dinero(cuota_sim)}</span>
                </div>
                <div class="metric-container">
                    <span class="metric-label">Fecha de Finalización</span>
                    <span class="metric-value" style="font-size: 1.15rem;">{fecha_fin_str}</span>
                </div>
                <div class="metric-container">
                    <span class="metric-label">Total a Pagar Estimado</span>
                    <span class="metric-value">{dinero(cuota_sim * n)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<h4 style="color:#1e3a8a; margin-top:20px; margin-bottom:10px;">📅 PROYECCIÓN PASO A PASO</h4>', unsafe_allow_html=True)
        cronograma = pd.DataFrame([
            {"Nº": r["cuota_num"], "Mes/Año": r["mes_anio"],
             "Cuota Fija": r["intereses"] + r["capital"], "Intereses": r["intereses"],
             "Capital": r["capital"], "Saldo Restante": r["saldo"]}
            for r in plan_sim if r["cuota_num"] > 0
        ])
        st.dataframe(
            cronograma.style.format({"Cuota Fija": "${:,.0f}", "Intereses": "${:,.0f}",
                                     "Capital": "${:,.0f}", "Saldo Restante": "${:,.0f}"}),
            use_container_width=True,
            hide_index=True,
        )
        st.write("")
        if st.button("📝 Solicitar este Crédito", type="primary", use_container_width=True):
            st.session_state["pantalla"] = "solicitud"
            st.rerun()

    # -----------------------------------------------------
    # 4. SOLICITUD DE CRÉDITO
    # -----------------------------------------------------
    elif st.session_state["pantalla"] == "solicitud":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">📝 Solicitud de Crédito</h3>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card" style="background-color: #f8fafc; border-left: 5px solid #2563eb; margin-bottom: 20px;">
            <div style="margin-bottom: 15px;">
                <strong style="color: #1e3a8a; font-size: 1.05rem;">LÍNEAS DE CRÉDITO</strong><br>
                <hr style="margin: 5px 0; border: none; border-top: 1px solid #cbd5e1; width: 30%;">
                <ul style="margin-top: 5px; color: #334155; font-size: 0.95rem;">
                    <li><strong>Crédito Express:</strong> Hasta por el 100% del valor ahorrado. No requiere codeudor.</li>
                    <li><strong>Crédito Ordinario:</strong> Hasta dos veces el valor ahorrado, debe contar con un codeudor (obligatoriamente asociado).</li>
                    <li><strong>Retanqueo:</strong> Renovación o ampliación de un crédito vigente.</li>
                </ul>
            </div>
            <div>
                <strong style="color: #1e3a8a; font-size: 1.05rem;">CONDICIONES</strong><br>
                <hr style="margin: 5px 0; border: none; border-top: 1px solid #cbd5e1; width: 30%;">
                <ul style="margin-top: 5px; color: #334155; font-size: 0.95rem;">
                    <li>Plazo entre 6 a 24 meses.</li>
                    <li>Registrar mínimo tres (3) meses de afiliación o reafiliación.</li>
                    <li>Firma personal del Asociado.</li>
                    <li>Tasa Efectiva Anual del 8,7%.</li>
                    <li>Tasa Mes Vencido 0,7%.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card" style="background-color: #f0fdf4; border-color: #bbf7d0;">
            <p style="color: #166534; font-size: 1.05rem; font-weight: 700; margin:0;">
                📌 Complete el siguiente formulario para solicitar su crédito. Sus datos como asociado ({st.session_state['nombre']}) se adjuntarán automáticamente.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_solicitar_credito"):
            st.markdown("#### Línea de Crédito *")
            linea_credito = st.radio("Seleccione la línea de crédito", LINEAS_CREDITO, label_visibility="collapsed")

            st.write("")
            st.markdown("#### Valor solicitado *")
            valor_solicitado = st.number_input("Ingrese el valor a solicitar ($)", min_value=0, step=100000,
                                               format="%d", label_visibility="collapsed")

            st.write("")
            st.markdown("#### Número de cuotas")
            opciones_plazo = [str(i) for i in range(6, 25)]  # 6 a 24 meses, según condiciones
            numero_cuotas = st.selectbox("Elegir", options=opciones_plazo,
                                         index=opciones_plazo.index("12"), label_visibility="collapsed")

            st.write("")
            submit_solicitud = st.form_submit_button("📩 Enviar Solicitud de Crédito", use_container_width=True)

            if submit_solicitud:
                if valor_solicitado <= 0:
                    st.error("El valor solicitado debe ser mayor a 0.")
                else:
                    try:
                        with st.spinner("Enviando su solicitud al administrador..."):
                            db.insertar_solicitud(usuario, st.session_state["nombre"], linea_credito,
                                                  float(valor_solicitado), int(numero_cuotas))
                        st.success("✅ ¡Su solicitud de crédito ha sido enviada exitosamente! El administrador la revisará pronto.")
                    except Exception as e:
                        mensaje_db_error(e)

    # -----------------------------------------------------
    # 5. PANEL DE ADMINISTRACIÓN
    # -----------------------------------------------------
    elif st.session_state["pantalla"] == "admin" and st.session_state["rol"] == "admin":
        st.markdown('<h3 style="color:#1e3a8a; margin-bottom: 20px;">🛠️ Panel de Administración FEDESO</h3>', unsafe_allow_html=True)

        tab_user, tab_prestamo, tab_cuota, tab_verif, tab_solic, tab_resumen, tab_editar = st.tabs([
            "👤 Crear Usuario",
            "💵 Registrar Préstamo",
            "📅 Registrar Pago / Cuota",
            "📩 Verificar Notificaciones",
            "📝 Solicitudes",
            "📈 Resumen del Fondo",
            "✏️ Editar Usuarios",
        ])

        # ---- Crear usuario ----
        with tab_user:
            st.subheader("Registrar Nuevo Usuario")
            with st.form("form_crear_usuario"):
                col1, col2 = st.columns(2)
                with col1:
                    new_user = st.text_input("Usuario (Cédula o ID)").strip().lower()
                    new_nombre = st.text_input("Nombre Completo").strip()
                with col2:
                    new_pass = st.text_input("Contraseña").strip()
                    new_rol = st.selectbox("Rol", ["asociado", "admin"])
                btn_crear_u = st.form_submit_button("Guardar Usuario", use_container_width=True)

                if btn_crear_u:
                    if not (new_user and new_pass and new_nombre):
                        st.warning("Por favor complete todos los campos.")
                    else:
                        try:
                            db.crear_usuario(new_user, hash_password(new_pass), new_nombre, new_rol)
                            st.success(f"✅ Usuario **{new_user}** registrado con éxito.")
                        except ValueError as e:
                            st.error(str(e))
                        except Exception as e:
                            mensaje_db_error(e)

        # ---- Registrar préstamo ----
        with tab_prestamo:
            st.subheader("Asignar Préstamo a Asociado")
            with st.form("form_crear_prestamo"):
                user_p = st.text_input("Usuario del Asociado").strip().lower()
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    monto_p = st.number_input("Monto del Préstamo ($)", value=5000000, step=500000, min_value=100000)
                with col_p2:
                    plazo_p = st.number_input("Plazo en Meses", value=24, step=1, min_value=1, max_value=120)
                with col_p3:
                    fecha_inicio_p = st.date_input("Mes de la Primera Cuota", value=date.today())

                cuota_calc, _ = L.generar_plan(float(monto_p), int(plazo_p), L.TASA_MENSUAL_DEFAULT,
                                               date(fecha_inicio_p.year, fecha_inicio_p.month, 1))
                st.info(f"Cuota mensual calculada: **{dinero(cuota_calc)}** | Se generarán **{int(plazo_p) + 1} filas** (Cuota 0 de desembolso + {int(plazo_p)} cuotas).")
                btn_crear_p = st.form_submit_button("Guardar Préstamo y Generar Amortización", use_container_width=True)

                if btn_crear_p:
                    if not user_p:
                        st.warning("Por favor ingrese el usuario del asociado.")
                    else:
                        try:
                            if not db.get_usuario(user_p):
                                st.error(f"No existe el usuario **{user_p}**. Créelo primero en la pestaña Crear Usuario.")
                            elif db.get_prestamo(user_p):
                                st.error(f"**{user_p}** ya tiene un préstamo registrado. Use la pestaña de pagos para abonos.")
                            else:
                                with st.spinner("Guardando préstamo y generando plan de pagos..."):
                                    cuota, plan = L.generar_plan(float(monto_p), int(plazo_p), L.TASA_MENSUAL_DEFAULT,
                                                                 date(fecha_inicio_p.year, fecha_inicio_p.month, 1))
                                    db.crear_prestamo(user_p, float(monto_p), int(plazo_p),
                                                      L.TASA_MENSUAL_DEFAULT, float(cuota), plan)
                                st.success(f"🎉 ¡Préstamo registrado! Se guardaron las {len(plan)} filas de **{user_p}**.")
                        except Exception as e:
                            mensaje_db_error(e)

        # ---- Registrar pago / recálculo ----
        with tab_cuota:
            st.subheader("Registrar Pago / Abono Extraordinario con Recálculo Automático")
            try:
                prestamistas = db.listar_prestamistas()
            except Exception as e:
                mensaje_db_error(e)
                prestamistas = []

            if not prestamistas:
                st.info("Todavía no hay préstamos registrados.")
            else:
                etiquetas = {p["usuario"]: f"{p['nombre'] or p['usuario']} ({p['usuario']})" for p in prestamistas}
                user_c = st.selectbox("Seleccione el Asociado:", list(etiquetas.keys()),
                                      format_func=lambda k: etiquetas[k])
                plan_c = db.get_plan(user_c)
                cuotas_c = [r for r in plan_c if r["cuota_num"] > 0]
                nums = [r["cuota_num"] for r in cuotas_c]

                # Fuera del formulario: al cambiar la cuota, los montos se actualizan al instante.
                num_cuota_sel = st.selectbox("Número de Cuota a Pagar:", nums, key=f"cuota_sel_{user_c}")
                fila_sel = next((r for r in cuotas_c if r["cuota_num"] == num_cuota_sel), None)
                val_int_def = fila_sel["intereses"] if fila_sel else 0.0
                val_cap_def = fila_sel["capital"] if fila_sel else 0.0

                with st.form(f"form_abono_recalculo_{user_c}_{num_cuota_sel}"):
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        interes_pagado_input = st.number_input("Intereses a Pagar ($)", value=float(val_int_def), step=1000.0)
                        capital_pagado_input = st.number_input("Abono a Capital Pagado ($)", value=float(val_cap_def), step=10000.0)
                    with col_c2:
                        st.write("**Efecto del Pago / Abono en Cuotas Futuras:**")
                        tipo_efecto = st.radio(
                            "Seleccione el tipo de recálculo:",
                            [
                                "🟢 Cuota Regular / Normal (Sin abono extra)",
                                "📉 Abono Extra -> Reducir Cuota Mensual (Mantener plazo restante)",
                                "⏳ Abono Extra -> Reducir Plazo (Mantener valor de cuota)",
                            ],
                        )
                    btn_guardar_abono = st.form_submit_button("💾 Guardar Pago y Recalcular Crédito", use_container_width=True)

                    if btn_guardar_abono:
                        if num_cuota_sel is None:
                            st.error("⚠️ No hay cuotas para registrar a este usuario.")
                        else:
                            modo = ("reducir_cuota" if "Reducir Cuota" in tipo_efecto
                                    else "reducir_plazo" if "Reducir Plazo" in tipo_efecto
                                    else "normal")
                            try:
                                with st.spinner("Recalculando plan de amortización..."):
                                    db.registrar_pago(user_c, int(num_cuota_sel), float(interes_pagado_input),
                                                      float(capital_pagado_input), modo)
                                st.success(f"🎉 ¡Pago de Cuota #{num_cuota_sel} registrado y amortización recalculada para **{user_c}**!")
                            except Exception as e:
                                mensaje_db_error(e)

        # ---- Verificar notificaciones ----
        with tab_verif:
            st.subheader("📩 Notificaciones de Pago Pendientes por Verificar")
            try:
                pendientes = db.listar_comprobantes("Pendiente")
            except Exception as e:
                mensaje_db_error(e)
                pendientes = []

            if not pendientes:
                st.success("🎉 ¡No hay pagos pendientes por verificar!")
            for c in pendientes:
                col_card, col_action = st.columns([2.5, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="card" style="border-left: 5px solid #2563eb; background-color: #f8fafc; padding: 16px; margin-bottom: 10px;">
                        <h4 style="margin:0; color:#1e3a8a;">👤 Asociado: {c['nombre']} <small>(Cédula: {c['usuario']})</small></h4>
                        <p style="margin: 6px 0 2px 0;"><strong>Cuota/Mes Notificado:</strong> <span style="color:#2563eb; font-weight:700;">{c['mes_cuota']}</span></p>
                        <p style="margin: 2px 0;"><strong>Fecha de Notificación:</strong> {c['fecha']}</p>
                        <p style="margin: 2px 0; color: #4b5563;"><strong>Notas / Referencia:</strong> {c['observaciones'] or 'Sin notas adicionales'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_action:
                    st.write("")
                    if st.button("✅ Aprobar Pago con 1 Clic", key=f"ok_{c['id']}", type="primary", use_container_width=True):
                        aprobado = False
                        try:
                            aprobado = db.aprobar_comprobante(c["id"])
                            if not aprobado:
                                st.warning("Esta notificación ya no está pendiente.")
                        except Exception as e:
                            mensaje_db_error(e)
                        if aprobado:
                            st.rerun()

            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.markdown("<h3 style='color: #1e3a8a;'>📁 Historial de Pagos Confirmados</h3>", unsafe_allow_html=True)
            try:
                confirmados = pd.DataFrame(db.listar_comprobantes("Aprobado"))
            except Exception as e:
                mensaje_db_error(e)
                confirmados = pd.DataFrame()

            if confirmados.empty:
                st.info("Aún no hay pagos confirmados en el historial.")
            else:
                col1, col2 = st.columns([2, 1])
                with col1:
                    buscar_texto = st.text_input("🔍 Buscar asociado o ID", placeholder="Ej. Luis Alejandro...")
                with col2:
                    fecha_notificacion = st.date_input("📅 Fecha de notificación", value=None)

                if buscar_texto:
                    mascara = (confirmados["nombre"].str.contains(buscar_texto, case=False, na=False)
                               | confirmados["usuario"].str.contains(buscar_texto, case=False, na=False))
                    confirmados = confirmados[mascara]
                if fecha_notificacion:
                    confirmados = confirmados[confirmados["fecha"].str.startswith(fecha_notificacion.strftime("%Y-%m-%d"))]

                if confirmados.empty:
                    st.warning("No se encontraron resultados para su búsqueda.")
                else:
                    st.dataframe(
                        confirmados[["usuario", "nombre", "mes_cuota", "fecha", "estado"]].rename(columns={
                            "usuario": "ID / Cédula", "nombre": "Asociado", "mes_cuota": "Cuota Notificada",
                            "fecha": "Fecha Notificación", "estado": "Estado"}),
                        use_container_width=True, hide_index=True, height=250,
                    )

        # ---- Solicitudes ----
        with tab_solic:
            st.subheader("📝 Solicitudes de Crédito Recibidas")
            try:
                solicitudes = pd.DataFrame(db.listar_solicitudes())
            except Exception as e:
                mensaje_db_error(e)
                solicitudes = pd.DataFrame()

            if solicitudes.empty:
                st.info("Aún no hay solicitudes de crédito.")
            else:
                st.dataframe(
                    solicitudes.rename(columns={
                        "id": "ID", "usuario": "Cédula", "nombre": "Asociado", "linea_credito": "Línea",
                        "valor_solicitado": "Valor", "numero_cuotas": "Cuotas", "fecha": "Fecha", "estado": "Estado"}).style.format(
                        {"Valor": "${:,.0f}"}),
                    use_container_width=True, hide_index=True,
                )
                with st.form("form_estado_solicitud"):
                    sol_id = st.selectbox("Solicitud (ID)", solicitudes["id"].tolist())
                    nuevo_estado = st.selectbox("Nuevo estado", ESTADOS_SOLICITUD)
                    if st.form_submit_button("Actualizar estado", use_container_width=True):
                        actualizado = False
                        try:
                            db.actualizar_solicitud(int(sol_id), nuevo_estado)
                            actualizado = True
                        except Exception as e:
                            mensaje_db_error(e)
                        if actualizado:
                            st.success(f"Solicitud {sol_id} marcada como {nuevo_estado}.")
                            st.rerun()

        # ---- Resumen del fondo ----
        with tab_resumen:
            st.subheader("📈 Resumen General y Balance del Fondo FEDESO")
            try:
                r = db.resumen_fondo()
                c1, c2, c3 = st.columns(3)
                c1.metric("Préstamos activos", r["prestamos"])
                c2.metric("Total prestado", dinero(r["total_prestado"]))
                c3.metric("Saldo por cobrar (aprox.)", dinero(r["saldo_por_cobrar"]))
                c4, c5, c6 = st.columns(3)
                c4.metric("Capital cobrado", dinero(r["capital_cobrado"]))
                c5.metric("Intereses cobrados", dinero(r["intereses_cobrados"]))
                c6.metric("Cuotas pagadas", r["cuotas_pagadas"])
                st.caption(f"Comprobantes pendientes de verificar: {r['comprobantes_pendientes']}")
            except Exception as e:
                mensaje_db_error(e)

        # ---- Editar usuarios ----
        with tab_editar:
            st.subheader("✏️ Editar Usuario (nombre, rol o contraseña)")
            try:
                todos = db.listar_usuarios()
            except Exception as e:
                mensaje_db_error(e)
                todos = []

            if todos:
                etiquetas = {u["usuario"]: f"{u['nombre'] or u['usuario']} ({u['usuario']})" for u in todos}
                sel = st.selectbox("Seleccione el usuario:", list(etiquetas.keys()),
                                   format_func=lambda k: etiquetas[k], key="edit_user_sel")
                actual = next(u for u in todos if u["usuario"] == sel)
                roles = ["asociado", "admin"]

                with st.form(f"form_editar_usuario_{sel}"):
                    nuevo_nombre = st.text_input("Nombre", value=actual["nombre"] or "").strip()
                    nuevo_rol = st.selectbox("Rol", roles,
                                             index=roles.index(actual["rol"]) if actual["rol"] in roles else 0)
                    nueva_clave = st.text_input("Nueva contraseña (déjela vacía para no cambiarla)",
                                                type="password").strip()
                    guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True)

                if guardar:
                    error = None
                    if not nuevo_nombre:
                        error = "El nombre no puede quedar vacío."
                    elif nueva_clave and len(nueva_clave) < 6:
                        error = "La contraseña debe tener al menos 6 caracteres."
                    elif sel == st.session_state["usuario"] and nuevo_rol != "admin":
                        error = "No puedes quitarte a ti mismo el rol de administrador."

                    guardado = False
                    if error:
                        st.error(error)
                    else:
                        try:
                            db.actualizar_usuario(sel, nuevo_nombre, nuevo_rol,
                                                  hash_password(nueva_clave) if nueva_clave else None)
                            guardado = True
                        except ValueError as e:
                            st.error(str(e))
                        except Exception as e:
                            mensaje_db_error(e)

                    if guardado:
                        if sel == st.session_state["usuario"]:
                            st.session_state["nombre"] = nuevo_nombre
                        st.rerun()
