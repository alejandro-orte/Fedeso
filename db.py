"""Acceso a Neon (PostgreSQL). Única capa que habla con la base de datos."""
import re

import psycopg
import streamlit as st
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

import logica as L


@st.cache_resource(show_spinner=False)
def _pool():
    url = st.secrets["database"]["url"]
    # Prueba directa primero: si la contraseña o la dirección están mal, el error real
    # se muestra en pantalla. El pool oculta ese motivo y solo dice "couldn't get a connection".
    with psycopg.connect(url, connect_timeout=10) as prueba:
        prueba.execute("SELECT 1")
    # El pool reconecta solo cuando Neon suspende el cómputo por inactividad.
    return ConnectionPool(
        conninfo=url,
        min_size=1,
        max_size=5,
        kwargs={"row_factory": dict_row},
        open=True,
    )


def _f(valor) -> float:
    return float(valor) if valor is not None else 0.0


def _filas_plan(filas):
    return [
        {
            "cuota_num": int(r["cuota_num"]),
            "mes_anio": r["mes_anio"],
            "intereses": _f(r["intereses"]),
            "capital": _f(r["capital"]),
            "saldo": _f(r["saldo"]),
            "estado": r["estado"],
        }
        for r in filas
    ]


# ---------- usuarios ----------
def get_usuario(usuario: str):
    with _pool().connection() as conn:
        return conn.execute(
            "SELECT usuario, contrasena, nombre, rol FROM usuarios WHERE usuario = %s", (usuario,)
        ).fetchone()


def listar_usuarios():
    with _pool().connection() as conn:
        return conn.execute("SELECT usuario, nombre, rol FROM usuarios ORDER BY nombre").fetchall()


def crear_usuario(usuario: str, contrasena_hash: str, nombre: str, rol: str):
    try:
        with _pool().connection() as conn:
            conn.execute(
                "INSERT INTO usuarios (usuario, contrasena, nombre, rol) VALUES (%s, %s, %s, %s)",
                (usuario, contrasena_hash, nombre, rol),
            )
    except psycopg.errors.UniqueViolation:
        raise ValueError(f"Ya existe un usuario con la cédula {usuario}.")


def actualizar_usuario(usuario: str, nombre: str, rol: str, contrasena_hash=None):
    """Cambia nombre y rol; cambia la contraseña solo si se entrega un hash nuevo."""
    with _pool().connection() as conn:
        if rol != "admin":
            otros_admins = conn.execute(
                "SELECT count(*) AS n FROM usuarios WHERE rol = 'admin' AND usuario <> %s", (usuario,)
            ).fetchone()["n"]
            if otros_admins == 0:
                raise ValueError("Debe quedar al menos un administrador en el sistema.")
        if contrasena_hash:
            conn.execute(
                "UPDATE usuarios SET nombre = %s, rol = %s, contrasena = %s WHERE usuario = %s",
                (nombre, rol, contrasena_hash, usuario))
        else:
            conn.execute(
                "UPDATE usuarios SET nombre = %s, rol = %s WHERE usuario = %s",
                (nombre, rol, usuario))


# ---------- préstamos y cuotas ----------
def get_prestamo(usuario: str):
    with _pool().connection() as conn:
        row = conn.execute(
            "SELECT monto, plazo, tasa_mv, cuota FROM prestamos WHERE usuario = %s", (usuario,)
        ).fetchone()
    if not row:
        return None
    return {"monto": _f(row["monto"]), "plazo": int(row["plazo"]),
            "tasa_mv": _f(row["tasa_mv"]), "cuota": _f(row["cuota"])}


def listar_prestamistas():
    with _pool().connection() as conn:
        return conn.execute(
            "SELECT p.usuario, u.nombre FROM prestamos p JOIN usuarios u USING (usuario) ORDER BY u.nombre"
        ).fetchall()


def get_plan(usuario: str):
    with _pool().connection() as conn:
        filas = conn.execute(
            "SELECT cuota_num, mes_anio, intereses, capital, saldo, estado "
            "FROM cuotas WHERE usuario = %s ORDER BY cuota_num", (usuario,)
        ).fetchall()
    return _filas_plan(filas)


_INSERT_CUOTA = (
    "INSERT INTO cuotas (usuario, cuota_num, mes_anio, intereses, capital, saldo, estado) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
)


def crear_prestamo(usuario: str, monto: float, plazo: int, tasa: float, cuota: float, plan):
    """Crea el préstamo y su plan de pagos en una sola transacción."""
    with _pool().connection() as conn:
        conn.execute(
            "INSERT INTO prestamos (usuario, monto, plazo, tasa_mv, cuota) VALUES (%s, %s, %s, %s, %s)",
            (usuario, monto, plazo, tasa, cuota),
        )
        with conn.cursor() as cur:
            cur.executemany(_INSERT_CUOTA, [
                (usuario, r["cuota_num"], r["mes_anio"], r["intereses"], r["capital"], r["saldo"], r["estado"])
                for r in plan
            ])


def registrar_pago(usuario: str, num_cuota: int, interes: float, capital: float, modo: str):
    """Registra un pago y recalcula el plan según el modo, en una sola transacción."""
    with _pool().connection() as conn:
        pr = conn.execute("SELECT tasa_mv FROM prestamos WHERE usuario = %s", (usuario,)).fetchone()
        if not pr:
            raise ValueError("El usuario no tiene préstamo registrado.")
        filas = _filas_plan(conn.execute(
            "SELECT cuota_num, mes_anio, intereses, capital, saldo, estado "
            "FROM cuotas WHERE usuario = %s ORDER BY cuota_num", (usuario,)
        ).fetchall())
        if not filas:
            raise ValueError("El usuario no tiene plan de pagos.")

        nuevo = L.recalcular_tras_pago(filas, num_cuota, interes, capital, modo, tasa=_f(pr["tasa_mv"]))

        conn.execute("DELETE FROM cuotas WHERE usuario = %s", (usuario,))
        with conn.cursor() as cur:
            cur.executemany(_INSERT_CUOTA, [
                (usuario, r["cuota_num"], r["mes_anio"], r["intereses"], r["capital"], r["saldo"], r["estado"])
                for r in nuevo
            ])


# ---------- notificaciones de pago ----------
_FECHA_LOCAL = "to_char(fecha_subida AT TIME ZONE 'America/Bogota', 'YYYY-MM-DD HH24:MI') AS fecha"


def insertar_comprobante(usuario: str, nombre: str, mes_cuota: str, observaciones: str):
    with _pool().connection() as conn:
        conn.execute(
            "INSERT INTO comprobantes (usuario, nombre, mes_cuota, nombre_archivo, tipo_archivo, "
            "archivo_b64, observaciones, estado) VALUES (%s, %s, %s, 'Sin comprobante', 'text/plain', '', %s, 'Pendiente')",
            (usuario, nombre, mes_cuota, observaciones),
        )


def listar_comprobantes(estado: str):
    with _pool().connection() as conn:
        return conn.execute(
            f"SELECT id, usuario, nombre, mes_cuota, {_FECHA_LOCAL}, observaciones, estado "
            "FROM comprobantes WHERE estado = %s ORDER BY fecha_subida DESC", (estado,)
        ).fetchall()


def aprobar_comprobante(comprobante_id: int) -> bool:
    """Marca el comprobante como aprobado y la cuota notificada como pagada."""
    with _pool().connection() as conn:
        fila = conn.execute(
            "SELECT usuario, mes_cuota FROM comprobantes WHERE id = %s AND estado = 'Pendiente'",
            (comprobante_id,),
        ).fetchone()
        if not fila:
            return False
        conn.execute("UPDATE comprobantes SET estado = 'Aprobado' WHERE id = %s", (comprobante_id,))
        m = re.search(r"Cuota #(\d+)", fila["mes_cuota"] or "")
        if m:
            conn.execute(
                "UPDATE cuotas SET estado = 'Pagado' WHERE usuario = %s AND cuota_num = %s",
                (fila["usuario"], int(m.group(1))),
            )
    return True


# ---------- solicitudes de crédito ----------
def insertar_solicitud(usuario: str, nombre: str, linea: str, valor: float, numero_cuotas: int):
    with _pool().connection() as conn:
        conn.execute(
            "INSERT INTO solicitudes (usuario, nombre, linea_credito, valor_solicitado, numero_cuotas, estado) "
            "VALUES (%s, %s, %s, %s, %s, 'Pendiente')",
            (usuario, nombre, linea, valor, numero_cuotas),
        )


def listar_solicitudes():
    with _pool().connection() as conn:
        return conn.execute(
            f"SELECT id, usuario, nombre, linea_credito, valor_solicitado, numero_cuotas, "
            f"to_char(fecha_solicitud AT TIME ZONE 'America/Bogota', 'YYYY-MM-DD HH24:MI') AS fecha, estado "
            "FROM solicitudes ORDER BY fecha_solicitud DESC"
        ).fetchall()


def actualizar_solicitud(solicitud_id: int, estado: str):
    with _pool().connection() as conn:
        conn.execute("UPDATE solicitudes SET estado = %s WHERE id = %s", (estado, solicitud_id))


# ---------- resumen del fondo ----------
def resumen_fondo():
    with _pool().connection() as conn:
        prest = conn.execute(
            "SELECT count(*) AS n, COALESCE(sum(monto), 0) AS total FROM prestamos").fetchone()
        cobro = conn.execute(
            "SELECT count(*) AS n, COALESCE(sum(intereses), 0) AS intereses, COALESCE(sum(capital), 0) AS capital "
            "FROM cuotas WHERE cuota_num > 0 AND lower(estado) IN ('pagado', 'pagada')").fetchone()
        pend = conn.execute(
            "SELECT count(*) AS n FROM comprobantes WHERE estado = 'Pendiente'").fetchone()
    total = _f(prest["total"])
    capital = _f(cobro["capital"])
    return {
        "prestamos": int(prest["n"]),
        "total_prestado": total,
        "cuotas_pagadas": int(cobro["n"]),
        "intereses_cobrados": _f(cobro["intereses"]),
        "capital_cobrado": capital,
        "saldo_por_cobrar": max(0.0, total - capital),
        "comprobantes_pendientes": int(pend["n"]),
    }
