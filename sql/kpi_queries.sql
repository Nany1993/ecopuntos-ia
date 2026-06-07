# KPIs SmartSort — consultas de referencia

-- Éxito por caneca
SELECT
    caneca_qr,
    COUNT(*) FILTER (WHERE resultado_intento = 'correcto') AS correctos,
    COUNT(*) FILTER (WHERE resultado_intento = 'incorrecto') AS incorrectos,
    ROUND(100.0 * COUNT(*) FILTER (WHERE resultado_intento = 'correcto')
        / NULLIF(COUNT(*) FILTER (WHERE resultado_intento IN ('correcto', 'incorrecto')), 0), 2) AS tasa_exito
FROM registro_intentos
GROUP BY caneca_qr;

-- Éxito por área
SELECT
    area,
    ROUND(100.0 * COUNT(*) FILTER (WHERE resultado_intento = 'correcto')
        / NULLIF(COUNT(*) FILTER (WHERE resultado_intento IN ('correcto', 'incorrecto')), 0), 2) AS tasa_exito_area
FROM registro_intentos
GROUP BY area;

-- First Time Right
SELECT
    ROUND(100.0 * COUNT(DISTINCT id_sesion) FILTER (WHERE numero_intento = 1 AND resultado_intento = 'correcto')
        / NULLIF(COUNT(DISTINCT id_sesion), 0), 2) AS first_time_right
FROM registro_intentos;

-- Intentos promedio hasta éxito
SELECT AVG(max_intento) AS intentos_promedio
FROM (
    SELECT id_sesion, MAX(numero_intento) AS max_intento
    FROM registro_intentos
    WHERE id_sesion IN (
        SELECT id_sesion FROM sesiones WHERE estado_sesion = 'CERRADA_EXITOSA'
    )
    GROUP BY id_sesion
) t;

-- Cumplimiento SLA (ajusta umbral según config)
SELECT
    ROUND(100.0 * COUNT(*) FILTER (WHERE tiempo_respuesta_ms <= 5000) / COUNT(*), 2) AS cumplimiento_sla
FROM registro_intentos;
