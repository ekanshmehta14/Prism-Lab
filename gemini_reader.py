"""Read a spectrometer scale from a photo with Gemini (structured JSON output)."""
import io
from PIL import Image
from pydantic import BaseModel, Field

DEFAULT_MODEL = "gemini-3.5-flash"

PROMPT = """You are reading a circular spectrometer scale (main scale plus vernier) from a photo.
1. main_scale_deg: the main-scale value (decimal degrees) of the last mark at or before the vernier zero.
   Main-scale marks are usually every 0.5 degree; add 0.5 for a half-degree mark.
2. vernier_division: the vernier line number that exactly coincides with a main-scale line.
3. vernier_total_divisions: number of divisions on the whole vernier (commonly 30).
4. main_division_deg: value of one main-scale division in degrees (commonly 0.5).
5. confidence: 0 to 1. Lower it for blur, glare, or two neighbouring vernier lines that look equally aligned.
6. notes: one short sentence on anything uncertain.
Never guess silently: if a value is unreadable, return your best estimate with low confidence and say so in notes."""


class ScaleReading(BaseModel):
    main_scale_deg: float = Field(description="Main scale reading in degrees")
    vernier_division: int = Field(description="Coinciding vernier division")
    vernier_total_divisions: int = Field(default=30)
    main_division_deg: float = Field(default=0.5)
    confidence: float = Field(ge=0, le=1)
    notes: str = ""


def read_scale(image: Image.Image, api_key: str, model: str = DEFAULT_MODEL) -> dict:
    if not api_key:
        return {"ok": False, "error": "No Gemini API key. Add GEMINI_API_KEY to Streamlit secrets."}
    try:
        from google import genai
        from google.genai import types

        img = image.convert("RGB")
        img.thumbnail((1600, 1600))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        client = genai.Client(api_key=api_key)
        try:
            resp = client.models.generate_content(
                model=model,
                contents=[types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"), PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ScaleReading,
                    temperature=0,
                ),
            )
        except Exception:
            if model == DEFAULT_MODEL:
                raise
            resp = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=[types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"), PROMPT],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ScaleReading,
                    temperature=0,
                ),
            )
        r = resp.parsed or ScaleReading.model_validate_json(resp.text)
        lc = r.main_division_deg / max(r.vernier_total_divisions, 1)
        return {"ok": True, "main": r.main_scale_deg, "vernier": r.vernier_division,
                "least_count": lc, "confidence": r.confidence, "notes": r.notes}
    except Exception as exc:  # network, quota, bad key, unreadable response
        return {"ok": False, "error": f"Gemini request failed: {exc}"}
