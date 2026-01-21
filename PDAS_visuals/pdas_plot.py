import matplotlib.pyplot as plt

from scipy.interpolate import interp1d

import numpy as np

def plot_pdas(pdas_curves, G_env, V_max_env, V_min_env):
    """
    Plot PDAS G-V curves for prescribed lambda1 values
    """

    for lam, data in pdas_curves.items():
        G = data["G"]
        V = data["V"]

        Vmin_of_G = interp1d(
            G_env,
            V_min_env,
            bounds_error = False,
            fill_value = np.nan
        )

        Vmax_of_G = interp1d(
            G_env,
            V_max_env,
            bounds_error = False,
            fill_value = np.nan
        )

        V_min_interp = Vmin_of_G(G)   # same shape as G
        V_max_interp = Vmax_of_G(G)   # same shape as G

        valid = (
            np.isfinite(G) &
            np.isfinite(V) &
            np.isfinite(V_min_interp) &

            (G >= G_env.min()) &
            (G <= G_env.max()) &

            (V >= V_min_interp) &
            (V <= V_max_interp)
        )

        G_trim = G[valid]
        V_trim = V[valid]

        if np.any(np.isfinite(V_trim)):
            label = f"lambda1 = {lam * 1e6:.0e} micron"
        else:
            label = ""

        plt.loglog(
            G_trim,
            V_trim,
            label = label
        )

    plt.xlabel("Thermal Gradient G (K/m)")
    plt.ylabel("Velocity V (m/s)")
    plt.title("Primary Dendrite Arm Spacing (PDAS) Map")

    plt.grid(True, which="both", ls="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()

