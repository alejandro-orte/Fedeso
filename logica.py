"""Lógica del préstamo: amortización, recálculo tras un pago y estados.

No depende de Streamlit ni de la base de datos, así que se puede probar por separado.
"""
import re
from datetime import date

TASA_MENSUAL_DEFAULT = 0.0069865  # 0,69865 % mensual vencido
MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGOS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
ESTADOS_PAGADO = {"pagado", "pagada"}


def sumar_meses(fecha: date, n: int) -> date:
    """Primer día del mes que queda n meses después de `fecha`."""
    m = fecha.month - 1 + n
    return date(fecha.year + m // 12, m % 12 + 1, 1)


def etiqueta_mes(fecha: date) -> str:
    """Formato de la app: ene-27."""
    return f"{MESES_CORTOS[fecha.month - 1]}-{str(fecha.year)[2:]}"


def parsear_mes(texto):
    """Convierte 'ene-27' (o 'enero 2027') en el primer día del mes. None si no se reconoce."""
    m = re.match(r"^\s*([a-záéíóú]{3,})\s*[-/ ]\s*(\d{2}|\d{4})\s*$", str(texto or "").strip().lower())
    if not m:
        return None
    mes = m.group(1)[:3]
    if mes not in MESES_CORTOS:
        return None
    anio = int(m.group(2))
    anio = anio + 2000 if anio < 100 else anio
    return date(anio, MESES_CORTOS.index(mes) + 1, 1)


def calcular_cuota(monto: float, tasa: float, plazo: int) -> float:
    """Cuota fija mensual (sistema francés)."""
    n = max(1, int(plazo))
    if tasa > 0:
        factor = (1 + tasa) ** n
        return monto * (tasa * factor) / (factor - 1)
    return monto / n


def _fila(num, mes, intereses, capital, saldo, estado="Pendiente"):
    texto_mes = etiqueta_mes(mes) if isinstance(mes, date) else str(mes)
    return {
        "cuota_num": num,
        "mes_anio": texto_mes,
        "intereses": round(intereses),
        "capital": round(capital),
        "saldo": round(max(0.0, saldo)),
        "estado": estado,
    }


def generar_plan(monto: float, plazo: int, tasa: float, fecha_primera: date):
    """Devuelve (cuota, filas). Fila 0 = desembolso; filas 1..plazo = cuotas mensuales."""
    cuota = round(calcular_cuota(monto, tasa, plazo))
    filas = [_fila(0, "", 0, 0, monto)]
    saldo = float(monto)
    for k in range(1, int(plazo) + 1):
        intereses = round(saldo * tasa)
        if k == plazo:
            capital = round(saldo)
            saldo = 0.0
        else:
            capital = cuota - intereses
            saldo -= capital
        filas.append(_fila(k, sumar_meses(fecha_primera, k - 1), intereses, capital, saldo))
    return cuota, filas


def recalcular_tras_pago(filas, num_pagar, interes_pagado, capital_pagado, modo,
                         tasa=TASA_MENSUAL_DEFAULT):
    """Registra el pago de la cuota `num_pagar` y recalcula las cuotas siguientes.

    filas: lista de dicts (cuota_num, mes_anio, intereses, capital, saldo, estado), incluye la cuota 0.
    modo: 'normal' | 'reducir_cuota' | 'reducir_plazo'.
    Devuelve el plan completo (incluida la cuota 0) listo para guardar.
    """
    filas = sorted(filas, key=lambda r: r["cuota_num"])
    cuota0 = next((r for r in filas if r["cuota_num"] == 0), None)
    originales = [r for r in filas if r["cuota_num"] > 0]
    paid_row = next((r for r in originales if r["cuota_num"] == num_pagar), None)
    if paid_row is None:
        raise ValueError(f"No existe la cuota {num_pagar} en el plan.")

    nuevas = [dict(cuota0)] if cuota0 else []
    saldo = float(cuota0["saldo"]) if cuota0 else 0.0

    for r in originales:
        c = r["cuota_num"]
        if c < num_pagar:
            nuevas.append(dict(r))
            saldo = float(r["saldo"])
        elif c == num_pagar:
            nuevo_saldo = max(0.0, saldo - capital_pagado)
            nuevas.append(dict(r, intereses=round(interes_pagado), capital=round(capital_pagado),
                               saldo=round(nuevo_saldo), estado="Pagado"))
            saldo = nuevo_saldo
            break

    max_orig = max(r["cuota_num"] for r in originales)
    fecha_ref = parsear_mes(paid_row["mes_anio"]) or date.today().replace(day=1)

    if saldo > 0:
        restantes = max_orig - num_pagar

        if modo == "reducir_cuota" and restantes > 0:
            factor = (1 + tasa) ** restantes
            cuota_fija = round(saldo * (tasa * factor) / (factor - 1)) if tasa > 0 else round(saldo / max(1, restantes))
            c = num_pagar + 1
            for k in range(1, restantes + 1):
                intereses = round(saldo * tasa)
                if k == restantes:
                    capital = round(saldo)
                    saldo = 0.0
                else:
                    capital = cuota_fija - intereses
                    saldo -= capital
                nuevas.append(_fila(c, sumar_meses(fecha_ref, k), intereses, capital, saldo))
                c += 1

        elif modo == "reducir_plazo":
            fila1 = next((r for r in originales if r["cuota_num"] == 1), None)
            cuota_regular = (float(fila1["intereses"]) + float(fila1["capital"])) if fila1 else 0.0
            if cuota_regular <= 0:
                cuota_regular = saldo * tasa + 100000
            c = num_pagar + 1
            k = 1
            while saldo > 0 and k <= 120:
                intereses = round(saldo * tasa)
                capital = cuota_regular - intereses
                if capital >= saldo or k == 120:
                    capital = round(saldo)
                    saldo = 0.0
                else:
                    saldo -= capital
                nuevas.append(_fila(c, sumar_meses(fecha_ref, k), intereses, capital, saldo))
                c += 1
                k += 1

        else:  # normal: se mantienen los meses y capitales originales
            posteriores = [r for r in originales if r["cuota_num"] > num_pagar]
            c = num_pagar + 1
            for idx, r in enumerate(posteriores, start=1):
                intereses = round(saldo * tasa)
                capital_orig = float(r["capital"])
                if capital_orig >= saldo or idx == len(posteriores):
                    capital = round(saldo)
                    saldo = 0.0
                else:
                    capital = capital_orig
                    saldo -= capital
                nuevas.append(_fila(c, r["mes_anio"], intereses, capital, saldo, estado=r["estado"]))
                c += 1

    return nuevas


def estado_credito(filas, hoy: date) -> str:
    """'finalizado' | 'mora' | 'pendiente' | 'al_dia' | 'sin_plan' según las cuotas."""
    cuotas = [r for r in filas if r["cuota_num"] > 0]
    if not cuotas:
        return "sin_plan"
    pendientes = [r for r in cuotas if str(r["estado"]).strip().lower() not in ESTADOS_PAGADO]
    if not pendientes:
        return "finalizado"
    mes_actual = date(hoy.year, hoy.month, 1)
    prox = parsear_mes(pendientes[0]["mes_anio"])
    if prox is None:
        return "al_dia"
    if prox < mes_actual:
        return "mora"
    if prox == mes_actual:
        return "pendiente"
    return "al_dia"


def cuota_actual(filas):
    """Primera cuota (>0) que no está pagada, o None."""
    for r in sorted(filas, key=lambda r: r["cuota_num"]):
        if r["cuota_num"] > 0 and str(r["estado"]).strip().lower() not in ESTADOS_PAGADO:
            return r
    return None
