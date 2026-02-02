import numpy as np

def monotonic_display_xy(x, y):
    """
    fixing the ims back-hooks by removing the entries after the maximum velocity
    """

    x = np.asarray(x)
    y = np.asarray(y)

    mask = np.isfinite(x)

    x = x[mask]
    y = y[mask]

    where_to_stop = np.argmax(x)
    
    x = x[:where_to_stop]
    y = y[:where_to_stop]


    return x, y
