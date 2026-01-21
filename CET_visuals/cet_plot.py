import matplotlib.pyplot as plt

import numpy as np

def plot_cet(cet_results):
    """
    Plot CET G-V curves
    """

    for phi, data in cet_results.items():
        G = data["G"]
        V = data["V"]

        if np.any(np.isfinite(V)):
            label = f"Phi = {phi}"
        else:
            label = ""

        plt.loglog(
            G,
            V,
            label = label
        )

    plt.xlabel("Thermal Gradient G (K/m)")
    plt.ylabel("Velocity V (m/s)")
    plt.title("CET Map")

    plt.grid(True, which="both", ls="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()

