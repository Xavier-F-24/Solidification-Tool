import matplotlib.pyplot as plt
import numpy as np

def plot_V_R(ims_results, Wanted_G):
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
    
    plt.figure()
    for i in range(len(G)):
        plt.loglog(V_minus[i][0], R_minus[i], label="Negatives")
        plt.loglog(V_plus[i][0], R_plus[i], label="Positives")
        plt.xlabel("Velocity (m/s)")
        plt.ylabel("Tip radius (m)")
        plt.title(f"Thermal Gradient {G[i]:.1e}")
        #plt.legend()
        plt.grid(True)

    # --------------------------------------------------
    # Plotting V versus solute undercooling
    # --------------------------------------------------
    plt.figure()
    for j in range(len(Solute_undercooling)):
        plt.semilogx(V_plus[idx][0], Solute_undercooling[j], label=f"Solute {j+1}")
    plt.semilogx(V_plus[idx][0], Total_undercooling[idx], label="Total Undercooling")
    plt.semilogx(V_plus[idx][0], Curvature_undercooling[idx], label="Curvature Undercooling")
    plt.xlabel("Velocity (m/s)")
    plt.ylabel("Undercooling (K)")
    plt.title(f"Thermal Gradient {G[idx]:.1e}")
    plt.legend()
    plt.grid(True)

    # --------------------------------------------------
    # Unleash the images!!
    # --------------------------------------------------

    #return( G, V_plus, R_plus )