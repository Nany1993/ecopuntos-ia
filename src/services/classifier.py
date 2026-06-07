"""Clasificación de residuos con Gemini (principal) y GPT (respaldo)."""

from __future__ import annotations

import base64
import json
import re
from typing import Any

from src.config import settings
from src.models import CANECAS_COLORES_VALIDOS, ClasificacionIA, ColorCaneca

PROMPT_SISTEMA = """
Eres un clasificador de residuos para oficinas en Colombia según el Código de Colores:
- blanca: papel, cartón, material reciclable limpio no plástico/metal/vidrio
- verde: plásticos, vidrio, metales, envases reciclables
- negra: residuos no aprovechables, orgánicos contaminados, servilletas usadas, etc.

Responde SOLO con JSON válido (sin markdown) con esta estructura exacta:
{
  "prediccion_ia": "blanca|verde|negra",
  "nivel_confianza": 0.0-1.0,
  "explicacion_breve": "máximo 120 caracteres en español"
}
"""


def _normalizar_color(valor: str) -> ColorCaneca | None:
    v = valor.strip().lower()
    if v in CANECAS_COLORES_VALIDOS:
        return v  # type: ignore[return-value]
    aliases = {
        "white": "blanca",
        "green": "verde",
        "black": "negra",
        "blanco": "blanca",
        "verde": "verde",
        "negro": "negra",
    }
    return aliases.get(v)  # type: ignore[return-value]


def _parse_json_respuesta(texto: str) -> dict[str, Any]:
    limpio = texto.strip()
    if limpio.startswith("```"):
        limpio = re.sub(r"^```(?:json)?", "", limpio).strip()
        limpio = re.sub(r"```$", "", limpio).strip()
    return json.loads(limpio)


def _validar_clasificacion(data: dict[str, Any], proveedor: str, respaldo: bool) -> ClasificacionIA:
    color = _normalizar_color(str(data.get("prediccion_ia", "")))
    if not color:
        raise ValueError("prediccion_ia inválida")

    confianza = float(data.get("nivel_confianza", 0))
    confianza = max(0.0, min(1.0, confianza))
    explicacion = str(data.get("explicacion_breve", "")).strip()[:200]

    return ClasificacionIA(
        prediccion_ia=color,
        nivel_confianza=confianza,
        explicacion_breve=explicacion or "Clasificación automática del residuo.",
        proveedor_ia=proveedor,
        respaldo_activado=respaldo,
    )


def clasificar_con_gemini(image_bytes: bytes, mime_type: str = "image/jpeg") -> ClasificacionIA:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY no configurada")

    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    response = model.generate_content(
        [
            PROMPT_SISTEMA,
            {"mime_type": mime_type, "data": image_bytes},
        ],
        generation_config={"temperature": 0.2, "response_mime_type": "application/json"},
    )
    data = _parse_json_respuesta(response.text or "{}")
    return _validar_clasificacion(data, "gemini", respaldo=False)


def clasificar_con_gpt(image_bytes: bytes, mime_type: str = "image/jpeg") -> ClasificacionIA:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY no configurada")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Clasifica el residuo de esta imagen."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    data = json.loads(response.choices[0].message.content or "{}")
    return _validar_clasificacion(data, "gpt", respaldo=True)


def clasificar_imagen(image_bytes: bytes, mime_type: str = "image/jpeg") -> ClasificacionIA:
    try:
        return clasificar_con_gemini(image_bytes, mime_type)
    except Exception:
        if settings.openai_api_key:
            return clasificar_con_gpt(image_bytes, mime_type)
        raise
