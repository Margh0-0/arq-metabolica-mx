"""
data/auth_repository.py — ARQ-Metabólica MX
Funciones de autenticación y sesión — sin UI, sin imports de Flet.
"""
import json
import os

from data.supabase_client import get_client

SESION_FILE = "sesion_local.json"


# ═══════════════════════════════════════════════════════════
#  SESIÓN PERSISTENTE
# ═══════════════════════════════════════════════════════════

def guardar_sesion(user) -> None:
    """Guarda los tokens de sesión en un archivo local."""
    try:
        supabase = get_client()
        sesion = supabase.auth.get_session()
        if sesion:
            datos = {
                "access_token":  sesion.access_token,
                "refresh_token": sesion.refresh_token,
                "user_id":       user.id,
                "user_email":    user.email,
            }
            with open(SESION_FILE, "w") as f:
                json.dump(datos, f)
    except Exception as ex:
        print(f"[auth] No se pudo guardar sesion: {ex}")


def cargar_sesion():
    """Intenta restaurar la sesión desde el archivo local."""
    if not os.path.exists(SESION_FILE):
        return None
    try:
        supabase = get_client()
        with open(SESION_FILE, "r") as f:
            datos = json.load(f)
        resultado = supabase.auth.set_session(
            datos["access_token"],
            datos["refresh_token"],
        )
        return resultado.user if resultado else None
    except Exception as ex:
        print(f"[auth] No se pudo restaurar sesion: {ex}")
        borrar_sesion()
        return None


def borrar_sesion() -> None:
    """Elimina el archivo de sesión local."""
    if os.path.exists(SESION_FILE):
        os.remove(SESION_FILE)


def obtener_usuario_actual():
    """Devuelve el usuario activo o intenta restaurar desde archivo."""
    try:
        supabase = get_client()
        sesion = supabase.auth.get_session()
        if sesion and sesion.user:
            return sesion.user
    except Exception:
        pass
    return cargar_sesion()


def cerrar_sesion() -> None:
    """Cierra sesión en Supabase y borra el archivo local."""
    try:
        supabase = get_client()
        supabase.auth.sign_out()
    except Exception:
        pass
    borrar_sesion()


def iniciar_sesion(email: str, password: str):
    """Inicia sesión con email y contraseña. Retorna el usuario o lanza excepción."""
    supabase = get_client()
    respuesta = supabase.auth.sign_in_with_password({
        "email": email.strip(),
        "password": password,
    })
    guardar_sesion(respuesta.user)
    return respuesta.user


def registrar_usuario(email: str, password: str, nombre: str, municipio: str = "San Andres Cholula"):
    """Registra un nuevo usuario en Supabase y guarda su perfil. Retorna el usuario o lanza excepción."""
    supabase = get_client()
    respuesta = supabase.auth.sign_up({
        "email": email.strip(),
        "password": password,
    })
    supabase.table("perfiles").insert({
        "id": respuesta.user.id,
        "nombre": nombre.strip(),
        "municipio_actual": municipio,
    }).execute()
    guardar_sesion(respuesta.user)
    return respuesta.user
