import matplotlib.pyplot as plt

def dendritic_stability_edges(G_out, V_planar, V_dend, fig_size):
    fig, ax = plt.subplots(figsize=fig_size)
    ax.loglog(G_out, V_planar, color="black", linestyle="-", linewidth=2)
    ax.loglog(G_out, V_dend,  color="black", linestyle="-", linewidth=2)
    ax.set_ylabel("Velocity (m/s)")
    ax.set_xlabel("Thermal Gradient G (K/m)")
    ax.grid(True, which="both", ls="--", alpha=0.4)
    fig.tight_layout()
    return fig, ax
