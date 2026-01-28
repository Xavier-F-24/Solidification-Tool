import matplotlib.pyplot as plt
import numpy as np

from io_utils.monotonic import monotonic_display_xy

def spacing_to_color(spacings):
    unique = sorted(set(spacings))

    cmap = plt.get_cmap("turbo")
    colors = cmap(np.linspace(0.1, 0.9, len(unique)))

    return {lam_um: color for lam_um, color in zip(unique, colors)}

def plot_V_R(ims_results, Wanted_G, fig_size):
    # --------------------------------------------------
    # Unpack inputs
    # --------------------------------------------------
    G = ims_results["G"]
    V_minus = ims_results["V-"]
    V_plus = ims_results["V+"]
    R_minus = ims_results["R-"]
    R_plus = ims_results["R+"]
    Total_undercooling = ims_results["Total_undercooling"]
    Solute_undercooling = ims_results["Solute_undercooling"]
    Curvature_undercooling = ims_results["Curvature_undercooling"]

    idx = np.argmin(np.abs(G - Wanted_G))

    # --------------------------------------------------
    # Plotting V and R curves
    # --------------------------------------------------
    
    fig_radius = plt.figure(figsize = fig_size)
    #for i in range(len(G)):
    plt.loglog(V_minus[idx][0], R_minus[idx], label="Negatives", color = "green", linestyle = "--", linewidth = 2)
    plt.loglog(V_plus[idx][0], R_plus[idx], label="Positives", color = "blue", linestyle = "-", linewidth = 2)
    plt.xlabel("Velocity (m/s)")
    plt.ylabel("Tip radius (m)")
    plt.title(f"Thermal Gradient {G[idx]:.1e}")
    plt.legend()
    plt.grid(True)

    # --------------------------------------------------
    # Plotting V versus solute undercooling
    # --------------------------------------------------
    fig_cool = plt.figure(figsize = fig_size)
    solute_colors = spacing_to_color(np.linspace(0,len(Solute_undercooling)-1, len(Solute_undercooling)))

    for j in range(len(Solute_undercooling)):
        color = solute_colors[j]
        V_solute_i, solute_i = monotonic_display_xy(V_plus[idx][0], Solute_undercooling[j])
        plt.semilogx(V_solute_i, solute_i, label=f"Solute {j+1}", color = color, linestyle = "-", linewidth = 2)
    V_total, total_cool = monotonic_display_xy(V_plus[idx][0], Total_undercooling[idx])
    plt.semilogx(V_total, total_cool, label="Total Undercooling", color = "black", linestyle = "-", linewidth = 2)
    V_curve, curvature_cool = monotonic_display_xy(V_plus[idx][0], Curvature_undercooling[idx])
    plt.semilogx(V_curve, curvature_cool, label="Curvature Undercooling", color = (0.45,0.25,0.0), linestyle = "-", linewidth = 2)
    plt.xlabel("Velocity (m/s)")
    plt.ylabel("Undercooling (K)")
    plt.title(f"Thermal Gradient {G[idx]:.1e}")
    plt.legend()
    plt.grid(True)

    # --------------------------------------------------
    # Unleash the images!!
    # --------------------------------------------------

    return(fig_radius, fig_cool)