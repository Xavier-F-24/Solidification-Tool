"""
Configuration and preset alloys for the Streamlit app.
"""

# Preset alloy compositions
PRESETS = {
    "Fe-Ni-Cr (Baseline)": {
        "name": "Fe-Ni-Cr (Baseline)",
        "description": "Iron-Nickel-Chromium stainless steel (MTGN 4XX class alloy)",
        "heat_transfer": {
            "k_l": 30.5,      # thermal conductivity of liquid [W/m-K]
            "rho_s": 7850,    # density of solid [kg/m^3]
            "c_p": 670,       # heat capacity of solid [J/kg-K]
            "L_f": 2.91e5,    # latent heat of fusion [J/kg]
            "T_f": 1728,      # fusion temperature [K]
            "T_o": 500,       # outside temperature [K]
        },
        "composition": {
            "C_0": [18.29, 11.55, 1.4],      # solute concentrations in liquid [wt%]
            "C_f": [24.55, 16.30, 3.33],     # solute concentrations in final solid [wt%]
            "k": [1.03, 0.74, 0.75],         # partition coefficients [-]
            "m": [1.92, -6.34, -4.14],       # liquidus slopes [K/wt%]
            "D": [8e-9, 8e-9, 8e-8],         # diffusivity [m^2/s]
            "Gamma": 2.56e-7,                # Gibbs-Thomson coefficient [-]
        },
        "model_params": {
            "NonEq_Freezing_range": 88,      # non-equilibrium freezing range [K]
            "N0": 1e12,                       # nucleant particle concentration [1/m^3]
            "DeltaTN": 2.5,                   # nucleation undercooling [K]
        },
    },
    "Al 6061": {
        "name": "Al 6061",
        "description": "Aluminum 6061 alloy (Al-Mg-Si system)",
        "heat_transfer": {
            "k_l": 70.0,      # higher thermal conductivity
            "rho_s": 2700,    # lower density
            "c_p": 900,       # higher heat capacity
            "L_f": 3.97e5,    # latent heat
            "T_f": 933,       # lower fusion temperature
            "T_o": 300,       # lower ambient
        },
        "composition": {
            "C_0": [1.0, 0.6],                # Al-Mg-Si
            "C_f": [1.5, 1.2],
            "k": [0.45, 0.73],
            "m": [-7.0, -4.5],
            "D": [3e-9, 3e-9],
            "Gamma": 1.5e-7,
        },
        "model_params": {
            "NonEq_Freezing_range": 125,
            "N0": 2e12,
            "DeltaTN": 1.8,
        },
    },
    "Ni-based Superalloy": {
        "name": "Ni-based Superalloy",
        "description": "Nickel-based superalloy (Ni-Co-Al system)",
        "heat_transfer": {
            "k_l": 25.0,      # lower than Fe
            "rho_s": 8800,    # higher density
            "c_p": 600,       # moderate heat capacity
            "L_f": 2.65e5,    # moderate latent heat
            "T_f": 1700,      # high fusion temperature
            "T_o": 600,       # higher ambient
        },
        "composition": {
            "C_0": [5.5, 12.0],               # Ni-Co-Al
            "C_f": [8.2, 18.5],
            "k": [0.81, 0.66],
            "m": [2.5, -3.2],
            "D": [5e-9, 5e-9],
            "Gamma": 2.0e-7,
        },
        "model_params": {
            "NonEq_Freezing_range": 95,
            "N0": 5e11,
            "DeltaTN": 3.0,
        },
    },
}

# Default visualization settings
DEFAULT_VIZ_SETTINGS = {
    "show_heat_transfer": True,
    "show_ims": True,
    "show_ims_fits": True,
    "show_pdas": True,
    "show_sdas": True,
    "show_cet": True,
}

# IMS analysis defaults
DEFAULT_IMS_SETTINGS = {
    "wanted_g": 1e5,  # K/m (for power law fitting)
    "g_range_min": -9,  # 10^-9 K/m
    "g_range_max": 9,   # 10^9 K/m
}

# Streamlit app settings
APP_TITLE = "Solidification Simulator"
APP_SUBTITLE = "Based on MTGN 4XX - Colorado School of Mines"
APP_DESCRIPTION = """
This tool simulates directional solidification microstructure evolution using coupled physics models:
- **Heat Transfer**: Thermal gradient vs. velocity relationships
- **IMS**: Ivantsov Multiple Solutes undercooling model
- **Stability**: Planar-dendritic transition boundaries
- **PDAS/SDAS**: Primary & secondary dendrite arm spacing
- **CET**: Columnar-to-equiaxed transition
"""

# Figure styling
FIG_SIZE_DEFAULT = (10, 7)
FIG_DPI = 150

# Caching settings
CACHE_TTL = 3600  # seconds (1 hour)

# Input ranges (for validation)
INPUT_RANGES = {
    "k_l": (1, 200),           # W/m-K
    "rho_s": (1000, 20000),    # kg/m^3
    "c_p": (100, 3000),        # J/kg-K
    "L_f": (1e5, 1e6),         # J/kg
    "T_f": (500, 3000),        # K
    "T_o": (100, 1000),        # K
    "C_0": (0, 100),           # wt%
    "C_f": (0, 100),           # wt%
    "k": (0.1, 3.0),           # partition coeff
    "m": (-20, 20),            # K/wt%
    "D": (1e-11, 1e-6),        # m^2/s
    "Gamma": (1e-10, 1e-4),    # Gibbs-Thomson
    "NonEq_Freezing_range": (1, 500),   # K
    "N0": (1e10, 1e15),        # nucleants/m^3
    "DeltaTN": (0.1, 20),      # K
}
