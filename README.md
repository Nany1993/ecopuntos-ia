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
3. Si acertaste a la **primera**, responde **`sí`** para confirmar el depósito y ganar EcoPuntos (ver [Sistema de EcoPuntos](#sistema-de-ecopuntos))

**Comandos del bot:** `/puntos` · `/ranking` · `/canecas` · `/ayuda`

**Canecas del piloto:** `CAN-BLANCA-01/02` · `CAN-VERDE-01/02` · `CAN-NEGRA-01/02`

---

## Sistema de EcoPuntos

Gamificación para incentivar la **segregación correcta a la primera**. Los puntos se acumulan por colaborador (ID de Telegram) y aparecen en el bot y en el dashboard.

### Cuándo se ganan puntos

| Condición | ¿EcoPuntos? |
|-----------|-------------|
| Clasificación **correcta en el 1.er intento** (IA coincide con la caneca escaneada) **y** confirmas el depósito con **`sí`** | **Sí** — +`PUNTOS_ACIERTO_PRIMERA` (por defecto **10 pts**) |
| Aciertas en el 2.º o 3.er intento (tras corregir caneca) | **No** — 0 pts |
| Clasificación incorrecta y la sesión se cierra por máximo de intentos | **No** |
| Respondes **`no`** a la confirmación de depósito | **No** — la sesión sigue abierta para otra foto |
| Pasan **15 min** sin confirmar el depósito tras clasificación correcta | **No** — sesión cerrada automáticamente |
| Inactividad prolongada o tiempo máximo de sesión | **No** — sesión cerrada automáticamente |

### Flujo resumido

```
Escaneas QR → Envías foto → IA dice "correcto"
        ↓
Respondes "sí" (confirmas que depositaste) → cierre exitoso de sesión
        ↓
¿Fue tu 1.er intento en esa sesión? → Sí → +10 EcoPuntos (configurable)
                                      → No → 0 pts (sesión OK, sin bonus)
```

Si la IA dice **incorrecto**, escanea el QR de la caneca recomendada (o escribe `CAN-VERDE-01`): **sigue siendo la misma sesión**, se reutiliza la clasificación de tu foto y **no necesitas enviar otra imagen**. La sesión solo cierra con éxito al confirmar el depósito con **`sí`**. Si no confirmas en **15 minutos**, el bot cierra la sesión y te avisa por Telegram. También se cierra sin puntos al agotar los 3 intentos o por inactividad.

### Qué se registra por usuario

| Métrica | Significado |
|---------|-------------|
| **EcoPuntos totales** | Suma acumulada de todos los bonos ganados |
| **Aciertos al 1.er intento** | Veces que clasificó bien a la primera y confirmó |
| **Sesiones completadas** | Depósitos confirmados con clasificación correcta |

> **Límite del prototipo actual:** la confirmación con **`sí`** es una **autodeclaración** del usuario. El sistema verifica la **clasificación** (caneca escaneada vs. predicción IA), pero **no comprueba físicamente** que el residuo entró en la caneca. Ver [Líneas futuras](#líneas-futuras-no-incluidas-en-el-prototipo-actual).

### Configuración

En `.env`:

```env
PUNTOS_ACIERTO_PRIMERA=10   # Puntos por acierto a la 1.ª + confirmación
MAXIMO_INTENTOS=3           # Intentos máximos por sesión antes de cerrarla
TIEMPO_CONFIRMACION_MIN=15  # Minutos para confirmar depósito tras acierto
```

Puedes cambiar `PUNTOS_ACIERTO_PRIMERA` (por ejemplo a `5` o `20`); reinicia el bot para aplicar el valor.

### Consultar puntos y ranking

- **Telegram:** `/puntos` (tu saldo) · `/ranking` (top 10)
- **Dashboard:** sección *Ranking EcoPuntos* en http://127.0.0.1:8501

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

## Líneas futuras (no incluidas en el prototipo actual)

Lo descrito a continuación son **posibles evoluciones** del sistema. **Ninguna está implementada** en esta versión del piloto. El alcance actual termina en: QR + foto + clasificación IA + confirmación voluntaria + EcoPuntos + dashboard.

### Qué verifica hoy el prototipo vs. qué no

| Aspecto | ¿Incluido en el prototipo? |
|---------|----------------------------|
| Caneca escaneada (QR) | **Sí** |
| Clasificación del residuo por IA (foto) | **Sí** |
| Coincidencia caneca ↔ tipo de residuo | **Sí** |
| Reintentos sin nueva foto (misma sesión) | **Sí** |
| Confirmación de depósito (`sí` / `no`) | **Sí** — autodeclaración |
| Comprobación física de que el residuo se depositó | **No** |
| Sensores en la caneca | **No** |
| Evidencia post-depósito (foto, doble QR, GPS) | **No** |

### Verificación del depósito (evidencia digital)

Mejoras posibles **sin hardware adicional** en la caneca:

| Mejora | Idea | Beneficio | Limitación |
|--------|------|-----------|------------|
| **Foto post-depósito** | Tras acertar, pedir una segunda foto del residuo dentro de la caneca | Evidencia visual | Simulable; más costo de IA |
| **Doble escaneo QR** | Exigir re-escanear la caneca correcta *después* de depositar | Prueba de presencia en el punto | No garantiza que tiró *ese* residuo |
| **Geolocalización** | Comparar ubicación del móvil con coordenadas de la caneca | Refuerzo de proximidad | Imprecisa en interiores; permisos del usuario |

En base de datos se podría distinguir, en una versión futura:

- `confirmacion_deposito` — lo que reporta el usuario (ya existe).
- `deposito_verificado` — evidencia objetiva (sensor, doble QR, foto validada).
- `metodo_verificacion` — p. ej. `autodeclaracion` · `doble_qr` · `foto_post` · `sensor`.

Así el dashboard podría separar **“aciertos de clasificación”** de **“depósitos verificados”**.

### IoT en la caneca (hardware)

Evolución hacia **comprobación física real** en 1–2 canecas piloto:

| Sensor / dispositivo | Qué detectaría |
|---------------------|----------------|
| **Apertura de tapa** (ESP32 + hall / microswitch) | Que alguien abrió la caneca en la ventana de tiempo de la sesión |
| **Célula de carga (peso)** | Incremento de masa tras el depósito |
| **Nivel de llenado** (ultrasonido / IR) | Aumento de volumen en el intervalo sesión → confirmación |
| **Cámara en caneca** | Objeto depositado; con más esfuerzo, tipo de material |

Requiere conectividad, energía, mantenimiento y consideraciones de privacidad — fuera del alcance del prototipo software actual.

### Enfoque por capas (roadmap sugerido)

```
Capa 1 (prototipo actual):  IA + QR + confirmación "sí"           → hábito y gamificación
Capa 2 (futuro cercano):    Re-escaneo QR en caneca correcta      → prueba de presencia
Capa 3 (futuro):            Foto post-depósito                    → evidencia visual
Capa 4 (futuro / IoT):      Sensor de tapa o peso en caneca       → depósito verificado
Capa 5 (complemento):       Auditoría humana periódica            → validación en campo
```

### Otras mejoras posibles

- **Supabase en producción** — backend remoto ya previsto en el código, no activo en el piloto local.
- **Notificaciones push** además del cierre por timeout (recordatorio antes de los 15 min).
- **Roles de administrador** — revisión manual de sesiones sospechosas.
- **Integración con building management** — KPIs de segregación por piso o edificio.

---

## Solución de problemas

| Problema | Solución |
|----------|----------|
| `python` no reconocido | Reinstala Python con "Add to PATH" o usa `py -m venv .venv` en Windows |
| `Entorno virtual no encontrado` | Ejecuta `.\scripts\setup.ps1` o `./scripts/setup.sh` |
| `Falta .env` | Copia `.env.example` a `.env` y agrega tus claves |
| Bot no responde | Verifica `TELEGRAM_BOT_TOKEN` y que la terminal del bot siga activa |
| Error 409 Conflict (dos instancias) | Ejecuta `.\scripts\stop_bot.ps1` y luego **una sola vez** `.\scripts\start.ps1` |
| Error al clasificar imagen | Revisa `GEMINI_API_KEY` y conexión a internet |
| QR abre otro bot | Corrige `TELEGRAM_BOT_USERNAME` en `.env` y ejecuta `python -m scripts.generate_qr` |
| Dashboard vacío | Ejecuta `python -m scripts.seed_demo_data --limpiar` o usa el bot para generar datos reales |
| Error de columnas en BD tras actualizar | Borra `data/smartsort.db` y ejecuta `python -m scripts.init_db` |
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
