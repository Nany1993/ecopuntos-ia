# ECOPUNTOS IA

Prototipo IoT para **segregación adecuada de residuos** en oficinas, con guía en tiempo real, trazabilidad y gamificación (EcoPuntos).

## ¿Por qué es un sistema IoT?

El objetivo no es automatizar la recolección, sino **reducir errores de segregación en la fuente** (Resolución 2184 de 2019 — código blanco, verde, negro).

| Capa IoT | Rol en el proyecto |
|----------|-------------------|
| **Cosa (Thing)** | Smartphone del colaborador |
| **Sensor** | Cámara — captura la imagen del residuo |
| **Identificación física** | QR en cada caneca (`id_caneca`, área, color) |
| **Conectividad** | Internet — Telegram + APIs en la nube |
| **Procesamiento** | IA (Gemini) — clasifica el residuo y compara con la caneca |
| **Actuador / feedback** | Pantalla + bot Telegram — guía y corrige al usuario |
| **Datos y analítica** | SQLite + dashboard — KPIs de segregación |

**Flujo:** el usuario escanea la caneca → envía foto → el sistema indica si va a tirar bien o mal → confirma el depósito → se registran intentos, EcoPuntos e indicadores ambientales.

---

## Requisitos previos

| Requisito | Detalle |
|-----------|---------|
| **Python** | 3.11 o superior ([python.org](https://www.python.org/downloads/)) |
| **Git** | Para clonar el repositorio ([git-scm.com](https://git-scm.com/)) |
| **Internet** | Telegram y Gemini funcionan en la nube |
| **Cuenta Telegram** | Para crear el bot en [@BotFather](https://t.me/BotFather) |
| **API Key Gemini** | Gratis en [Google AI Studio](https://aistudio.google.com/apikey) |

> **Windows:** al instalar Python, marca la opción **"Add Python to PATH"**.

---

## Instalación rápida (clonar y ejecutar)

### 1. Clonar el repositorio

```bash
git clone https://github.com/Nany1993/ecopuntos-ia.git
cd ecopuntos-ia
```

### 2. Instalar todo (un solo comando)

**Windows (PowerShell):**

```powershell
.\scripts\setup.ps1
```

**Linux / macOS:**

```bash
chmod +x scripts/setup.sh scripts/start.sh scripts/start_dashboard.sh
./scripts/setup.sh
```

El script crea el entorno virtual, instala dependencias, copia `.env.example` → `.env`, inicializa la base de datos y genera los QR en `output/qr/`.

### 3. Configurar claves (obligatorio)

Abre el archivo `.env` en la raíz del proyecto y completa:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...        # Token de @BotFather
TELEGRAM_BOT_USERNAME=TuBotSinArroba             # Ej: ClasificadorResiduosbot
GEMINI_API_KEY=AIza...                           # Google AI Studio
```

**Cómo obtener el token de Telegram:**

1. Abre [@BotFather](https://t.me/BotFather) en Telegram.
2. Envía `/newbot` y sigue los pasos.
3. Copia el token que te entrega.
4. El **username** es el nombre que termina en `bot` (sin `@`).

> **Importante:** `TELEGRAM_BOT_USERNAME` debe coincidir con tu bot. Los QR se generan con ese nombre; si lo cambias, vuelve a ejecutar `python -m scripts.generate_qr`.

### 4. Arrancar el sistema (dos terminales)

**Terminal 1 — Bot de Telegram**

| Windows | Linux / macOS |
|---------|---------------|
| `.\scripts\start.ps1` | `./scripts/start.sh` |

**Terminal 2 — Dashboard web**

| Windows | Linux / macOS |
|---------|---------------|
| `.\scripts\start_dashboard.ps1` | `./scripts/start_dashboard.sh` |

Abre en el navegador: **http://127.0.0.1:8501**

---

## Probar en Telegram

1. Escanea un QR de `output/qr/` **o** escribe en el bot: `/start CAN-BLANCA-01`
2. Envía una **foto** del residuo (espera ~20–30 s)
3. Si acertaste a la primera, responde **`sí`** para confirmar y ganar EcoPuntos (+10 pts)

**Comandos del bot:** `/puntos` · `/ranking` · `/canecas` · `/ayuda`

**Canecas del piloto:** `CAN-BLANCA-01/02` · `CAN-VERDE-01/02` · `CAN-NEGRA-01/02`

---

## Instalación manual (paso a paso)

Si prefieres no usar los scripts de setup:

```bash
# 1. Entorno virtual
python -m venv .venv

# 2. Activar (elige tu sistema)
# Windows:  .venv\Scripts\Activate.ps1
# Linux/Mac: source .venv/bin/activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Configuración
copy .env.example .env      # Windows
# cp .env.example .env      # Linux/Mac
# Editar .env con tus claves

# 5. Base de datos y QR
python -m scripts.init_db
python -m scripts.generate_qr

# 6. (Opcional) Datos demo para el dashboard
python -m scripts.seed_demo_data --limpiar
```

---

## Arquitectura

```
Caneca física (QR) → Smartphone (cámara)
        ↓
   Bot Telegram → SessionService → Gemini (IA)
        ↓
   SQLite (data/smartsort.db)
        ↓
   Dashboard — KPIs de segregación + EcoPuntos
```

## Qué incluye

| Componente | Descripción |
|------------|-------------|
| Bot Telegram | Captura fotos, feedback y EcoPuntos |
| Clasificación IA | Gemini 2.5 Flash (+ GPT opcional) |
| Motor de sesiones | Reglas, reintentos, comparación caneca vs predicción |
| SQLite | Persistencia local (`data/smartsort.db`) |
| Dashboard | KPIs, ranking EcoPuntos, gráficos (Streamlit) |
| Generador QR | 6 canecas del piloto en `output/qr/` |

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `python` no reconocido | Reinstala Python con "Add to PATH" o usa `py -m venv .venv` en Windows |
| `Entorno virtual no encontrado` | Ejecuta `.\scripts\setup.ps1` o `./scripts/setup.sh` |
| `Falta .env` | Copia `.env.example` a `.env` y agrega tus claves |
| Bot no responde | Verifica `TELEGRAM_BOT_TOKEN` y que la terminal del bot siga activa |
| Error al clasificar imagen | Revisa `GEMINI_API_KEY` y conexión a internet |
| QR abre otro bot | Corrige `TELEGRAM_BOT_USERNAME` en `.env` y ejecuta `python -m scripts.generate_qr` |
| Dashboard vacío | Ejecuta `python -m scripts.seed_demo_data --limpiar` o usa el bot para generar datos reales |
| Puerto 8501 ocupado | Cierra otra instancia de Streamlit o cambia el puerto en el comando |

---

## Estructura del proyecto

```
ecopuntos-ia/
├── .env.example          # Plantilla de configuración (copiar a .env)
├── requirements.txt
├── scripts/
│   ├── setup.ps1 / setup.sh       # Instalación inicial
│   ├── start.ps1 / start.sh       # Bot Telegram
│   ├── start_dashboard.ps1 / .sh  # Dashboard web
│   ├── init_db.py
│   ├── generate_qr.py
│   └── seed_demo_data.py
├── src/
│   ├── bot/telegram_bot.py
│   ├── dashboard/                 # Streamlit + Plotly
│   ├── services/                  # IA, sesiones, EcoPuntos
│   ├── database.py
│   └── models.py
├── sql/schema_sqlite.sql
├── data/                          # Se crea al iniciar (no se sube a Git)
└── output/qr/                     # QR generados (no se sube a Git)
```

---

## Variables de entorno (`.env`)

| Variable | Obligatorio | Descripción |
|----------|-------------|-------------|
| `TELEGRAM_BOT_TOKEN` | Sí | Token del bot |
| `TELEGRAM_BOT_USERNAME` | Sí | Username del bot (sin `@`) |
| `GEMINI_API_KEY` | Sí | Clave de Google AI Studio |
| `GEMINI_MODEL` | No | Por defecto `gemini-2.5-flash` |
| `OPENAI_API_KEY` | No | Respaldo si Gemini falla |
| `PUNTOS_ACIERTO_PRIMERA` | No | EcoPuntos por acierto 1ra (default: 10) |
| `SQLITE_PATH` | No | Ruta BD (default: `data/smartsort.db`) |

> **Nunca subas `.env` a GitHub.** Contiene claves secretas. El archivo ya está en `.gitignore`.

---

## Licencia y uso

Proyecto académico / piloto IoT. Usa tus propias claves de Telegram y Gemini; cada persona que clone el repo debe crear su bot y su `.env`.
