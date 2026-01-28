import matplotlib.pyplot as plt

def plot_G_V(G, V, fig_size):
    fig = plt.figure(figsize = fig_size)
    plt.loglog(G, V, marker = 'o', color = "maroon", linestyle = "-", linewidth = 2)
    plt.ylabel("Solidification Velocity (m/s)")
    plt.xlabel("Thermal Gradient (K/m)")
    plt.title("Steady-State Directional Solidification")
    plt.grid(True)

    return(fig)
