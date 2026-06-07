"""Datos iniciales del piloto SmartSort."""

CANECAS_SEED = [
    {
        "id_caneca": "CAN-BLANCA-01",
        "area": "Piso 1 - Cafetería",
        "color_caneca": "blanca",
        "tipos_residuo_permitidos": [
            "papel", "cartón", "revistas", "carpetas", "sobres", "cajas de cartón",
        ],
    },
    {
        "id_caneca": "CAN-BLANCA-02",
        "area": "Piso 2 - Open Space",
        "color_caneca": "blanca",
        "tipos_residuo_permitidos": ["papel", "cartón", "documentos", "cajas"],
    },
    {
        "id_caneca": "CAN-VERDE-01",
        "area": "Piso 1 - Cafetería",
        "color_caneca": "verde",
        "tipos_residuo_permitidos": [
            "botellas PET", "latas", "vidrio", "envases plásticos", "tapas plásticas",
        ],
    },
    {
        "id_caneca": "CAN-VERDE-02",
        "area": "Piso 2 - Open Space",
        "color_caneca": "verde",
        "tipos_residuo_permitidos": ["botellas", "latas", "envases plásticos"],
    },
    {
        "id_caneca": "CAN-NEGRA-01",
        "area": "Piso 1 - Pasillo",
        "color_caneca": "negra",
        "tipos_residuo_permitidos": [
            "restos de comida", "servilletas usadas", "residuos no aprovechables",
            "pañales", "chicles", "colillas",
        ],
    },
    {
        "id_caneca": "CAN-NEGRA-02",
        "area": "Piso 2 - Baños",
        "color_caneca": "negra",
        "tipos_residuo_permitidos": [
            "papel higiénico", "residuos sanitarios", "residuos no reciclables",
        ],
    },
]

REGLAS_SEED = [
    {
        "tipo_residuo": "botella plástica",
        "caneca_recomendada": "verde",
        "mensaje_educativo": "Las botellas PET van en la caneca verde para reciclaje.",
    },
    {
        "tipo_residuo": "papel",
        "caneca_recomendada": "blanca",
        "mensaje_educativo": "El papel limpio va en la caneca blanca.",
    },
    {
        "tipo_residuo": "servilleta usada",
        "caneca_recomendada": "negra",
        "mensaje_educativo": "Las servilletas usadas van en la caneca negra (no reciclable).",
    },
    {
        "tipo_residuo": "lata de aluminio",
        "caneca_recomendada": "verde",
        "mensaje_educativo": "Las latas metálicas se reciclan en la caneca verde.",
    },
    {
        "tipo_residuo": "restos de comida",
        "caneca_recomendada": "negra",
        "mensaje_educativo": "Los residuos orgánicos no aprovechables van en la caneca negra.",
    },
]
