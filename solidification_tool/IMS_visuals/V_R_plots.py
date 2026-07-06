import matplotlib.pyplot as plt
import numpy as np

from solidification_tool.io_utils.monotonic import monotonic_display_xy


def spacing_to_color(spacings):
    unique = sorted(set(spacings))

    cmap = plt.get_cmap("turbo")
    colors = cmap(np.linspace(0.1, 0.9, len(unique)))

    return {lam_um: color for lam_um, color in zip(unique, colors)}

def plot_V_R(ims_results, Wanted_G, fig_size, plot_range = False, G_range = (1e-9, 1e9)):
    # --------------------------------------------------
    # Unpack inputs
    # --------------------------------------------------
    G = ims_results.G
    V_minus = ims_results.V_minus
    V_plus = ims_results.V_plus
    R_minus = ims_results.R_minus
    R_plus = ims_results.R_plus
    Total_undercooling = ims_results.Total_undercooling
    Curvature_undercooling = ims_results.Curvature_undercooling

    idx = np.argmin(np.abs(G - Wanted_G))

    # --------------------------------------------------
    # Plotting V and R curves
    # --------------------------------------------------
    
    fig_radius, ax1 = plt.subplots(figsize = fig_size)

    if (plot_range == True) :
        
        idx_low = np.argmin(np.abs(G - G_range[0]))
        idx_high = np.argmin(np.abs(G - G_range[1]))

        G_mask = G[idx_low : idx_high]

        for ix in range(len(G_mask)):

        #ix = 0
            ax1.loglog(V_minus[ix + idx_low][0], R_minus[ix + idx_low], label="Negatives", color = "green", linestyle = "--", linewidth = 2)
            ax1.loglog(V_plus[ix + idx_low][0], R_plus[ix + idx_low], label="Positives", color = "blue", linestyle = "-", linewidth = 2)
            ax1.set_xlabel("Velocity (m/s)")
            ax1.set_ylabel("Tip radius (m)")
            ax1.set_title(f"Thermal Gradient {G[ix + idx_low]:.1e}")
            #fig_radius.legend()
            ax1.grid(True)
    else:
        ax1.loglog(V_minus[idx][0], R_minus[idx], label="Negatives", color = "green", linestyle = "--", linewidth = 2)
        ax1.loglog(V_plus[idx][0], R_plus[idx], label="Positives", color = "blue", linestyle = "-", linewidth = 2)
        ax1.set_xlabel("Velocity (m/s)")
        ax1.set_ylabel("Tip radius (m)")
        ax1.set_title(f"Thermal Gradient {G[idx]:.1e}")
        ax1.legend()
        ax1.grid(True)

    # --------------------------------------------------
    # Plotting V versus solute undercooling
    # --------------------------------------------------
    fig_cool, ax2 = plt.subplots(figsize = fig_size)
    solute_undercooling_at_g = ims_results.solute_undercooling_at_g(idx)
    solute_colors = spacing_to_color(np.linspace(0,len(solute_undercooling_at_g)-1, len(solute_undercooling_at_g)))

    for j in range(len(solute_undercooling_at_g)):
        color = solute_colors[j]
        V_solute_i, solute_i = monotonic_display_xy(V_plus[idx][0], solute_undercooling_at_g[j])
        ax2.semilogx(V_solute_i, solute_i, label=f"Solute {j+1}", color = color, linestyle = "-", linewidth = 2)
    V_total, total_cool = monotonic_display_xy(V_plus[idx][0], Total_undercooling[idx])
    ax2.semilogx(V_total, total_cool, label="Total Undercooling", color = "black", linestyle = "-", linewidth = 2)
    V_curve, curvature_cool = monotonic_display_xy(V_plus[idx][0], Curvature_undercooling[idx])
    ax2.semilogx(V_curve, curvature_cool, label="Curvature Undercooling", color = (0.45,0.25,0.0), linestyle = "-", linewidth = 2)
    ax2.set_xlabel("Velocity (m/s)")
    ax2.set_ylabel("Undercooling (K)")
    ax2.set_title(f"Thermal Gradient {G[idx]:.1e}")
    ax2.legend()
    ax2.grid(True)

    # --------------------------------------------------
    # Unleash the images!!
    # --------------------------------------------------

    return (fig_radius, fig_cool)
