import matplotlib.pyplot as plt

def dendritic_stability_edges(G_out, V_planar, V_dend, fig_size):
    
    fig = plt.figure(figsize = fig_size)

    plt.loglog(G_out, V_planar, color = "black", linestyle = "-", linewidth = 2) #, label="Planar -> Cellular")
    plt.loglog(G_out, V_dend, color = "black", linestyle = "-", linewidth = 2) #, label="Cellular -> Dendritic")

    plt.ylabel("Velocity (m/s)")
    plt.xlabel("Thermal Gradient G (K/m)")
    #plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.4)

    return(fig)