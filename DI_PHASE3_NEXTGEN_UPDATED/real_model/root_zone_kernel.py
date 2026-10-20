"""Verbatim AquaCrop 3.1.0 root-zone equations, compiled without fastmath.
Only round(np.float64,2) is expressed as np.round(...,2)."""
import numpy as np
from numba import njit

@njit(cache=True,fastmath=False)
def root_zone_water(prof, InitCond_Zroot, InitCond_th, Soil_zTop, Crop_Zmin, Crop_Aer):
    """
    Function to calculate actual and total available water in the rootzone at current time step


    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=14" target="_blank">Reference Manual: root-zone water calculations</a> (pg. 5-8)


    Arguments:

        prof (SoilProfile): jit class Object containing soil paramaters

        InitCond_Zroot (float): Initial rooting depth

        InitCond_th (np.array): Initial water content

        Soil_zTop (float): Top soil depth

        Crop_Zmin (float): crop minimum rooting depth

        Crop_Aer (int): number of aeration stress days

    Returns:

        WrAct (float):  Actual rootzone water content

        Dr_Zt (float):  topsoil depletion

        Dr_Rz (float):  rootzone depletion

        TAW_Zt (float):  topsoil total available water

        TAW_Rz (float):  rootzone total available water

        thRZ_Act (float):  Actual rootzone water content

        thRZ_S (float):  rootzone water content at saturation

        thRZ_FC (float):  rootzone water content at field capacity

        thRZ_WP (float):  rootzone water content at wilting point

        thRZ_Dry (float):  rootzone water content at air dry

        thRZ_Aer (float):  rootzone water content at aeration stress threshold 


    """
    rootdepth = np.round(np.maximum(InitCond_Zroot, Crop_Zmin), 2)
    comp_sto = np.argwhere(prof.dzsum >= rootdepth).flatten()[0]
    WrAct = 0
    WrS = 0
    WrFC = 0
    WrWP = 0
    WrDry = 0
    WrAer = 0
    for ii in range(comp_sto + 1):
        if prof.dzsum[ii] > rootdepth:
            factor = 1 - (prof.dzsum[ii] - rootdepth) / prof.dz[ii]
        else:
            factor = 1
        WrAct = WrAct + np.round(factor * 1000 * InitCond_th[ii] * prof.dz[ii], 2)
        WrS = WrS + np.round(factor * 1000 * prof.th_s[ii] * prof.dz[ii], 2)
        WrFC = WrFC + np.round(factor * 1000 * prof.th_fc[ii] * prof.dz[ii], 2)
        WrWP = WrWP + np.round(factor * 1000 * prof.th_wp[ii] * prof.dz[ii], 2)
        WrDry = WrDry + np.round(factor * 1000 * prof.th_dry[ii] * prof.dz[ii], 2)
        WrAer = WrAer + np.round(factor * 1000 * (prof.th_s[ii] - Crop_Aer / 100) * prof.dz[ii], 2)
    if WrAct < 0:
        WrAct = 0
    TAW_Rz = max(WrFC - WrWP, 0.0)
    Dr_Rz = min(WrFC - WrAct, TAW_Rz)
    thRZ_Act = WrAct / (rootdepth * 1000)
    thRZ_S = WrS / (rootdepth * 1000)
    thRZ_FC = WrFC / (rootdepth * 1000)
    thRZ_WP = WrWP / (rootdepth * 1000)
    thRZ_Dry = WrDry / (rootdepth * 1000)
    thRZ_Aer = WrAer / (rootdepth * 1000)
    if rootdepth > Soil_zTop:
        ztopdepth = np.round(Soil_zTop, 2)
        comp_sto = np.sum(prof.dzsum <= ztopdepth)
        WrAct_Zt = 0
        WrFC_Zt = 0
        WrWP_Zt = 0
        assert comp_sto > 0
        for ii in range(comp_sto):
            if prof.dzsum[ii] > ztopdepth:
                factor = 1 - (prof.dzsum[ii] - ztopdepth) / prof.dz[ii]
            else:
                factor = 1
            WrAct_Zt = WrAct_Zt + factor * 1000 * InitCond_th[ii] * prof.dz[ii]
            WrFC_Zt = WrFC_Zt + factor * 1000 * prof.th_fc[ii] * prof.dz[ii]
            WrWP_Zt = WrWP_Zt + factor * 1000 * prof.th_wp[ii] * prof.dz[ii]
        if WrAct_Zt < 0:
            WrAct_Zt = 0
        TAW_Zt = max(WrFC_Zt - WrWP_Zt, 0)
        Dr_Zt = min(WrFC_Zt - WrAct_Zt, TAW_Zt)
    else:
        Dr_Zt = Dr_Rz
        TAW_Zt = TAW_Rz
    return (WrAct, Dr_Zt, Dr_Rz, TAW_Zt, TAW_Rz, thRZ_Act, thRZ_S, thRZ_FC, thRZ_WP, thRZ_Dry, thRZ_Aer)
