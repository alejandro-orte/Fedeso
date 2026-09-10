import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Configuración inicial de la página
st.set_page_config(
    page_title="Simulador de Crédito FEDESO",
    page_icon="🧮",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 1. CONSTANTES Y CONFIGURACIÓN GLOBAL
# -----------------------------------------------------------------------------
# Tasa mensual configurada en 0.7% (0.007 en decimal)
TASA_MENSUAL_DEFAULT = 0.007  
SHEET_ID = "TU_ID_DE_GOOGLE_SHEETS_AQUI"

# -----------------------------------------------------------------------------
# 2. FUNCIONES HELPER / CÁLCULOS
# -----------------------------------------------------------------------------
def calcular_cuota_francesa(monto, plazo_meses, tasa_mensual):
    """
    Calcula la cuota mensual fija usando el sistema de amortización francés.
    Aplica redondeo al entero más cercano para evitar discrepancias de centavos.
    """
    if tasa_mensual > 0:
        cuota_exacta = monto * (tasa_mensual * (1 + tasa_mensual)**plazo_meses) / ((1 + tasa_mensual)**plazo_meses - 1)
    else:
        cuota_exacta = monto / plazo_meses
        
    return round(cuota_exacta)

def generar_tabla_amortizacion(monto, plazo_meses, tasa_mensual, cuota):
    """
    Genera el plan de pagos detallado mes a mes.
    """
    saldo = monto
    fecha_actual = datetime.now()
    plan_pagos = []

    for i in range(1, plazo_meses + 1):
        interes_mes = saldo * tasa_mensual
        
        # Ajuste en la última cuota para liquidar exactamente el saldo restante
        if i == plazo_meses:
            abono_capital = saldo
            cuota_aplicada = abono_capital + interes_mes
            nuevo_saldo = 0.0
        else:
            abono_capital = cuota - interes_mes
            cuota_aplicada = cuota
            nuevo_saldo = saldo - abono_capital

        fecha_pago = fecha_actual + relativedelta(months=i)

        plan_pagos.append({
            "N° Cuota": i,
            "Fecha Pago": fecha_pago.strftime("%d/%m/%Y"),
            "Cuota ($)": round(cuota_aplicada),
            "Interés ($)": round(interes_mes),
            "Abono Capital ($)": round(abono_capital),
            "Saldo Restante ($)": round(max(0, nuevo_saldo))
        })

        saldo = nuevo_saldo

    return pd.DataFrame(plan_pagos)

# -----------------------------------------------------------------------------
# 3. INTERFAZ DE USUARIO (STREAMLIT)
# -----------------------------------------------------------------------------
st.title("🧮 Simulador de Crédito FEDESO")

# Contenedor superior: Información de la Tasa
st.subheader("💡 CALCULADORA DE CUOTAS")
st.info(f"**Tasa de interés aplicada:** {TASA_MENSUAL_DEFAULT * 100:.2f}% M.V.")

st.markdown("---")

# Campos de entrada de datos
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
        value=24,
        step=1
    )

# -----------------------------------------------------------------------------
# 4. PROCESAMIENTO Y RESULTADOS
# -----------------------------------------------------------------------------
# Cálculo de la cuota fija redondeada
cuota_sim = calcular_cuota_francesa(monto_sim, plazo_sim, TASA_MENSUAL_DEFAULT)

# Cálculo de totales
total_a_pagar = cuota_sim * plazo_sim
fecha_finalizacion = datetime.now() + relativedelta(months=plazo_sim)

st.markdown("---")
st.subheader("📊 RESULTADO DE LA SIMULACIÓN")

# Métricas principales
col_res1, col_res2, col_res3 = st.columns(3)

with col_res1:
    st.metric(
        label="CUOTA MENSUAL ESTIMADA:",
        value=f"${cuota_sim:,.0f}".replace(",", ".")
    )

with col_res2:
    st.metric(
        label="FECHA DE FINALIZACIÓN:",
        value=fecha_finalizacion.strftime("%B de %Y").capitalize()
    )

with col_res3:
    st.metric(
        label="TOTAL A PAGAR:",
        value=f"${total_a_pagar:,.0f}".replace(",", ".")
    )

# -----------------------------------------------------------------------------
# 5. TABLA DE AMORTIZACIÓN
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📋 Proyección del Plan de Pagos")

df_plan = generar_tabla_amortizacion(monto_sim, plazo_sim, TASA_MENSUAL_DEFAULT, cuota_sim)

# Formatear la tabla con separadores de miles para visualización
df_display = df_plan.copy()
for col in ["Cuota ($)", "Interés ($)", "Abono Capital ($)", "Saldo Restante ($)"]:
    df_display[col] = df_display[col].apply(lambda x: f"${x:,.0f}".replace(",", "."))

st.dataframe(df_display, use_container_width=True)
