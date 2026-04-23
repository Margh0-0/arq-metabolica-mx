import flet as ft
import json
import os
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

VERDE_OSCURO  = "#1B5E20"
VERDE_MEDIO   = "#2E7D32"
VERDE_CLARO   = "#66BB6A"
BLANCO        = "#FFFFFF"
BLANCO_SUAVE  = "#E8F5E9"

SESION_FILE = "sesion_local.json"


# ═══════════════════════════════════════════════════════════
#  SESIÓN PERSISTENTE
# ═══════════════════════════════════════════════════════════

def guardar_sesion(user):
    """Guarda los tokens de sesión en un archivo local."""
    try:
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


def borrar_sesion():
    """Elimina el archivo de sesión local."""
    if os.path.exists(SESION_FILE):
        os.remove(SESION_FILE)


def obtener_usuario_actual():
    """Devuelve el usuario activo o intenta restaurar desde archivo."""
    try:
        sesion = supabase.auth.get_session()
        if sesion and sesion.user:
            return sesion.user
    except:
        pass
    return cargar_sesion()


def cerrar_sesion():
    """Cierra sesión en Supabase y borra el archivo local."""
    try:
        supabase.auth.sign_out()
    except:
        pass
    borrar_sesion()


# ═══════════════════════════════════════════════════════════
#  PANTALLA LOGIN
# ═══════════════════════════════════════════════════════════

def pantalla_login(page: ft.Page, on_login_exitoso):
    email_field = ft.TextField(
        label="Correo electronico",
        hint_text="tu@correo.com",
        keyboard_type=ft.KeyboardType.EMAIL,
        width=300,
        border_color=VERDE_CLARO,
        focused_border_color=BLANCO,
        label_style=ft.TextStyle(color=BLANCO_SUAVE),
        text_style=ft.TextStyle(color=BLANCO),
        cursor_color=BLANCO,
        hint_style=ft.TextStyle(color="#80FFFFFF"),
    )
    password_field = ft.TextField(
        label="Contrasena",
        password=True,
        can_reveal_password=True,
        width=300,
        border_color=VERDE_CLARO,
        focused_border_color=BLANCO,
        label_style=ft.TextStyle(color=BLANCO_SUAVE),
        text_style=ft.TextStyle(color=BLANCO),
        cursor_color=BLANCO,
    )
    error_text = ft.Text("", color="#FF8A80", size=13, text_align=ft.TextAlign.CENTER)
    loading = ft.ProgressRing(visible=False, width=22, height=22, color=BLANCO)

    def hacer_login(e):
        if not email_field.value or not password_field.value:
            error_text.value = "Por favor completa todos los campos"
            page.update()
            return
        loading.visible = True
        error_text.value = ""
        page.update()
        try:
            respuesta = supabase.auth.sign_in_with_password({
                "email": email_field.value.strip(),
                "password": password_field.value,
            })
            loading.visible = False
            guardar_sesion(respuesta.user)  # ← guarda sesión local
            on_login_exitoso(respuesta.user)
        except Exception:
            loading.visible = False
            error_text.value = "Correo o contrasena incorrectos"
            page.update()

    def ir_a_registro(e):
        page.views.clear()
        page.views.append(pantalla_registro(page, on_login_exitoso))
        page.update()

    vista = ft.View(route="/login", bgcolor=VERDE_OSCURO)
    vista.controls.append(
        ft.Container(
            expand=True,
            bgcolor=VERDE_OSCURO,
            padding=ft.padding.symmetric(horizontal=30, vertical=20),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(height=20),
                    ft.Container(
                        width=100, height=100,
                        border_radius=20,
                        bgcolor=VERDE_MEDIO,
                        alignment=ft.alignment.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.HOME_WORK_ROUNDED, size=54, color=BLANCO),
                    ),
                    ft.Text("ARQ-Metabolica MX", size=26, weight=ft.FontWeight.BOLD,
                            color=BLANCO, text_align=ft.TextAlign.CENTER),
                    ft.Text("Diseno del entorno para prevenir\nresistencia a la insulina",
                            size=13, color=BLANCO_SUAVE, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=6),
                    ft.Container(
                        width=320, padding=ft.padding.all(20),
                        border_radius=16, bgcolor=VERDE_MEDIO,
                        content=ft.Column(
                            spacing=14,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text("Iniciar Sesion", size=18,
                                        weight=ft.FontWeight.BOLD, color=BLANCO),
                                email_field,
                                password_field,
                                error_text,
                                ft.Row([loading], alignment=ft.MainAxisAlignment.CENTER),
                                ft.ElevatedButton(
                                    "Entrar a la app",
                                    on_click=hacer_login,
                                    width=260, height=44,
                                    icon=ft.Icons.LOGIN_ROUNDED,
                                    style=ft.ButtonStyle(
                                        bgcolor=VERDE_CLARO, color=VERDE_OSCURO,
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                    ),
                                ),
                            ],
                        ),
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text("No tienes cuenta?", color=BLANCO_SUAVE, size=13),
                            ft.TextButton("Registrate aqui", on_click=ir_a_registro,
                                          style=ft.ButtonStyle(color=VERDE_CLARO)),
                        ],
                    ),
                ],
            ),
        )
    )
    return vista


# ═══════════════════════════════════════════════════════════
#  PANTALLA REGISTRO
# ═══════════════════════════════════════════════════════════

def pantalla_registro(page: ft.Page, on_registro_exitoso):
    nombre_field = ft.TextField(
        label="Nombre completo", width=260,
        border_color=VERDE_CLARO, focused_border_color=BLANCO,
        label_style=ft.TextStyle(color=BLANCO_SUAVE),
        text_style=ft.TextStyle(color=BLANCO), cursor_color=BLANCO,
    )
    email_field = ft.TextField(
        label="Correo electronico", keyboard_type=ft.KeyboardType.EMAIL, width=260,
        border_color=VERDE_CLARO, focused_border_color=BLANCO,
        label_style=ft.TextStyle(color=BLANCO_SUAVE),
        text_style=ft.TextStyle(color=BLANCO), cursor_color=BLANCO,
    )
    password_field = ft.TextField(
        label="Contrasena (min. 6 caracteres)", password=True,
        can_reveal_password=True, width=260,
        border_color=VERDE_CLARO, focused_border_color=BLANCO,
        label_style=ft.TextStyle(color=BLANCO_SUAVE),
        text_style=ft.TextStyle(color=BLANCO), cursor_color=BLANCO,
    )
    municipio_field = ft.Dropdown(
        label="Tu municipio", width=260,
        color=BLANCO, focused_border_color=BLANCO, border_color=VERDE_CLARO,
        label_style=ft.TextStyle(color=BLANCO_SUAVE),
        options=[
            ft.dropdown.Option("San Andres Cholula"),
            ft.dropdown.Option("San Pablo Xochimehuacan"),
            ft.dropdown.Option("Cuautlancingo"),
            ft.dropdown.Option("Otro"),
        ],
        value="San Andres Cholula",
    )
    error_text = ft.Text("", color="#FF8A80", size=13, text_align=ft.TextAlign.CENTER)
    loading = ft.ProgressRing(visible=False, width=22, height=22, color=BLANCO)

    def hacer_registro(e):
        if not nombre_field.value or not email_field.value or not password_field.value:
            error_text.value = "Por favor completa todos los campos"
            page.update()
            return
        if len(password_field.value) < 6:
            error_text.value = "La contrasena debe tener al menos 6 caracteres"
            page.update()
            return
        loading.visible = True
        error_text.value = ""
        page.update()
        try:
            respuesta = supabase.auth.sign_up({
                "email": email_field.value.strip(),
                "password": password_field.value,
            })
            supabase.table("perfiles").insert({
                "id": respuesta.user.id,
                "nombre": nombre_field.value.strip(),
                "municipio_actual": municipio_field.value,
            }).execute()
            loading.visible = False
            guardar_sesion(respuesta.user)  # ← guarda sesión local
            on_registro_exitoso(respuesta.user)
        except Exception as ex:
            loading.visible = False
            error_text.value = f"Error: {str(ex)}"
            page.update()

    def ir_a_login(e):
        page.views.clear()
        page.views.append(pantalla_login(page, on_registro_exitoso))
        page.update()

    vista = ft.View(route="/registro", bgcolor=VERDE_OSCURO)
    vista.controls.append(
        ft.Container(
            expand=True,
            bgcolor=VERDE_OSCURO,
            padding=ft.padding.symmetric(horizontal=30, vertical=20),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(height=20),
                    ft.Container(
                        width=70, height=70, border_radius=14,
                        bgcolor=VERDE_MEDIO,
                        alignment=ft.alignment.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.PERSON_ADD_ROUNDED, size=36, color=BLANCO),
                    ),
                    ft.Text("Crear cuenta", size=24, weight=ft.FontWeight.BOLD, color=BLANCO),
                    ft.Text("Unete a ARQ-Metabolica MX", size=13, color=BLANCO_SUAVE),
                    ft.Container(
                        width=320, padding=ft.padding.all(20),
                        border_radius=16, bgcolor=VERDE_MEDIO,
                        content=ft.Column(
                            spacing=12,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                nombre_field,
                                email_field,
                                password_field,
                                municipio_field,
                                error_text,
                                ft.Row([loading], alignment=ft.MainAxisAlignment.CENTER),
                                ft.ElevatedButton(
                                    "Crear mi cuenta",
                                    on_click=hacer_registro,
                                    width=260, height=44,
                                    icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
                                    style=ft.ButtonStyle(
                                        bgcolor=VERDE_CLARO, color=VERDE_OSCURO,
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                    ),
                                ),
                            ],
                        ),
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Text("Ya tienes cuenta?", color=BLANCO_SUAVE, size=13),
                            ft.TextButton("Inicia sesion", on_click=ir_a_login,
                                          style=ft.ButtonStyle(color=VERDE_CLARO)),
                        ],
                    ),
                ],
            ),
        )
    )
    return vista