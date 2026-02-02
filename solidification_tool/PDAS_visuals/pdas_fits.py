import matplotlib.pyplot as plt

import numpy as np

from solidification_tool.io_utils.monotonic import monotonic_display_xy

def plot_fits(ims_results, fit_ims_results, Wanted_G, fig_size):

    G = ims_results["G"]
    V = ims_results["V+"]
    R = ims_results["R+"]
    Total_undercooling = ims_results["Total_undercooling"]

    alpha1 = fit_ims_results["alpha1"]
    beta1 = fit_ims_results["beta1"]
    alpha2 = fit_ims_results["alpha2"]
    beta2 = fit_ims_results["beta2"]
    R2_radius = fit_ims_results["R2_radius"]
    R2_undercooling = fit_ims_results["R2_undercooling"]

    idx = np.argmin(np.abs(G - Wanted_G))

    fig_fit_radius, ax1 = plt.subplots(figsize = fig_size)
    ax1.loglog(V[idx][0], R[idx], label = "Calculated", color = "blue", linestyle = "-", linewidth = 2)
    ax1.loglog(V[idx][0], alpha1 * V[idx][0]**beta1 , label = f"Fit alpha: {alpha1:.3e}, beta: {beta1:.3e}, R-squared: {R2_radius:.3f}", color = "red", linestyle = "-", linewidth = 2)
    ax1.set_xlabel("Velocity (m/s)")
    ax1.set_ylabel("Tip radius (m)")
    ax1.set_title(f"Velocity Power Law fit for Radius")
    ax1.grid(True)
    ax1.legend()

    fig_fit_cool, ax2 = plt.subplots(figsize = fig_size)
    V_cool, Cool = monotonic_display_xy(V[idx][0], Total_undercooling[idx])
    ax2.semilogx(V_cool, Cool, label = "Calculated", color = "black", linestyle = "-", linewidth = 2)
    ax2.semilogx(V[idx][0], alpha2 * V[idx][0]**beta2 , label = f"Fit alpha: {alpha2:.3e}, beta: {beta2:.3e}, R-squared: {R2_undercooling:.3f}", color = "red", linestyle = "-", linewidth = 2)
    ax2.set_xlabel("Velocity (m/s)")
    ax2.set_ylabel("Tip undercooling (K)")
    ax2.set_title(f"Velocity Power Law fit for Undercooling")
    ax2.grid(True)
    ax2.legend()

    return(fig_fit_radius, fig_fit_cool)