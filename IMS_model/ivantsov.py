"""
Ivantsov function evaluation
"""

import numpy as np

def Ivantsov(Pe):
    Pe = np.asarray(Pe, dtype=float)

    # Coefficients from literature
    a = np.array([
        -0.57721566,   # a0
         0.99999193,   # a1
        -0.24991055,   # a2
         0.05519968,   # a3
        -0.00976004,   # a4
         0.00107857    # a5
    ])

    b = np.array([8.5733287401, 18.059016973, 8.6347608925, 0.2677737343])
    c = np.array([9.5733223454, 25.6329561486, 21.0996530827, 3.9584969228])

    out = np.empty_like(Pe)

    mask = Pe <= 1.0

    # ---- Pe <= 1 branch ----
    poly = (
        a[0]
        + a[1]*Pe[mask]
        + a[2]*Pe[mask]**2
        + a[3]*Pe[mask]**3
        + a[4]*Pe[mask]**4
        + a[5]*Pe[mask]**5
    )

    out[mask] = (
        Pe[mask]
        * np.exp(Pe[mask])
        * (poly - np.log(Pe[mask]))
    )

    # ---- Pe > 1 branch ----
    Pe_hi = Pe[~mask]

    num = (
        Pe_hi**4
        + b[0]*Pe_hi**3
        + b[1]*Pe_hi**2
        + b[2]*Pe_hi
        + b[3]
    )

    den = (
        Pe_hi**4
        + c[0]*Pe_hi**3
        + c[1]*Pe_hi**2
        + c[2]*Pe_hi
        + c[3]
    )

    out[~mask] = num / den

    return out
