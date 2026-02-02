def normalize_spacing_um(lam_m, ndigits=6):
    """
    Normalize spacing for dictionary keys and plotting.
    Converts meters → microns → rounded Python float.
    """
    return round(float(lam_m) * 1e6, ndigits)
