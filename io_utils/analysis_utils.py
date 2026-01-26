import numpy as np

def r_squared(y, y_hat):
    ss_res = np.sum((y - y_hat)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    return 1.0 - ss_res / ss_tot
