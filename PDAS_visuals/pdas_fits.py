import matplotlib.pyplot as plt

import numpy as np

def plot_fits(ims_results, fit_ims_results, Wanted_G):

    G = ims_results["G"]
    V = ims_results["V+"]
    R = ims_results["R+"]
    Total_undercooling = ims_results["Total_undercooling"]

    alpha1, beta1, alpha2, beta2 = fit_ims_results

    idx = np.argmin(np.abs(G - Wanted_G))

    plt.figure()
    plt.loglog(V[idx][0], R[idx], label="True")
    plt.loglog(V[idx][0], alpha1 * V[idx][0]**beta1 , label="Fit")
    plt.xlabel("Velocity (m/s)")
    plt.ylabel("Tip radius (m)")
    plt.legend()

    plt.figure()
    plt.semilogx(V[idx][0], Total_undercooling[idx], label="True")
    plt.semilogx(V[idx][0], alpha2 * V[idx][0]**beta2 , label="Fit")
    plt.xlabel("Velocity (m/s)")
    plt.ylabel("Tip undercooling (K)")
    plt.legend()