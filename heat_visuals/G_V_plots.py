import matplotlib.pyplot as plt

def plot_G_V(G, V):
    plt.figure()
    plt.loglog(G, V, marker = 'o')
    plt.ylabel("Solidification Velocity (m/s)")
    plt.xlabel("Thermal Gradient (K/m)")
    plt.title("Steady-State Directional Solidification")
    plt.grid(True)
