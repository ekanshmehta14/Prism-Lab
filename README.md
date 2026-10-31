# Prism Spectrometer Physics Lab

A Streamlit application for an interactive prism-spectrometer practical. It includes a mouse/touch telescope component, mercury line reference data, four first/second-order left/right groups, observation management, local OCR workflow, calculations, plots, PDF/CSV/JSON exports and viva support.

## Run locally

Python 3.11 is recommended.

```powershell
cd "prism-spectrometer-lab"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

The exact start command is also:

```text
streamlit run app.py
```

Tesseract is optional. When the Python wrapper cannot find a Tesseract executable, OCR reports low confidence and manual reading entry remains available. The app never sends uploaded images to an external OCR service.

## Deploy to Streamlit Community Cloud

1. Put this project in a GitHub repository.
2. Commit `app.py`, `requirements.txt`, source folders and the `.streamlit` configuration.
3. Open Streamlit Community Cloud and create an app from the repository.
4. Select `app.py` as the entry point.
5. Deploy and verify the virtual telescope, scanner and exports.

## Tests

```text
pytest -q
```

The virtual telescope drag component uses a local HTML/CSS/JavaScript front end and sends angle values back to Streamlit. Browser testing still needs verification on the target desktop/mobile device.
