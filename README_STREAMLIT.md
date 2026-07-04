# Streamlit Web App for Solidification Simulator

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_streamlit.txt
```

### 2. Run the App
```bash
streamlit run solidification_tool/streamlit_app/app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Features

### 📋 Presets
- **Fe-Ni-Cr (Baseline)**: Iron-nickel-chromium stainless steel (MTGN 4XX class)
- **Al 6061**: Aluminum alloy
- **Ni-based Superalloy**: Nickel-based superalloy

Load any preset with one click to get started.

### 🎛️ Interactive Controls
All 16 input parameters are adjustable via sliders and number inputs:
- Heat transfer properties
- Alloy composition (dynamic per number of solutes)
- Model parameters (Gamma, freezing range, nucleation)

### 📈 Real-Time Visualization
Five physics models coupled together:
1. **Heat Transfer**: G-V diagram
2. **IMS**: Ivantsov Multiple Solutes undercooling model
3. **Stability**: Planar-dendritic transition boundaries
4. **PDAS/SDAS**: Dendrite arm spacing maps
5. **CET**: Columnar-to-equiaxed transition

### 📊 Results Tabs
- **Results**: High-quality matplotlib figures
- **Physics**: Key metrics and summary statistics
- **Data**: Export raw values as CSV
- **Help**: Model documentation and references

### 💾 Export Options
- **Results (NPZ)**: Binary numpy format with all data
- **Inputs (JSON)**: Reproducible parameter set
- **Figures (PNG)**: Individual plot exports

---

## Architecture

### File Structure
```
solidification_tool/streamlit_app/
├── app.py                 # Main Streamlit app
├── config.py              # Presets and app settings
├── caching.py             # Performance optimization (multi-stage caching)
├── inputs_ui.py           # Sidebar input widgets
└── results_display.py     # Tab panels and visualization
```

### Caching Strategy
Multi-level caching ensures fast re-runs:
1. **Heat Transfer Cache**: < 0.1s (algebraic)
2. **IMS Solver Cache**: 1-2s (vectorized)
3. **Stability & Fits Cache**: < 0.1s (array ops)
4. **PDAS/SDAS Cache**: 0.2s each
5. **CET Cache**: 0.3s (root solve)

When you adjust an input, only affected downstream stages recompute.

---

## Customization

### Add New Alloy Preset
Edit `solidification_tool/streamlit_app/config.py`:

```python
PRESETS["My Alloy"] = {
    "name": "My Alloy",
    "description": "Description here",
    "heat_transfer": {
        "k_l": 30.5,
        # ... other params
    },
    # ...
}
```

### Adjust Visualization
In the sidebar, toggle which models to display:
- Show/hide PDAS, SDAS, CET independently
- Customize IMS G-range for detailed analysis

### Change Figure Sizes
Edit `config.py`:
```python
FIG_SIZE_DEFAULT = (12, 8)  # width, height
FIG_DPI = 200  # resolution
```

---

## Physics Modeling

### IMS (Ivantsov Multiple Solutes)
The core physics model solves for dendritic growth in multi-element alloys.
Outputs a 3D array: [G, Solute, Peclet number]

Key outputs:
- **Tip radius (R)**: Spatial scale of dendrite tips
- **Dendrite velocity (V)**: Growth speed
- **Total undercooling (ΔT)**: Compositional + curvature
- **Stability field**: Valid (G, V, Pe) combinations

### Power Law Fits
At the desired thermal gradient (default 1e5 K/m), the tool fits:
- R(V) = α₁ × V^β₁ → tip radius scaling
- ΔT(V) = α₂ × V^β₂ → undercooling scaling

These fits feed downstream models (PDAS, SDAS, CET).

### PDAS & SDAS
Predict dendrite arm spacing as functions of G and V.
13 logarithmically-spaced values from 1 µm to 1 mm.

### CET
Columnar-to-equiaxed transition boundary based on nucleation kinetics.
Two critical solid fractions: φ = 0.01 (incipient) and φ = 0.50 (substantial).

---

## Performance Tips

1. **First run is slower** (IMS solver is heavy)
2. **Subsequent runs are instant** if inputs unchanged (cached)
3. **Change one parameter at a time** to see exact effects
4. **Export and compare** multiple runs offline

---

## Deployment (Optional)

Deploy to **Streamlit Cloud** for free:

1. Push code to GitHub
2. Sign up at https://streamlit.io/cloud
3. Select repo and branch
4. Streamlit handles deployment automatically

---

## Troubleshooting

### App won't start
```bash
# Check Python version (3.8+)
python --version

# Reinstall dependencies
pip install --upgrade -r requirements_streamlit.txt

# Try with cache cleared
rm -rf ~/.streamlit/cache
streamlit run solidification_tool/streamlit_app/app.py --logger.level=debug
```

### Simulation is slow
- First run: Expected (1-2s for IMS solver)
- Subsequent runs: Should be instant (check sidebar for "Rerun" notice)
- If stuck: Kill and restart the app

### Results look wrong
- Check the **Physics tab** for summary metrics
- Verify inputs are in valid ranges (sidebar shows ranges)
- Try the **Fe-Ni-Cr preset** to compare against known good values

---

## References

- **MTGN 4XX**: Solidification and Phase Transformations, Colorado School of Mines
- **Ivantsov Model**: Classical dendritic growth theory (Ivantsov, 1947)
- **Marginal Stability**: Langer & Müller-Krumbhaar (1978)
- **CET**: Campbell & Blank (1994)

---

## Contributing

Found a bug or have a feature request? Open an issue on GitHub!

---

## License

[Same as main repository]
