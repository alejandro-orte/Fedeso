"""Hash de contraseñas con PBKDF2-SHA256 (solo librería estándar)."""
import hashlib
import hmac
import secrets

ITERACIONES = 600_000
PREFIJO = "pbkdf2_sha256"


def hash_password(texto: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", texto.encode("utf-8"), bytes.fromhex(salt), ITERACIONES)
    return f"{PREFIJO}${ITERACIONES}${salt}${dk.hex()}"


def verificar_password(texto: str, almacenado: str) -> bool:
    try:
        prefijo, iteraciones, salt, esperado = almacenado.split("$")
    except ValueError:
        return False
    if prefijo != PREFIJO:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", texto.encode("utf-8"), bytes.fromhex(salt), int(iteraciones))
    return hmac.compare_digest(dk.hex(), esperado)
