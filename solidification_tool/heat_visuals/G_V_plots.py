import matplotlib.pyplot as plt

def plot_G_V(G, V, fig_size):
    fig, ax = plt.subplots(figsize = fig_size)
    ax.loglog(G, V, marker='o', linestyle='-', linewidth=2)
    ax.set_ylabel("Solidification Velocity (m/s)")
    ax.set_xlabel("Thermal Gradient (K/m)")
    ax.set_title("Steady-State Directional Solidification")
    ax.grid(True, which="both")
    fig.tight_layout()
    return fig
