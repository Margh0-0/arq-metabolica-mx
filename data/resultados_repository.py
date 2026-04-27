"""
data/resultados_repository.py — ARQ-Metabólica MX
Persistencia de resultados IARRI y progreso de retos en Supabase.
"""
import datetime
from data.supabase_client import get_client


def guardar_resultado_iarri(usuario_id: str, municipio: str, iarri_total: float, nivel_riesgo: str) -> dict | None:
    """
    Inserta un registro en la tabla resultados_iarri.
    Columnas: id (auto), usuario_id (uuid), municipio (text), iarri_total (float), nivel_riesgo (text), created_at (auto)
    Retorna el registro insertado o None si falla.
    """
    try:
        supabase = get_client()
        respuesta = (
            supabase.table("resultados_iarri")
            .insert({
                "usuario_id":  usuario_id,
                "municipio":   municipio,
                "iarri_total": iarri_total,
                "nivel_riesgo": nivel_riesgo,
            })
            .execute()
        )
        return respuesta.data[0] if respuesta.data else None
    except Exception as ex:
        print(f"[repo] error: {ex}")
        return None


def obtener_historial_iarri(usuario_id: str) -> list[dict]:
    """
    Retorna todos los resultados del usuario ordenados por created_at desc.
    """
    try:
        supabase = get_client()
        respuesta = (
            supabase.table("resultados_iarri")
            .select("*")
            .eq("usuario_id", usuario_id)
            .order("created_at", desc=True)
            .execute()
        )
        return respuesta.data if respuesta.data else []
    except Exception as ex:
        print(f"[repo] error: {ex}")
        return []


def guardar_progreso_reto(usuario_id: str, reto_id: int, semana: int, anio: int, completado: bool = True) -> dict | None:
    """
    Inserta o actualiza el progreso de un reto para el usuario.
    Columnas: id (auto), usuario_id (uuid FK→perfiles), reto_id (int), completado (bool default false), semana (int NOT NULL), anio (int NOT NULL), created_at (auto)
    Retorna el registro o None si falla.
    """
    try:
        supabase = get_client()
        respuesta = (
            supabase.table("progreso_retos")
            .upsert(
                {
                    "usuario_id": usuario_id,
                    "reto_id":    reto_id,
                    "semana":     semana,
                    "anio":       anio,
                    "completado": completado,
                },
                on_conflict="usuario_id,reto_id",
            )
            .execute()
        )
        return respuesta.data[0] if respuesta.data else None
    except Exception as ex:
        print(f"[repo] error: {ex}")
        return None


def obtener_retos_completados(usuario_id: str) -> list[int]:
    """
    Retorna lista de reto_id (int) completados por el usuario.
    Filtra por completado=True.
    """
    try:
        supabase = get_client()
        respuesta = (
            supabase.table("progreso_retos")
            .select("reto_id")
            .eq("usuario_id", usuario_id)
            .eq("completado", True)
            .execute()
        )
        return [row["reto_id"] for row in respuesta.data] if respuesta.data else []
    except Exception as ex:
        print(f"[repo] error: {ex}")
        return []
