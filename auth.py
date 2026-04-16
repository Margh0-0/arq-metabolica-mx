import flet as ft
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def obtener_usuario_actual():
    try:
        sesion = supabase.auth.get_session()
        return sesion.user if sesion else None
    except:
        return None

def cerrar_sesion():
    supabase.auth.sign_out()

def pantalla_login(page: ft.Page, on_login_exitoso):
    email_field = ft.TextField(label="Correo electronico", width=320)
    password_field = ft.TextField(label="Contrasena", password=True, can_reveal_password=True, width=320)
    error_text = ft.Text("", color=ft.Colors.RED_400, size=13)

    def hacer_login(e):
        if not email_field.value or not password_field.value:
            error_text.value = "Por favor completa todos los campos"
            page.update()
            return
        try:
            respuesta = supabase.auth.sign_in_with_password({
                "email": email_field.value.strip(),
                "password": password_field.value,
            })
            on_login_exitoso(respuesta.user)
        except Exception as ex:
            error_text.value = "Correo o contrasena incorrectos"
            page.update()

    def ir_a_registro(e):
        page.go("/registro")

    return ft.View(
        "/login",
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("ARQ-Metabolica MX", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Inicia sesion para continuar", size=14, color=ft.Colors.GREY_600),
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        email_field,
                        password_field,
                        error_text,
                        ft.ElevatedButton("Iniciar sesion", on_click=hacer_login, width=320,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)),
                        ft.TextButton("No tienes cuenta? Registrate", on_click=ir_a_registro),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=40,
                alignment=ft.alignment.center,
                expand=True,
            )
        ]
    )

def pantalla_registro(page: ft.Page, on_registro_exitoso):
    nombre_field = ft.TextField(label="Nombre completo", width=320)
    email_field = ft.TextField(label="Correo electronico", width=320)
    password_field = ft.TextField(label="Contrasena (minimo 6 caracteres)", password=True, can_reveal_password=True, width=320)
    error_text = ft.Text("", color=ft.Colors.RED_400, size=13)

    def hacer_registro(e):
        if not nombre_field.value or not email_field.value or not password_field.value:
            error_text.value = "Por favor completa todos los campos"
            page.update()
            return
        if len(password_field.value) < 6:
            error_text.value = "La contrasena debe tener al menos 6 caracteres"
            page.update()
            return
        try:
            respuesta = supabase.auth.sign_up({
                "email": email_field.value.strip(),
                "password": password_field.value,
            })
            supabase.table("perfiles").insert({
                "id": respuesta.user.id,
                "nombre": nombre_field.value.strip(),
                "municipio_actual": "San Andres Cholula",
            }).execute()
            on_registro_exitoso(respuesta.user)
        except Exception as ex:
            error_text.value = f"Error al registrarse: {str(ex)}"
            page.update()

    def ir_a_login(e):
        page.go("/login")

    return ft.View(
        "/registro",
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Crear cuenta", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Unete a ARQ-Metabolica MX", size=14, color=ft.Colors.GREY_600),
                        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                        nombre_field,
                        email_field,
                        password_field,
                        error_text,
                        ft.ElevatedButton("Registrarme", on_click=hacer_registro, width=320,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)),
                        ft.TextButton("Ya tienes cuenta? Inicia sesion", on_click=ir_a_login),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                padding=40,
                alignment=ft.alignment.center,
                expand=True,
            )
        ]
    )
