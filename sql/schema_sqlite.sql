-- ECOPUNTOS IA — Esquema SQLite (piloto local)

CREATE TABLE IF NOT EXISTS catalogo_canecas (
    id_caneca TEXT PRIMARY KEY,
    area TEXT NOT NULL,
    color_caneca TEXT NOT NULL CHECK (color_caneca IN ('blanca', 'verde', 'negra')),
    estado_caneca TEXT NOT NULL DEFAULT 'activa',
    latitud REAL,
    longitud REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sesiones (
    id_sesion TEXT PRIMARY KEY,
    id_colaborador TEXT NOT NULL,
    id_caneca_inicial TEXT NOT NULL,
    id_caneca_actual TEXT,
    estado_sesion TEXT NOT NULL,
    numero_intento_actual INTEGER NOT NULL DEFAULT 0,
    creada_en TEXT NOT NULL,
    actualizada_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registro_intentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_sesion TEXT NOT NULL,
    numero_intento INTEGER NOT NULL,
    fecha_hora_evento TEXT NOT NULL,
    id_colaborador TEXT NOT NULL,
    id_caneca TEXT NOT NULL,
    caneca_qr TEXT NOT NULL,
    area TEXT NOT NULL,
    prediccion_ia TEXT,
    nivel_confianza REAL,
    explicacion_breve TEXT,
    resultado_intento TEXT NOT NULL,
    mensaje_enviado TEXT NOT NULL,
    confirmacion_deposito INTEGER,
    tiempo_respuesta_ms INTEGER NOT NULL DEFAULT 0,
    estado_sesion TEXT NOT NULL,
    proveedor_ia TEXT,
    respaldo_activado INTEGER NOT NULL DEFAULT 0,
    codigo_error TEXT,
    acierto_primera INTEGER NOT NULL DEFAULT 0,
    puntos_otorgados INTEGER NOT NULL DEFAULT 0,
    UNIQUE (id_sesion, numero_intento)
);

CREATE TABLE IF NOT EXISTS puntos_colaborador (
    id_colaborador TEXT PRIMARY KEY,
    puntos_totales INTEGER NOT NULL DEFAULT 0,
    aciertos_primera INTEGER NOT NULL DEFAULT 0,
    sesiones_completadas INTEGER NOT NULL DEFAULT 0,
    ultima_actualizacion TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS colaboradores (
    id_colaborador TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    username_telegram TEXT,
    es_semilla INTEGER NOT NULL DEFAULT 0,
    registrado_en TEXT NOT NULL,
    ultima_actividad TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_registro_intentos_sesion ON registro_intentos(id_sesion);
CREATE INDEX IF NOT EXISTS idx_registro_intentos_colaborador ON registro_intentos(id_colaborador);
CREATE INDEX IF NOT EXISTS idx_colaboradores_semilla ON colaboradores(es_semilla);
