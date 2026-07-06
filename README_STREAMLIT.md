# Streamlit Web App

## Quick Start

Install dependencies from the root requirements file:

```powershell
python -m pip install -r requirements.txt
```

Run the app:

```powershell
streamlit run solidification_tool/streamlit_app/app.py
```

The app opens at `http://localhost:8501`.

## Streamlit Cloud

Use:

- Branch: `codex-dig-in`
- Main file path: `solidification_tool/streamlit_app/app.py`
- Dependency file: root `requirements.txt`

## Features

- Alloy presets for baseline Fe-Ni-Cr, Al 6061, and a Ni-based superalloy
- Sidebar controls for heat transfer, composition, model parameters, and plot visibility
- Results, physics summary, raw data, and help tabs
- Downloads for compressed result arrays and input JSON

## Current Architecture

The Streamlit app does not call engine internals directly. It uses:

- `solidification_tool.app_api.run_model()` for simulation
- `solidification_tool.app_api.build_figures()` for plotting
- `solidification_tool.streamlit_app.caching.get_or_run_simulation()` for Streamlit-specific caching

This keeps the UI replaceable and the physics engine independent.

## Testing

Run:

```powershell
python -m unittest discover -s tests -p "test*.py"
```

The tests verify that the Streamlit and Qt UIs only cross into the engine through `app_api`, that the engine remains UI-independent, and that default engine runs and save/load round trips work.

## Troubleshooting

If the app will not start:

```powershell
python --version
python -m pip install --upgrade -r requirements.txt
streamlit run solidification_tool/streamlit_app/app.py --logger.level=debug
```

For Streamlit Cloud, confirm the main file path is exactly `solidification_tool/streamlit_app/app.py`.

