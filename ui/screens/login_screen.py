"""
ui/screens/login_screen.py — ARQ-Metabólica MX
Pantallas de Login y Registro — extraídas de auth.py en F6 del refactor arquitectural.
UI pura: no importa auth.py ni ningún módulo legacy.
"""

import flet as ft

from data.auth_repository import iniciar_sesion, registrar_usuario

VERDE_OSCURO  = "#1B5E20"
VERDE_MEDIO   = "#2E7D32"
VERDE_CLARO   = "#66BB6A"
BLANCO        = "#FFFFFF"
BLANCO_SUAVE  = "#E8F5E9"


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
            user = iniciar_sesion(email_field.value.strip(), password_field.value)
            loading.visible = False
            on_login_exitoso(user)
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
            user = registrar_usuario(
                email=email_field.value.strip(),
                password=password_field.value,
                nombre=nombre_field.value.strip(),
                municipio=municipio_field.value or "San Andres Cholula",
            )
            loading.visible = False
            on_registro_exitoso(user)
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
