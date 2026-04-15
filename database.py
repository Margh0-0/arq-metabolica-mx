"""
database.py — ARQ-Metabólica MX
Módulo de conexión y operaciones con MySQL Workbench

Instalar dependencia:
    pip install mysql-connector-python

Crear la base de datos primero en MySQL Workbench:
    CREATE DATABASE arq_metabolica CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json

# ═══════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE CONEXIÓN  ← edita estos datos
# ═══════════════════════════════════════════════════════════
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "database": "arq_metabolica",
    "user":     "root",          # tu usuario de MySQL Workbench
    "password": "tu_password",   # tu contraseña de MySQL Workbench
}


# ═══════════════════════════════════════════════════════════
#  CONEXIÓN
# ═══════════════════════════════════════════════════════════
def get_connection():
    """Retorna una conexión activa a MySQL."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] No se pudo conectar: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  INICIALIZAR TABLAS (ejecutar una sola vez)
# ═══════════════════════════════════════════════════════════
def init_db():
    """
    Crea todas las tablas si no existen.
    Llama esta función al iniciar la app.
    """
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    try:
        # ── Tabla: municipios ──────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS municipios (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                nombre      VARCHAR(120) NOT NULL UNIQUE,
                AV          FLOAT NOT NULL COMMENT 'Áreas Verdes (0-1)',
                IC          FLOAT NOT NULL COMMENT 'Índice Caminabilidad (0-1)',
                ED          FLOAT NOT NULL COMMENT 'Equipamiento Deportivo (0-1)',
                EAR         FLOAT NOT NULL COMMENT 'Entorno Alimentario Riesgo (0-1)',
                IM          FLOAT NOT NULL COMMENT 'Índice Marginación (0-1)',
                fuente      VARCHAR(200) DEFAULT 'Manual',
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """)

        # ── Tabla: encuestas (respuestas del usuario) ──────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encuestas (
                id              INT AUTO_INCREMENT PRIMARY KEY,
                municipio_id    INT,
                nombre_usuario  VARCHAR(100) DEFAULT 'Anónimo',
                edad            INT,
                genero          VARCHAR(20),
                -- Hábitos personales (de la encuesta)
                actividad_fisica    TINYINT(1) DEFAULT 0  COMMENT '1=sí hace ejercicio',
                min_ejercicio_sem   INT DEFAULT 0          COMMENT 'minutos/semana',
                consume_ultraprocesados TINYINT(1) DEFAULT 0,
                acceso_areas_verdes TINYINT(1) DEFAULT 0,
                camina_diario   TINYINT(1) DEFAULT 0,
                -- Valores IARRI calculados con sus respuestas
                AV_enc          FLOAT,
                IC_enc          FLOAT,
                ED_enc          FLOAT,
                EAR_enc         FLOAT,
                IM_enc          FLOAT,
                iarri_resultado FLOAT,
                nivel_riesgo    VARCHAR(10),
                prob_ri         FLOAT,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (municipio_id) REFERENCES municipios(id) ON DELETE SET NULL
            ) ENGINE=InnoDB;
        """)

        # ── Tabla: calculos_historicos ─────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculos_historicos (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                municipio_id INT,
                encuesta_id  INT,
                AV           FLOAT NOT NULL,
                IC           FLOAT NOT NULL,
                ED           FLOAT NOT NULL,
                EAR          FLOAT NOT NULL,
                IM           FLOAT NOT NULL,
                iarri        FLOAT NOT NULL,
                nivel_riesgo VARCHAR(10),
                prob_ri      FLOAT,
                mc_media     FLOAT,
                mc_desv      FLOAT,
                mc_ci_lo     FLOAT,
                mc_ci_hi     FLOAT,
                origen       VARCHAR(50) DEFAULT 'calculadora' COMMENT 'calculadora|encuesta|importacion',
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (municipio_id) REFERENCES municipios(id) ON DELETE SET NULL,
                FOREIGN KEY (encuesta_id)  REFERENCES encuestas(id)  ON DELETE SET NULL
            ) ENGINE=InnoDB;
        """)

        # ── Tabla: importaciones CSV/Excel ─────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS importaciones (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                archivo     VARCHAR(200),
                filas_ok    INT DEFAULT 0,
                filas_error INT DEFAULT 0,
                detalle     JSON,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;
        """)

        conn.commit()

        # Insertar municipios base si la tabla está vacía
        cursor.execute("SELECT COUNT(*) FROM municipios")
        if cursor.fetchone()[0] == 0:
            _seed_municipios(cursor, conn)

        print("[DB] Base de datos inicializada correctamente ✓")
        return True

    except Error as e:
        print(f"[DB ERROR] init_db: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def _seed_municipios(cursor, conn):
    """Inserta los 3 municipios base de Puebla."""
    datos = [
        ("San Andrés Cholula",      0.80, 0.60, 0.40, 0.45, 0.10, "Datos base IARRI-MX"),
        ("San Pablo Xochimehuacan", 0.50, 0.35, 0.20, 0.60, 0.55, "Datos base IARRI-MX"),
        ("Cuautlancingo",           0.30, 0.20, 0.10, 0.80, 0.70, "Datos base IARRI-MX"),
    ]
    cursor.executemany("""
        INSERT INTO municipios (nombre, AV, IC, ED, EAR, IM, fuente)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, datos)
    conn.commit()
    print("[DB] Municipios base insertados ✓")


# ═══════════════════════════════════════════════════════════
#  MUNICIPIOS
# ═══════════════════════════════════════════════════════════
def get_municipios():
    """
    Retorna lista de municipios desde la BD.
    Formato compatible con el dict MUNICIPIOS del main.py
    """
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM municipios ORDER BY nombre")
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] get_municipios: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def upsert_municipio(nombre, AV, IC, ED, EAR, IM, fuente="Manual"):
    """
    Inserta o actualiza un municipio.
    Retorna el id del registro.
    """
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO municipios (nombre, AV, IC, ED, EAR, IM, fuente)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                AV=VALUES(AV), IC=VALUES(IC), ED=VALUES(ED),
                EAR=VALUES(EAR), IM=VALUES(IM), fuente=VALUES(fuente)
        """, (nombre, AV, IC, ED, EAR, IM, fuente))
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"[DB ERROR] upsert_municipio: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════════════
#  ENCUESTAS
# ═══════════════════════════════════════════════════════════
def guardar_encuesta(datos: dict):
    """
    Guarda las respuestas de una encuesta.

    datos = {
        "municipio_id": 1,
        "nombre_usuario": "Juan",
        "edad": 30,
        "genero": "M",
        "actividad_fisica": True,
        "min_ejercicio_sem": 150,
        "consume_ultraprocesados": False,
        "acceso_areas_verdes": True,
        "camina_diario": True,
        # Valores derivados del cálculo IARRI:
        "AV_enc": 0.7, "IC_enc": 0.6, "ED_enc": 0.5,
        "EAR_enc": 0.3, "IM_enc": 0.4,
        "iarri_resultado": 0.42,
        "nivel_riesgo": "Medio",
        "prob_ri": 0.31,
    }
    Retorna el id de la encuesta guardada.
    """
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO encuestas (
                municipio_id, nombre_usuario, edad, genero,
                actividad_fisica, min_ejercicio_sem,
                consume_ultraprocesados, acceso_areas_verdes, camina_diario,
                AV_enc, IC_enc, ED_enc, EAR_enc, IM_enc,
                iarri_resultado, nivel_riesgo, prob_ri
            ) VALUES (
                %(municipio_id)s, %(nombre_usuario)s, %(edad)s, %(genero)s,
                %(actividad_fisica)s, %(min_ejercicio_sem)s,
                %(consume_ultraprocesados)s, %(acceso_areas_verdes)s, %(camina_diario)s,
                %(AV_enc)s, %(IC_enc)s, %(ED_enc)s, %(EAR_enc)s, %(IM_enc)s,
                %(iarri_resultado)s, %(nivel_riesgo)s, %(prob_ri)s
            )
        """, datos)
        conn.commit()
        enc_id = cursor.lastrowid
        # También registrar en historial
        _guardar_calculo(cursor, conn,
            municipio_id=datos.get("municipio_id"),
            encuesta_id=enc_id,
            vals={k: datos[k] for k in ["AV_enc","IC_enc","ED_enc","EAR_enc","IM_enc"]},
            iarri=datos["iarri_resultado"],
            nivel=datos["nivel_riesgo"],
            prob=datos["prob_ri"],
            origen="encuesta"
        )
        return enc_id
    except Error as e:
        print(f"[DB ERROR] guardar_encuesta: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_encuestas(municipio_id=None, limit=50):
    """Retorna encuestas, opcionalmente filtradas por municipio."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        if municipio_id:
            cursor.execute("""
                SELECT e.*, m.nombre AS municipio_nombre
                FROM encuestas e
                LEFT JOIN municipios m ON e.municipio_id = m.id
                WHERE e.municipio_id = %s
                ORDER BY e.created_at DESC LIMIT %s
            """, (municipio_id, limit))
        else:
            cursor.execute("""
                SELECT e.*, m.nombre AS municipio_nombre
                FROM encuestas e
                LEFT JOIN municipios m ON e.municipio_id = m.id
                ORDER BY e.created_at DESC LIMIT %s
            """, (limit,))
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] get_encuestas: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════════════
#  CÁLCULOS HISTÓRICOS
# ═══════════════════════════════════════════════════════════
def guardar_calculo(municipio_id, AV, IC, ED, EAR, IM,
                    iarri, nivel, prob,
                    mc_media=None, mc_desv=None, mc_ci_lo=None, mc_ci_hi=None,
                    origen="calculadora"):
    """
    Guarda el resultado de un cálculo IARRI en el historial.
    Llama esto desde build_calculadora cuando el usuario presiona calcular.
    """
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        _guardar_calculo(cursor, conn,
            municipio_id=municipio_id,
            encuesta_id=None,
            vals={"AV_enc": AV, "IC_enc": IC, "ED_enc": ED, "EAR_enc": EAR, "IM_enc": IM},
            iarri=iarri, nivel=nivel, prob=prob,
            mc_media=mc_media, mc_desv=mc_desv,
            mc_ci_lo=mc_ci_lo, mc_ci_hi=mc_ci_hi,
            origen=origen
        )
        return cursor.lastrowid
    except Error as e:
        print(f"[DB ERROR] guardar_calculo: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def _guardar_calculo(cursor, conn, municipio_id, encuesta_id, vals,
                     iarri, nivel, prob,
                     mc_media=None, mc_desv=None, mc_ci_lo=None, mc_ci_hi=None,
                     origen="calculadora"):
    """Interno: inserta en calculos_historicos."""
    cursor.execute("""
        INSERT INTO calculos_historicos (
            municipio_id, encuesta_id,
            AV, IC, ED, EAR, IM,
            iarri, nivel_riesgo, prob_ri,
            mc_media, mc_desv, mc_ci_lo, mc_ci_hi, origen
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        municipio_id, encuesta_id,
        vals.get("AV_enc", vals.get("AV")),
        vals.get("IC_enc", vals.get("IC")),
        vals.get("ED_enc", vals.get("ED")),
        vals.get("EAR_enc", vals.get("EAR")),
        vals.get("IM_enc", vals.get("IM")),
        iarri, nivel, prob,
        mc_media, mc_desv, mc_ci_lo, mc_ci_hi, origen
    ))
    conn.commit()


def get_historial(municipio_id=None, limit=100):
    """Retorna el historial de cálculos IARRI."""
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    try:
        if municipio_id:
            cursor.execute("""
                SELECT c.*, m.nombre AS municipio_nombre
                FROM calculos_historicos c
                LEFT JOIN municipios m ON c.municipio_id = m.id
                WHERE c.municipio_id = %s
                ORDER BY c.created_at DESC LIMIT %s
            """, (municipio_id, limit))
        else:
            cursor.execute("""
                SELECT c.*, m.nombre AS municipio_nombre
                FROM calculos_historicos c
                LEFT JOIN municipios m ON c.municipio_id = m.id
                ORDER BY c.created_at DESC LIMIT %s
            """, (limit,))
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] get_historial: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════════════
#  ESTADÍSTICAS CALCULADAS (para la pantalla de reportes)
# ═══════════════════════════════════════════════════════════
def get_estadisticas_municipio(municipio_id):
    """
    Retorna estadísticas agregadas de un municipio:
    promedio IARRI, total encuestas, distribución de riesgo, etc.
    """
    conn = get_connection()
    if not conn:
        return {}
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                COUNT(*)                        AS total_calculos,
                AVG(iarri)                      AS iarri_promedio,
                MIN(iarri)                      AS iarri_min,
                MAX(iarri)                      AS iarri_max,
                AVG(prob_ri)                    AS prob_ri_promedio,
                SUM(nivel_riesgo = 'Bajo')      AS casos_bajo,
                SUM(nivel_riesgo = 'Medio')     AS casos_medio,
                SUM(nivel_riesgo = 'Alto')      AS casos_alto
            FROM calculos_historicos
            WHERE municipio_id = %s
        """, (municipio_id,))
        stats = cursor.fetchone()

        # Tendencia: últimas 10 mediciones
        cursor.execute("""
            SELECT iarri, created_at
            FROM calculos_historicos
            WHERE municipio_id = %s
            ORDER BY created_at DESC LIMIT 10
        """, (municipio_id,))
        stats["tendencia"] = cursor.fetchall()

        # Promedio hábitos de encuestas
        cursor.execute("""
            SELECT
                AVG(actividad_fisica)           AS pct_activos,
                AVG(consume_ultraprocesados)    AS pct_ultra,
                AVG(acceso_areas_verdes)        AS pct_av,
                AVG(camina_diario)              AS pct_caminan,
                AVG(min_ejercicio_sem)          AS min_ejercicio_prom
            FROM encuestas
            WHERE municipio_id = %s
        """, (municipio_id,))
        stats["habitos"] = cursor.fetchone()

        return stats
    except Error as e:
        print(f"[DB ERROR] get_estadisticas_municipio: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()


def get_estadisticas_globales():
    """Estadísticas de todos los municipios combinados."""
    conn = get_connection()
    if not conn:
        return {}
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                m.nombre,
                COUNT(c.id)     AS total,
                AVG(c.iarri)    AS iarri_prom,
                AVG(c.prob_ri)  AS prob_prom
            FROM municipios m
            LEFT JOIN calculos_historicos c ON c.municipio_id = m.id
            GROUP BY m.id, m.nombre
            ORDER BY iarri_prom DESC
        """)
        return cursor.fetchall()
    except Error as e:
        print(f"[DB ERROR] get_estadisticas_globales: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


# ═══════════════════════════════════════════════════════════
#  IMPORTACIÓN CSV/EXCEL
# ═══════════════════════════════════════════════════════════
def importar_desde_csv(filepath: str):
    """
    Importa datos de municipios o encuestas desde un CSV.

    Formato esperado del CSV:
        nombre,AV,IC,ED,EAR,IM
        San Andrés Cholula,0.80,0.60,0.40,0.45,0.10

    Retorna dict con conteos de filas_ok y filas_error.
    """
    import csv

    ok, err, detalle = 0, 0, []

    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    upsert_municipio(
                        nombre=row["nombre"].strip(),
                        AV=float(row["AV"]),
                        IC=float(row["IC"]),
                        ED=float(row["ED"]),
                        EAR=float(row["EAR"]),
                        IM=float(row["IM"]),
                        fuente=f"CSV: {filepath}",
                    )
                    ok += 1
                except Exception as e:
                    err += 1
                    detalle.append(str(e))
    except Exception as e:
        detalle.append(f"Error leyendo archivo: {e}")

    # Registrar la importación
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO importaciones (archivo, filas_ok, filas_error, detalle)
            VALUES (%s, %s, %s, %s)
        """, (filepath, ok, err, json.dumps(detalle)))
        conn.commit()
        cursor.close()
        conn.close()

    print(f"[DB] Importación completada: {ok} OK, {err} errores")
    return {"ok": ok, "error": err, "detalle": detalle}
