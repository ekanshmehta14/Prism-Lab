# Prism Lab v2
Streamlit prism-spectrometer lab with Gemini scale reading.

    pip install -r requirements.txt
    streamlit run app.py

Gemini key: set `GEMINI_API_KEY` in Streamlit Cloud's secrets settings, or in `.streamlit/secrets.toml` locally:

    GEMINI_API_KEY = "your-api-key"

Optional: `GEMINI_MODEL` env var to change the model (default gemini-2.5-flash).
