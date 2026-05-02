# ARQ-Metabólica MX 🏛️📱

### App Móvil con Flet (Python + Flutter)

**Índice Arquitectónico de Riesgo de Resistencia a la Insulina (IARRI-MX)**

---

## ▶️ Correr en desarrollo

```bash
# 1. Copiar variables de entorno
cp .env.example .env
# (Editar .env con tus credenciales de Supabase)

# 2. Instalar dependencias
pip install -e ".[dev]"

# 3. Correr la app
python main.py
```

---

## 📱 Compilar APK para Android

### Requisitos

- Python 3.9+
- Flutter SDK → https://flutter.dev/docs/get-started/install
- Android Studio + Android SDK

```bash
# Compilar APK
flet build apk

# El APK quedará en:
#   build/apk/arq-metabolica-mx.apk

# Instalar en el celular (USB + modo desarrollador)
adb install build/apk/arq-metabolica-mx.apk
```

---

## 🍎 Compilar para iOS (solo macOS)

```bash
flet build ipa
```

---

## 📁 Estructura del proyecto

```
metabolica-mx/
├── main.py               ← Punto de entrada
├── pyproject.toml        ← Dependencias y configuración
├── .env.example          ← Plantilla de variables de entorno
│
├── config/               ← Configuración (settings, carga de .env)
├── core/                 ← Lógica de negocio (IARRI, IARM, datos)
├── data/                 ← Repositorios y cliente Supabase
├── ui/                   ← Interfaz de usuario
│   ├── app_shell.py      ← Shell principal y navegación
│   ├── theme.py          ← Colores y estilos globales
│   ├── components/       ← Componentes reutilizables
│   └── screens/          ← Pantallas de la app
├── assets/               ← Recursos estáticos (mapa HTML, etc.)
└── tests/                ← Tests unitarios
```

---

## 📱 Pantallas de la App

| Pantalla | Descripción |
|----------|-------------|
| 🔐 **Login** | Autenticación con Supabase |
| 🏠 **Inicio** | Selector de municipio, IARRI en grande, semáforo, variables territoriales |
| 🗺️ **Mapa** | Mapa interactivo con heatmaps y comparativa municipal |
| 🧮 **Calcular** | Sliders interactivos, cálculo en tiempo real, Monte Carlo |
| 🛡️ **Intervención** | Recomendaciones, simulación arquitectónica, insignias gamificadas |
| 📚 **Educación** | Lecciones y quiz IARRI |
| 👤 **Perfil** | Datos del usuario y configuración |

---

## 🧮 Fórmula IARRI

```
IARRI = 0.20(1−AV) + 0.25(1−IC) + 0.15(1−ED) + 0.25(EAR) + 0.15(IM)
```

| Var | Descripción | Peso |
|-----|-------------|------|
| AV  | Áreas Verdes (OMS 9 m²/hab) | 0.20 |
| IC  | Índice de Caminabilidad | 0.25 |
| ED  | Equipamiento Deportivo | 0.15 |
| EAR | Entorno Alimentario Riesgoso | 0.25 |
| IM  | Índice de Marginación (CONAPO) | 0.15 |

---

## 📊 Resultados — 3 Municipios de Puebla

| Municipio | IARRI | Riesgo |
|-----------|-------|--------|
| San Andrés Cholula | 0.36 | Medio |
| San Pablo Xochimehuacan | 0.62 | Medio-Alto |
| Cuautlancingo | 0.78 | Alto |

---

## 🧪 Tests

```bash
pytest tests/
```

---

## 🎯 ODS 3 — Salud  ·  ODS 11 — Ciudades Sostenibles
