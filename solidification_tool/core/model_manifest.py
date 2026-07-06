"""
Scientific provenance and validity notes for the engine submodels.

This module is intentionally compact and machine-readable so saved runs can
record the scientific contract used to produce their numerical results.
"""

MODEL_MANIFEST_VERSION = "2026.07-science-audit-1"


MODEL_MANIFEST = {
    "heat_transfer": {
        "intent": "Steady-state directional solidification thermal gradient as a function of interface velocity.",
        "equations": [
            "G = V * (rho_s * c_p * (T_f - T_o) / k_l - L_f * rho_s / k_l)",
        ],
        "inputs": {
            "V": "solidification velocity [m/s]",
            "k_l": "liquid thermal conductivity [W/m-K]",
            "rho_s": "solid density [kg/m^3]",
            "c_p": "solid heat capacity [J/kg-K]",
            "L_f": "latent heat of fusion [J/kg]",
            "T_f": "fusion/furnace temperature [K]",
            "T_o": "outside temperature [K]",
        },
        "outputs": {"G": "thermal gradient [K/m]"},
        "validity": "Requires positive thermal properties and T_f > T_o; assumes one-dimensional steady heat flow.",
        "provenance": "Directional-solidification energy balance used by the original project model.",
        "limitations": "Does not solve transient heat conduction or latent-heat redistribution.",
    },
    "ivantsov": {
        "intent": "Evaluate the Ivantsov function for solutal diffusion around a dendrite tip.",
        "equations": [
            "Iv(Pe) = Pe * exp(Pe) * E1(Pe), approximated by low/high-Pe rational fits.",
        ],
        "inputs": {"Pe": "Peclet number [-], positive"},
        "outputs": {"Iv": "dimensionless concentration response [-]"},
        "validity": "Requires Pe > 0; approximation is split at Pe = 1.",
        "provenance": "Ivantsov dendrite-tip diffusion solution with project polynomial/rational coefficients.",
        "limitations": "Approximation coefficients need external literature citation before precision claims are tightened.",
    },
    "ims": {
        "intent": "Multi-solute Ivantsov undercooling plus marginal-stability radius/velocity branches.",
        "equations": [
            "eta_i = 1 - 2*k_i / (2*k_i - 1 + sqrt(1 + (2*pi/Pe_i)^2))",
            "C_l_i* = C_0_i / (1 - (1 - k_i) * Iv(Pe_i))",
            "A/R^2 + B/R + G = 0, A = 4*pi^2*Gamma, B = 2*sum(m_i*Pe_i*(1-k_i)*C_l_i*eta_i)",
            "V_i = 2*D_ref*Pe_i/R",
        ],
        "inputs": {
            "C_0": "initial solute concentrations [wt%]",
            "k": "partition coefficients [-]",
            "m": "liquidus slopes [K/wt%]",
            "D": "solute diffusivities [m^2/s]",
            "Gamma": "Gibbs-Thomson coefficient [K-m]",
            "G": "thermal gradient [K/m]",
            "Pe": "solute-scaled Peclet number [-]",
        },
        "outputs": {
            "R_plus": "positive marginal-stability radius branch [m]",
            "V_plus": "positive velocity branch [m/s]",
            "Total_undercooling": "solute plus curvature undercooling [K]",
            "Stable": "finite positive discriminant mask [-]",
        },
        "validity": "Requires positive diffusivities/Gamma and real marginal-stability discriminant.",
        "provenance": "Project multi-solute Ivantsov and marginal-stability formulation.",
        "limitations": "Adaptive Pe bounds are numerical windows from the discriminant, not an independent physical model.",
    },
    "stability_boundaries": {
        "intent": "Extract planar/cellular and cellular/dendritic velocity boundaries from IMS branches.",
        "equations": [
            "V_planar(G) = min(V_plus where V_plus and R_plus are finite positive)",
            "V_dendritic(G) = V_plus at min(R_plus) over the finite positive branch",
        ],
        "inputs": {"R_plus": "IMS positive radius branch [m]", "V_plus": "IMS positive velocity branch [m/s]"},
        "outputs": {"G_out": "valid gradients [K/m]", "V_planar": "planar boundary velocity [m/s]", "V_dend": "dendritic boundary velocity [m/s]"},
        "validity": "Requires at least one finite positive IMS branch per retained G row.",
        "provenance": "Operational extraction rule from project IMS stability plots.",
        "limitations": "Boundary definitions should be checked against the target reference paper before high-confidence prediction use.",
    },
    "pdas": {
        "intent": "Primary dendrite arm spacing curves for prescribed lambda_1 values.",
        "equations": ["G = 3*R(V)*(DeltaT0 - DeltaT_IMS(V))/lambda_1^2"],
        "inputs": {"lambda_1": "primary arm spacing [m]", "R": "IMS fitted tip radius [m]", "DeltaT0": "non-equilibrium freezing range [K]"},
        "outputs": {"G(V)": "thermal gradient curve [K/m]"},
        "validity": "Requires V_min < V_max, positive fit coefficient alpha1, and positive effective freezing range.",
        "provenance": "Project PDAS relation coupled to IMS power-law fits.",
        "limitations": "Uses fitted IMS power laws; uncertainty follows fit range and fit quality.",
    },
    "sdas": {
        "intent": "Secondary dendrite arm spacing curves from coarsening coefficient M.",
        "equations": ["lambda_2 = 5.5*(M*t_f)^(1/3)", "G = M*DeltaT0 / (V*(lambda_2^3/5.5^3))"],
        "inputs": {"lambda_2": "secondary arm spacing [m]", "M": "coarsening coefficient [m^3/s]", "DeltaT0": "freezing range [K]"},
        "outputs": {"G(V)": "thermal gradient curve [K/m]"},
        "validity": "Requires positive logarithm argument and positive finite coarsening coefficient.",
        "provenance": "Project SDAS coarsening relation.",
        "limitations": "Sign conventions depend on liquidus slope and composition definitions; benchmark against reference alloys before tightening.",
    },
    "cet": {
        "intent": "Columnar-to-equiaxed transition curves for prescribed equiaxed fraction phi.",
        "equations": [
            "G_CET(V) = A*DeltaT_IMS(V)*(1 - DeltaT_N^(n+1)/DeltaT_IMS(V)^(n+1))",
            "A = (1/(n+1))*(-4*pi*N0/(3*ln(1-phi)))^(1/3)",
        ],
        "inputs": {"N0": "nucleant density [1/m^3]", "DeltaT_N": "nucleation undercooling [K]", "phi": "equiaxed fraction [-]"},
        "outputs": {"G(V)": "CET thermal gradient curve [K/m]"},
        "validity": "Requires 0 < phi < 1 and a bracketed transition velocity root.",
        "provenance": "Project CET relation coupled to IMS undercooling fit.",
        "limitations": "Uses a scalar bracket solve and fitted undercooling law; no stochastic nucleation distribution is modeled.",
    },
}


def model_manifest_summary():
    """Return minimal run-metadata fields for the active scientific contract."""
    return {
        "version": MODEL_MANIFEST_VERSION,
        "models": tuple(MODEL_MANIFEST.keys()),
    }
