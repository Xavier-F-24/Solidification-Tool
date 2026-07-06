"""Deprecated scratch module retained only for historical reference.

The active scientific engine lives under ``solidification_tool.core`` and the
``*_model`` packages. This file contains old exploratory code and must not be
imported by application or engine paths.
"""

"""
def solve_ims1(inputs):
    
    Multi-solute Ivantsov + marginal stability solver.

    Solves for:
        - Tip radius (R+/-)
        - Tip velocity (V+/-)
        - Solutal, curvature, and total undercooling
        - Planar stability parameter

    Written 1.12.2026 XF
    

    # --------------------------------------------------
    # Unpack inputs
    # --------------------------------------------------
    C_0   = np.atleast_1d(inputs.C_0).reshape(-1, 1)   # (n_solute, 1)
    k     = np.atleast_1d(inputs.k).reshape(-1, 1)
    m     = np.atleast_1d(inputs.m).reshape(-1, 1)
    D     = np.atleast_1d(inputs.D).reshape(-1, 1)

    Gamma = inputs.Gamma        # scalar
    G     = 1e5                 # imposed thermal gradient

    n_solute = C_0.shape[0]

    # --------------------------------------------------
    # Peclet construction (scaled by diffusivity)
    # --------------------------------------------------
    N_Pe = 100
    P = np.logspace(-6, 6, N_Pe)                     # (n_Pe,)

    D_ref = D[0, 0]
    scale = D_ref / D                               # (n_solute, 1)

    Pe = scale * P[None, :]                         # (n_solute, n_Pe)

    # --------------------------------------------------
    # Ivantsov & solute response
    # --------------------------------------------------
    Iv = Ivantsov(Pe)

    Eta = 1 - (2 * k) / (2 * k - 1 + np.sqrt(1 + (2 * np.pi / Pe)**2))

    C_l_star = C_0 / (1 - (1 - k) * Iv)

    # Solutal contribution inside stability condition
    S = m * Pe * (1 - k) * C_l_star * Eta

    # --------------------------------------------------
    # Marginal stability quadratic: A/R² + B/R + C = 0
    # --------------------------------------------------
    A = 4 * np.pi**2 * Gamma
    B = 2 * np.sum(S, axis=0)      # sum over solutes → (n_Pe,)
    Cq = G

    disc = B**2 - 4 * A * Cq
    valid = disc > 0

    Quad_plus  = np.full_like(B, np.nan)
    Quad_minus = np.full_like(B, np.nan)

    Quad_plus[valid]  = (-B[valid] + np.sqrt(disc[valid])) / (2 * A)
    Quad_minus[valid] = (-B[valid] - np.sqrt(disc[valid])) / (2 * A)

    # --------------------------------------------------
    # Radius is the inverse of the quadratic solution
    # --------------------------------------------------
    R_plus  = 1 / Quad_plus
    R_minus = 1 / Quad_minus

    # --------------------------------------------------
    # Velocity from Peclet definition
    # --------------------------------------------------
    V_plus  = 2 * D_ref * Pe / R_plus
    V_minus = 2 * D_ref * Pe / R_minus

    # --------------------------------------------------
    # Undercooling sources
    # --------------------------------------------------
    Individual_Solutes = (m * (C_0 - C_l_star))      # (n_solute, n_Pe)

    Solute_undercool = np.sum(Individual_Solutes, axis=0)

    Curvature_undercool = 2 * Gamma / np.minimum(R_plus, R_minus)

    Total_undercool = Solute_undercool + Curvature_undercool

    # --------------------------------------------------
    # Output
    # --------------------------------------------------
    return {
        "Pe": Pe,
        "R+": R_plus,
        "R-": R_minus,
        "V+": V_plus,
        "V-": V_minus,
        "Total_undercooling": Total_undercool,
        "Solute_undercooling": Individual_Solutes,
        "Curvature_undercooling": Curvature_undercool,
        "Stable": valid
    }

Set G solver for IMS: 

def solve_ims(inputs):
    #
    Multi-solute Ivantsov + marginal stability solver.

    Solves for:
        - Tip radius (R+/-)
        - Tip velocity (V+/-)
        - Solutal, curvature, and total undercooling
        - Planar stability parameter

    Written 1.12.2026 XF
    #

    # --------------------------------------------------
    # Unpack inputs
    # --------------------------------------------------
    C_0   = np.atleast_1d(inputs.C_0).reshape(-1, 1)   # (n_solute, 1)
    k     = np.atleast_1d(inputs.k).reshape(-1, 1)
    m     = np.atleast_1d(inputs.m).reshape(-1, 1)
    D     = np.atleast_1d(inputs.D).reshape(-1, 1)

    Gamma = inputs.Gamma        # scalar
    G     = 1e5                 # imposed thermal gradient

    n_solute = C_0.shape[0]

    # --------------------------------------------------
    # Peclet construction (scaled by diffusivity)
    # --------------------------------------------------
    N_Pe = 100
    P = np.logspace(-6, 6, N_Pe)                     # (n_Pe,)

    D_ref = D[0, 0]
    scale = D_ref / D                               # (n_solute, 1)

    Pe = scale * P[None, :]                         # (n_solute, n_Pe)

    # --------------------------------------------------
    # Ivantsov & solute response
    # --------------------------------------------------
    Iv = Ivantsov(Pe)

    Eta = 1 - (2 * k) / (2 * k - 1 + np.sqrt(1 + (2 * np.pi / Pe)**2))

    C_l_star = C_0 / (1 - (1 - k) * Iv)

    # Solutal contribution inside stability condition
    S = m * Pe * (1 - k) * C_l_star * Eta

    # --------------------------------------------------
    # Marginal stability quadratic: A/R² + B/R + C = 0
    # --------------------------------------------------
    A = 4 * np.pi**2 * Gamma
    B = 2 * np.sum(S, axis=0)      # sum over solutes → (n_Pe,)
    Cq = G

    disc = B**2 - 4 * A * Cq
    valid = disc > 0

    Quad_plus  = np.full_like(B, np.nan)
    Quad_minus = np.full_like(B, np.nan)

    Quad_plus[valid]  = (-B[valid] + np.sqrt(disc[valid])) / (2 * A)
    Quad_minus[valid] = (-B[valid] - np.sqrt(disc[valid])) / (2 * A)

    # --------------------------------------------------
    # Radius is the inverse of the quadratic solution
    # --------------------------------------------------
    R_plus  = 1 / Quad_plus
    R_minus = 1 / Quad_minus

    # --------------------------------------------------
    # Velocity from Peclet definition
    # --------------------------------------------------
    V_plus  = 2 * D_ref * Pe / R_plus
    V_minus = 2 * D_ref * Pe / R_minus

    # --------------------------------------------------
    # Undercooling sources
    # --------------------------------------------------
    Individual_Solutes = (m * (C_0 - C_l_star))      # (n_solute, n_Pe)

    Solute_undercool = np.sum(Individual_Solutes, axis=0)

    Curvature_undercool = 2 * Gamma / np.minimum(R_plus, R_minus)

    Total_undercool = Solute_undercool + Curvature_undercool

    # --------------------------------------------------
    # Output
    # --------------------------------------------------
    return {
        "Pe": Pe,
        "R+": R_plus,
        "R-": R_minus,
        "V+": V_plus,
        "V-": V_minus,
        "Total_undercooling": Total_undercool,
        "Solute_undercooling": Individual_Solutes,
        "Curvature_undercooling": Curvature_undercool,
        "Stable": valid
    }


# --------------------------------------------------
# Space for unimportant working, but cool historical code
# --------------------------------------------------


Xaviers Original Code for def solve_ims()! - 1.10.2026


def solve_ims1(inputs):
    
    Solves for:
        - Tip undercooling for velocity
        - Tip Radius for velocity
        - Iteratively solves with different G to find planar, cellular, and dendritic stability regions
    

    C_0 = inputs.C_0      # shape (n_solutes,)
    k = inputs.k
    m = inputs.m
    D = inputs.D
    Gamma = inputs.Gamma   # scalar


    C_0, k, m, D = map(
        lambda x: np.atleast_1d(x)[None, :],
        (C_0, k, m, D) )

    print('C_0')
    print(C_0)
    print(np.shape(C_0))
    print('k')
    print(k)
    print(np.shape(k))
    print('m')
    print(m)
    print(np.shape(m))
    print('D')
    print(D)
    print(np.shape(D))

    #C_0 = inputs.C_0
    #k = inputs.k
    #m = inputs.m
    #D = inputs.D

    Gamma = inputs.Gamma

    G = 1e5  # will change later

    
    Peclett conditioning
    

    # Péclet definition: Pe = V R / (2 D)
    N_Pe = 100

    P = np.logspace(-6,6,N_Pe)

    D = np.asarray(D)             # shape (n_solute,)
    D_ref = D[0][0]               # or any reference you like
    # need to change this long term to handle pure metals too - or just one solute!
    scale = D_ref / D             # shape (n_solute,)

    scale = np.asarray(scale).reshape(-1) # to fix it up

    

    print(np.shape(D))
    print(np.shape(scale))
    print(np.shape(scale[:, None]))
    print(np.shape(P[None, :]))

    Pe = scale[:, None] * P[None, :]

    print('Pe')
    print(Pe)


    Iv = Ivantsov(Pe)
    print('Iv')
    print(Iv)

    k1 = np.asarray(k).reshape(-1, 1)
    Eta = 1 - (2*k1) / (2*k1 - 1 + np.sqrt(1 + (2*np.pi / Pe)**2))
    print('Eta')
    print(Eta)

    C_01 = np.asarray(C_0).reshape(-1, 1)
    C_l_star = C_01 / ( 1 - ( ( 1 - k1 ) * Iv ) )
    print('Cl*')
    print(C_l_star)

    #C_l_star.shape == (np.length(Pe), np.length(C_0))

    m1 = np.asarray(m).reshape(-1, 1)
    Sums = m1 * Pe * ( 1 - k1 ) * C_l_star * Eta
    print('Sums')
    print(Sums)

    
    Here we go back to a consolidated set
    

    
    A = 4 * np.pi**2 * Gamma          # scalar
    print('A')
    print(A)

    B = 2 * np.sum(Sums, axis=0)      # (nPe,)
    print('B')
    print(B)

    C = G                             # scalar
    print('C')
    print(C)



    
    Now we do the quadratic formula on our A, B, and C terms
    

    disc = B**2 - 4*A*C

    valid = disc >= 1e-10

    Quad_plus  = np.full_like(B, np.nan)
    Quad_minus = np.full_like(B, np.nan)

    Quad_plus[valid] = (-B[valid] + np.sqrt(disc[valid])) / (2*A)
    Quad_minus[valid] = (-B[valid] - np.sqrt(disc[valid])) / (2*A)

    R_plus  = 1 / Quad_plus
    R_minus = 1 / Quad_minus

    #R = np.minimum(R_plus, R_minus)
    #R[R <= 0] = np.nan
    
    #print('R')
    #print(R)

    D1 = np.asarray(D[0][0])              # (n_solute, 1)
    #R = np.asarray(R)                     # (1, n_pe)
    Pe = np.asarray(Pe)                   # (n_solute, n_pe)   

    V_minus = 2 * D1 * Pe / R_minus
    V_plus = 2 * D1 * Pe / R_plus

    print('V-')
    print(V_minus)
    print('V+')
    print(V_plus)

    #print(np.sum(V[0][0]-V[0][1]))
    #print(V[1]-V[2])
    #print(V[2]-V[0])

    
    Back to individual solutes
    
    print(np.shape(m))
    print(np.shape((C_0 ) ))

    
    reshape the C_0 to work!
    
    multer = np.ones(shape= [N_Pe,1] )
    C_01 = C_0 * multer


    m2 = m * multer

    print(np.shape(m2))
    print(np.shape(C_01 - C_l_star.T))


    #print(np.shape((C_01 ) ))
    #print(np.shape(( C_l_star.T) ))
    #print(np.shape((C_01 - C_l_star.T) ))
    #print((C_01 - C_l_star.T) * m)
    Individual_Solutes = ((C_01 - C_l_star.T) * m).T
    print("indis")
    print(Individual_Solutes)

    Solute_undercool = np.sum((C_01 - C_l_star.T) * m, axis=1)
    print('Solutes')
    print(Solute_undercool)
    print(np.shape(Solute_undercool))

    
    Now to overall again
    

    Curvature_undercool = 2 * Gamma / np.minimum(R_minus, R_plus)
    print('Curvature')
    print(Curvature_undercool)

    Total_undercool = Solute_undercool + Curvature_undercool
    print('Total cool')
    print(Total_undercool)

    print('stable')
    print(valid)

    S_planar = np.sum(m * C_0 * (1 - k) / (k * D))


    #assert V.ndim == 1
    #assert R.ndim == 1
    #assert Pe.ndim == 2 or Pe.ndim == 1

    return {
        "Pe": Pe.flatten(),
        "R+": R_plus,
        "R-": R_minus,
        "V+": V_plus,
        "V-": V_minus,
        "DeltaT": Total_undercool,
        "stable": valid,
        "A" : A,
        "B" : B,
        "S" : S_planar,
        "Solutes": Individual_Solutes,
        "Curvature": Curvature_undercool
    }

    """
