"""
ARQ-Metabólica MX — App Móvil con Flet (Python + Flutter)
Índice Arquitectónico de Riesgo de Resistencia a la Insulina (IARRI-MX)

Instalar:  pip install flet numpy scipy
Correr:    python main.py
APK:       flet build apk
iOS:       flet build ipa
"""

import flet as ft
from ui.app_shell import main

if __name__ == "__main__":
    ft.app(target=main)
