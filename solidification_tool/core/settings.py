from dataclasses import dataclass


@dataclass(frozen=True)
class EngineSettings:
    heat_v_min_exp: float = -6
    heat_v_max_exp: float = 6
    heat_v_count: int = 100
    ims_g_min_exp: float = -6
    ims_g_max_exp: float = 9
    ims_g_count: int = 100
    ims_pe_min_exp: float = -9
    ims_pe_max_exp: float = 9
    ims_pe_count: int = 3000
    ims_sampling_mode: str = "adaptive"
    spacing_min_exp: float = -6
    spacing_max_exp: float = 6
    spacing_count: int = 13
    spacing_v_count: int = 100
    cet_v_count: int = 100
    cet_phi_values: tuple[float, ...] = (0.01, 0.5)

    def __post_init__(self):
        if self.ims_sampling_mode == "legacy":
            object.__setattr__(self, "ims_sampling_mode", "sweep")
