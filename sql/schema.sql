-- ECOPUNTOS IA — Esquema Supabase/PostgreSQL

CREATE TABLE IF NOT EXISTS catalogo_canecas (
    id_caneca TEXT PRIMARY KEY,
    area TEXT NOT NULL,
    color_caneca TEXT NOT NULL CHECK (color_caneca IN ('blanca', 'verde', 'negra')),
    estado_caneca TEXT NOT NULL DEFAULT 'activa' CHECK (estado_caneca IN ('activa', 'inactiva')),
    latitud DOUBLE PRECISION,
    longitud DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sesiones (
    id_sesion TEXT PRIMARY KEY,
    id_colaborador TEXT NOT NULL,
    id_caneca_inicial TEXT NOT NULL REFERENCES catalogo_canecas(id_caneca),
    id_caneca_actual TEXT REFERENCES catalogo_canecas(id_caneca),
    estado_sesion TEXT NOT NULL,
    numero_intento_actual INTEGER NOT NULL DEFAULT 0,
    creada_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizada_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS registro_intentos (
    id BIGSERIAL PRIMARY KEY,
    id_sesion TEXT NOT NULL REFERENCES sesiones(id_sesion),
    numero_intento INTEGER NOT NULL,
    fecha_hora_evento TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    id_colaborador TEXT NOT NULL,
    id_caneca TEXT NOT NULL REFERENCES catalogo_canecas(id_caneca),
    caneca_qr TEXT NOT NULL,
    area TEXT NOT NULL,
    prediccion_ia TEXT,
    nivel_confianza DOUBLE PRECISION,
    explicacion_breve TEXT,
    resultado_intento TEXT NOT NULL CHECK (resultado_intento IN ('correcto', 'incorrecto', 'error')),
    mensaje_enviado TEXT NOT NULL,
    confirmacion_deposito BOOLEAN,
    tiempo_respuesta_ms INTEGER NOT NULL DEFAULT 0,
    estado_sesion TEXT NOT NULL,
    proveedor_ia TEXT,
    respaldo_activado BOOLEAN NOT NULL DEFAULT FALSE,
    codigo_error TEXT,
    UNIQUE (id_sesion, numero_intento)
);

CREATE INDEX IF NOT EXISTS idx_registro_intentos_sesion ON registro_intentos(id_sesion);
CREATE INDEX IF NOT EXISTS idx_registro_intentos_colaborador ON registro_intentos(id_colaborador);
CREATE INDEX IF NOT EXISTS idx_registro_intentos_fecha ON registro_intentos(fecha_hora_evento);

CREATE OR REPLACE VIEW v_kpi_resumen AS
SELECT
    COUNT(DISTINCT id_sesion) AS sesiones_totales,
    COUNT(*) FILTER (WHERE resultado_intento = 'correcto') AS intentos_correctos,
    COUNT(*) FILTER (WHERE resultado_intento = 'incorrecto') AS intentos_incorrectos,
    COUNT(*) FILTER (WHERE resultado_intento = 'error') AS intentos_error,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE resultado_intento = 'correcto')
        / NULLIF(COUNT(*) FILTER (WHERE resultado_intento IN ('correcto', 'incorrecto')), 0),
        2
    ) AS tasa_exito_global
FROM registro_intentos;
