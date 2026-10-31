import json
import os


def _api_key():
    key = os.getenv("GEMINI_API_KEY", "")
    if key:
        return key
    try:
        import streamlit as st
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


def read_spectrometer_scale(image, model="gemini-2.5-flash"):
    api_key = _api_key()
    if not api_key:
        return {
            "ok": False,
            "error": "Missing GEMINI_API_KEY. Add it under Streamlit Secrets.",
            "main_scale": None,
            "vernier": None,
            "confidence": 0.0,
        }

    try:
        import streamlit as st
        model = str(st.secrets.get("GEMINI_MODEL", model)).strip() or model
    except Exception:
        model = os.getenv("GEMINI_MODEL", model).strip() or model

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return {
            "ok": False,
            "error": "The google-genai package is not installed.",
            "main_scale": None,
            "vernier": None,
            "confidence": 0.0,
        }

    prompt = (
        "You are reading a laboratory prism spectrometer image. "
        "Return only a JSON object. Identify the main-scale degree closest to "
        "the Vernier index line and identify the Vernier division aligned with "
        "a main-scale line. Do not infer from unrelated numbers in the photo. "
        "Main scale must be from 30 to 359 degrees. Vernier must be from 0 to 60. "
        'If either value is unreadable, use null. Return: '
        '{"main_scale": number or null, "vernier": number or null, '
        '"confidence": number from 0 to 1}.'
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )
        raw = (response.text or "").strip()
        parsed = json.loads(raw)
        main_scale = parsed.get("main_scale")
        vernier = parsed.get("vernier")
        confidence = float(parsed.get("confidence", 0))

        if main_scale is not None:
            main_scale = float(main_scale)
            if not 30 <= main_scale <= 359:
                main_scale = None
        if vernier is not None:
            vernier = float(vernier)
            if not 0 <= vernier <= 60:
                vernier = None
        confidence = max(0.0, min(1.0, confidence))

        return {
            "ok": main_scale is not None or vernier is not None,
            "error": None if main_scale is not None or vernier is not None else "The API could not read a valid scale value.",
            "main_scale": main_scale,
            "vernier": vernier,
            "confidence": confidence,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Gemini API error: {exc}",
            "main_scale": None,
            "vernier": None,
            "confidence": 0.0,
        }
