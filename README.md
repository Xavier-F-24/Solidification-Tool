# Solidification Tool

Directional solidification modeling toolkit with a Streamlit web app, a Qt desktop app, and a UI-independent physics engine.

## Quick Start

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the Streamlit app:

```powershell
streamlit run solidification_tool/streamlit_app/app.py
```

Run the Qt desktop app:

```powershell
python -m solidification_tool.gui.app
```

## Streamlit Cloud

Use these deployment settings:

- Repository: `Xavier-F-24/Solidification-Tool`
- Branch: `codex-dig-in`
- Main file path: `solidification_tool/streamlit_app/app.py`
- Dependency file: root `requirements.txt`

## Architecture

The UI talks to the engine through `solidification_tool/app_api.py`.

- `solidification_tool/core/engine.py`: simulation orchestration
- `solidification_tool/core/settings.py`: configurable numerical grid defaults
- `solidification_tool/core/validation.py`: engine input and settings validation
- `solidification_tool/visualization/figures.py`: matplotlib figure generation
- `solidification_tool/streamlit_app/`: Streamlit UI
- `solidification_tool/gui/`: Qt UI

The architecture boundary is guarded by tests so UI code does not reach around `app_api`, and engine/model code does not import UI or visualization packages.

## Tests

Run all tests:

```powershell
python -m unittest discover -s tests -p "test*.py"
```

The test suite covers architecture boundaries, input validation, default engine regression behavior, configurable engine settings, and save/load round trips.

