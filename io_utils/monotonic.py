import numpy as np

def monotonic_display_xy(x, y):
    """
    Sort by x and enforce monotonic non-decreasing y for display.

    Parameters
    ----------
    x : array-like
        Independent variable (e.g. V)
    y : array-like
        Dependent variable (e.g. DeltaT)

    Returns
    -------
    x_sorted : ndarray
    y_mono   : ndarray
    """

    x = np.asarray(x)
    y = np.asarray(y)

    print(len(x))

    mask = np.isfinite(x)

    x = x[mask]
    y = y[mask]

    where_to_stop = np.argmax(x)
    
    x = x[:where_to_stop]
    y = y[:where_to_stop]


    return x, y
