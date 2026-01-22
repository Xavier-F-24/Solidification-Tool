from dataclasses import dataclass, asdict


@dataclass
class SolidificationInputs:
    # --------------------------------------------------
    # Heat transfer model inputs
    # --------------------------------------------------
    k_l: float       # thermal conductivity of liquid [W/m-K]
    rho_s: float     # density of solid [kg/m^3]
    c_p: float       # heat capacity of solid [J/kg-K]
    L_f: float       # latent heat of fusion [J/kg]
    T_f: float       # fusion or furnace temperature [K]
    T_o: float       # outside temperature [K]

    # --------------------------------------------------
    # IMS model inputs
    # --------------------------------------------------
    C_0 : list       # solute concentrations in alloy [wt%]
    C_f : list       # solute concentrations in alloy end solid [wt%]
    k : list         # partition coefficient (local) [-]
    m : list         # liquidus slopes (local) [K / wt%]
    D : list         # diffusivity [something, Xavier forgets]
    Gamma : float    # given value [-]

    # --------------------------------------------------
    # PDAS inputs
    # --------------------------------------------------
    NonEq_Freezing_range : float # given value of to eutectic (usually) [K]
    
    # --------------------------------------------------
    # CET inputs
    # --------------------------------------------------
    N0 : float # innoculant particles concentration [1/m^3]
    DeltaTN : float # the temperature decrease from a particle (?) [K]

    def to_dict(self):
        return asdict(self)
    
