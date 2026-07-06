import numpy as np

def monotonic_display_xy(x, y):
    """
    fixing the ims back-hooks by removing the entries after the maximum velocity
    """

    x = np.asarray(x)
    y = np.asarray(y)

    mask = np.isfinite(x) & np.isfinite(y)

    x = x[mask]
    y = y[mask]

    where_to_stop = np.argmax(x)
    
    x = x[:where_to_stop + 1]
    y = y[:where_to_stop + 1]


    return x, y
