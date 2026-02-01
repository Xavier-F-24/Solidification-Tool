import matplotlib.pyplot as plt

from scipy.interpolate import interp1d

import numpy as np

from solidification_tool.io_utils.spacing import normalize_spacing_um

def plot_pdas(pdas_curves, G_env, V_max_env, V_min_env, color_map, dry_run, ax):
    shown_spacings = set()
    
    for lam, data in pdas_curves.items():
        G = data["G"]
        V = data["V"]

        # --- interpolation (unchanged) ---
        Vmin_of_G = interp1d(G_env, V_min_env, bounds_error=False, fill_value=np.nan)
        Vmax_of_G = interp1d(G_env, V_max_env, bounds_error=False, fill_value=np.nan)

        V_min_interp = Vmin_of_G(G)
        V_max_interp = Vmax_of_G(G)

        valid = (
            np.isfinite(G) &
            np.isfinite(V) &
            np.isfinite(V_min_interp) &
            (V >= V_min_interp) &
            (V <= V_max_interp)
        )

        G_trim = G[valid]
        V_trim = V[valid]

        if not np.any(np.isfinite(V_trim)):
            continue

        lam_um = normalize_spacing_um(lam)
        
        shown_spacings.add(lam_um)

        if dry_run == False:
            color = color_map[lam_um]
            ax.loglog(
                G_trim,
                V_trim,
                color=color,
                linestyle="-",
                linewidth=2
            )

    return shown_spacings