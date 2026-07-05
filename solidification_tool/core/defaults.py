from solidification_tool.core.inputs import SolidificationInputs


def get_inputs() -> SolidificationInputs:
    return SolidificationInputs(
        k_l=30.5,
        rho_s=7850,
        c_p=670,
        L_f=2.91e5,
        T_f=1728,
        T_o=500,
        C_0=[18.29, 11.55, 1.4],
        C_f=[24.55, 16.30, 3.33],
        k=[1.03, 0.74, 0.75],
        m=[1.92, -6.34, -4.14],
        D=[8e-9, 8e-9, 8e-8],
        Gamma=2.56e-7,
        NonEq_Freezing_range=88,
        N0=1e12,
        DeltaTN=2.5,
    )

