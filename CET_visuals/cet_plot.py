import matplotlib.pyplot as plt

import numpy as np

from scipy.interpolate import interp1d

def spacing_to_color(spacings):
    unique = sorted(set(spacings))

    cmap = plt.get_cmap("turbo")
    colors = cmap(np.linspace(0.1, 0.9, len(unique)))

    return {lam_um: color for lam_um, color in zip(unique, colors)}

def plot_cet(cet_results, phi_list, G_out, V_max_env, V_min_env, ax):
    """
    Plot CET G-V curves
    """

    # Map values to colors using Turbo colormap
    cet_colors = spacing_to_color(phi_list)

    for phi, data in cet_results.items():
        G = data["G"]
        V = data["V"]

        if np.any(np.isfinite(V)):
            label = f"Phi = {phi}"
        else:
            label = ""

        G = np.concatenate([ [np.min(G_out)], G ])
        V = np.concatenate([ [V[0]], V])

        ax.loglog(
            G, #_trim,
            V, #_trim,
            label = label,
            color = cet_colors[phi],
            #marker = "*",
            linestyle = "-",
            linewidth = 2
        )

    ax.set_xlabel("Thermal Gradient G (K/m)")
    ax.set_ylabel("Velocity V (m/s)")
    ax.set_title("CET Map")
    ax.grid(True)
    ax.legend()

    #rturn(fig)
