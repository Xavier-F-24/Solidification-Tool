import matplotlib.pyplot as plt

def dendritic_stability_edges(G_out, V_planar, V_dend):
    plt.figure()#figsize=(6,5))

    plt.loglog(G_out, V_planar) #, label="Planar -> Cellular")
    plt.loglog(G_out, V_dend) #, label="Cellular -> Dendritic")

    plt.ylabel("Velocity (m/s)")
    plt.xlabel("Thermal Gradient G (K/m)")
    #plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.4)