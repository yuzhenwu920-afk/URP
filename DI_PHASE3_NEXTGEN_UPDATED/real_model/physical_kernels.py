"""Original AquaCrop 3.1.0 numerical functions; numba strict IEEE, no fastmath."""

import numpy as np

from numba import njit

@njit(cache=True,fastmath=False)

def evap_layer_water_content(InitCond_th, InitCond_EvapZ, prof):
    """
    Function to get water contents in the evaporation layer

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=82" target="_blank">Reference Manual: evaporation equations</a> (pg. 73-81)


    Arguments:

        InitCond_th (numpy.array): Initial water content

        InitCond_EvapZ (float): evaporation depth

        prof (SoilProfile): Soil object containing soil paramaters


    Returns:


        Wevap_Sat (float): Water storage in evaporation layer at saturation (mm)

        Wevap_Fc (float): Water storage in evaporation layer at field capacity (mm)

        Wevap_Wp (float): Water storage in evaporation layer at permanent wilting point (mm)

        Wevap_Dry (float): Water storage in evaporation layer at air dry (mm)

        Wevap_Act (float): Actual water storage in evaporation layer (mm)



    """
    comp_sto = np.sum(prof.dzsum < InitCond_EvapZ) + 1
    Wevap_Sat = 0
    Wevap_Fc = 0
    Wevap_Wp = 0
    Wevap_Dry = 0
    Wevap_Act = 0
    for ii in range(int(comp_sto)):
        if prof.dzsum[ii] > InitCond_EvapZ:
            factor = 1 - (prof.dzsum[ii] - InitCond_EvapZ) / prof.dz[ii]
        else:
            factor = 1
        Wevap_Act += factor * 1000 * InitCond_th[ii] * prof.dz[ii]
        Wevap_Sat += factor * 1000 * prof.th_s[ii] * prof.dz[ii]
        Wevap_Fc += factor * 1000 * prof.th_fc[ii] * prof.dz[ii]
        Wevap_Wp += factor * 1000 * prof.th_wp[ii] * prof.dz[ii]
        Wevap_Dry += factor * 1000 * prof.th_dry[ii] * prof.dz[ii]
    if Wevap_Act < 0:
        Wevap_Act = 0
    return (Wevap_Sat, Wevap_Fc, Wevap_Wp, Wevap_Dry, Wevap_Act)

@njit(cache=True,fastmath=False)

def soil_evaporation(ClockStruct_EvapTimeSteps, ClockStruct_SimOffSeason, ClockStruct_TimeStepCounter, prof, Soil_EvapZmin, Soil_EvapZmax, Soil_REW, Soil_Kex, Soil_fwcc, Soil_fWrelExp, Soil_fevap, Crop_CalendarType, Crop_Senescence, IrrMngt_IrrMethod, IrrMngt_WetSurf, FieldMngt_Mulches, FieldMngt_fMulch, FieldMngt_MulchPct, NewCond_DAP, NewCond_Wsurf, NewCond_EvapZ, NewCond_Stage2, NewCond_th, NewCond_DelayedCDs, NewCond_GDDcum, NewCond_DelayedGDDs, NewCond_CCxW, NewCond_CCadj, NewCond_CCxAct, NewCond_CC, NewCond_PrematSenes, NewCond_SurfaceStorage, NewCond_Wstage2, NewCond_Epot, et0, Infl, Rain, Irr, growing_season):
    """
    Function to calculate daily soil evaporation

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=82" target="_blank">Reference Manual: evaporation equations</a> (pg. 73-81)


    Arguments:

        ClockStruct_EvapTimeSteps (int): number of evaportation time steps

        ClockStruct_SimOffSeason (bool): simulate off season? (False=no, True=yes)
        
        ClockStruct_TimeStepCounter (int): time step counter

        prof (SoilProfile): soil profile object

        Soil_EvapZmin (float): minimum evaporation depth (m)

        Soil_EvapZmax (float): maximum evaporation depth (m)

        Soil_REW (float): Readily Evaporable Water 

        Soil_Kex (float): Soil evaporation coefficient

        Soil_fwcc (float): 

        Soil_fWrelExp (float): 

        Soil_fevap (float): 

        Crop_CalendarType (int): calendar type 

        Crop_Senescence (float):

        IrrMngt_IrrMethod (int): irrigation method

        IrrMngt_WetSurf (float): wet surface area

        FieldMngt_Mulches (bool): mulch present? (0=no, 1=yes)

        FieldMngt_fMulch (float): mulch factor

        FieldMngt_MulchPct (float): mulch percentage

        NewCond_DAP (int): days after planting

        NewCond_Wsurf (float): wet surface area

        NewCond_EvapZ (float): evaporation depth (m)

        NewCond_Stage2 (float): stage 2 evaporation

        NewCond_th (ndarray): soil water content

        NewCond_DelayedCDs: delayed calendar days

        NewCond_GDDcum (float): cumulative growing degree days

        NewCond_DelayedGDDs (float): delayed growing degree days

        NewCond_CCxW (float): 

        NewCond_CCadj (float): canopy cover adjusted

        NewCond_CCxAct: max canopy cover actual

        NewCond_CC (float): canopy cover

        NewCond_PrematSenes (bool): prematurity senescence? (0=no, 1=yes)

        NewCond_SurfaceStorage (float): surface storage

        NewCond_Wstage2 (float): stage 2 water content

        NewCond_Epot (float): potential evaporation

        et0 (float): daily reference evapotranspiration

        Infl (float): Infiltration on current day

        Rain (float): daily precipitation mm

        Irr (float): Irrigation applied on current day

        growing_season (bool): is growing season (True or Flase)


    Returns:

        NewCond_Epot (float): Potential surface evaporation current day

        NewCond_th (ndarray): updated soil water content

        NewCond_Stage2 (bool): stage 2 soil evaporation

        NewCond_Wstage2 (float): stage 2 soil evaporation 

        NewCond_Wsurf (float): updated surface water content

        NewCond_SurfaceStorage (float): updated surface storage

        NewCond_EvapZ (float): updated evaporation layer depth

        EsAct (float): Actual surface evaporation current day

        EsPot (float): Potential surface evaporation current day

    """
    if ClockStruct_TimeStepCounter == 0 or (NewCond_DAP == 1 and ClockStruct_SimOffSeason == False):
        NewCond_Wsurf = 0
        NewCond_EvapZ = Soil_EvapZmin
        NewCond_Stage2 = True
        Wevap_Sat, Wevap_Fc, Wevap_Wp, Wevap_Dry, Wevap_Act = evap_layer_water_content(NewCond_th, NewCond_EvapZ, prof)
        NewCond_Wstage2 = round((Wevap_Act - (Wevap_Fc - Soil_REW)) / (Wevap_Sat - (Wevap_Fc - Soil_REW)), 2)
        if NewCond_Wstage2 < 0:
            NewCond_Wstage2 = 0
    if Rain > 0 or (Irr > 0 and IrrMngt_IrrMethod != 4):
        if Infl > 0:
            NewCond_Wsurf = Infl
            if NewCond_Wsurf > Soil_REW:
                NewCond_Wsurf = Soil_REW
            NewCond_Wstage2 = 0
            NewCond_EvapZ = Soil_EvapZmin
            NewCond_Stage2 = False
    if growing_season == True:
        if Crop_CalendarType == 1:
            tAdj = NewCond_DAP - NewCond_DelayedCDs
        elif Crop_CalendarType == 2:
            tAdj = NewCond_GDDcum - NewCond_DelayedGDDs
        EsPotMax = Soil_Kex * et0 * (1 - NewCond_CCxW * (Soil_fwcc / 100))
        EsPot = Soil_Kex * (1 - NewCond_CCadj) * et0
        if tAdj > Crop_Senescence and NewCond_CCxAct > 0:
            if NewCond_CC > NewCond_CCxAct / 2:
                if NewCond_CC > NewCond_CCxAct:
                    mult = 0
                else:
                    mult = (NewCond_CCxAct - NewCond_CC) / (NewCond_CCxAct / 2)
            else:
                mult = 1
            EsPot = EsPot * (1 - NewCond_CCxAct * (Soil_fwcc / 100) * mult)
            CCxActAdj = 1.72 * NewCond_CCxAct - NewCond_CCxAct ** 2 + 0.3 * NewCond_CCxAct ** 3
            EsPotMin = Soil_Kex * (1 - CCxActAdj) * et0
            if EsPotMin < 0:
                EsPotMin = 0
            if EsPot < EsPotMin:
                EsPot = EsPotMin
            elif EsPot > EsPotMax:
                EsPot = EsPotMax
        if NewCond_PrematSenes == True:
            if EsPot > EsPotMax:
                EsPot = EsPotMax
    else:
        EsPot = Soil_Kex * et0
    if NewCond_SurfaceStorage < 1e-06:
        if not FieldMngt_Mulches:
            EsPotMul = EsPot
        elif FieldMngt_Mulches:
            EsPotMul = EsPot * (1 - FieldMngt_fMulch * (FieldMngt_MulchPct / 100))
    else:
        EsPotMul = EsPot
    if Irr > 0 and IrrMngt_IrrMethod != 4:
        if Rain > 1 or NewCond_SurfaceStorage > 0:
            EsPotIrr = EsPot
        else:
            EsPotIrr = EsPot * (IrrMngt_WetSurf / 100)
    else:
        EsPotIrr = EsPot
    EsPot = min(EsPotIrr, EsPotMul)
    EsAct = 0
    if NewCond_SurfaceStorage > 0:
        if NewCond_SurfaceStorage > EsPot:
            EsAct = EsPot
            NewCond_SurfaceStorage = NewCond_SurfaceStorage - EsAct
        else:
            EsAct = NewCond_SurfaceStorage
            NewCond_SurfaceStorage = 0
            NewCond_Wsurf = Soil_REW
            NewCond_Wstage2 = 0
            NewCond_EvapZ = Soil_EvapZmin
            NewCond_Stage2 = False
    ToExtract = EsPot - EsAct
    ExtractPotStg1 = min(ToExtract, NewCond_Wsurf)
    if ExtractPotStg1 > 0:
        comp_sto = np.sum(prof.dzsum < Soil_EvapZmin) + 1
        comp = -1
        while ExtractPotStg1 > 0 and comp < comp_sto:
            comp = comp + 1
            if prof.dzsum[comp] > Soil_EvapZmin:
                factor = 1 - (prof.dzsum[comp] - Soil_EvapZmin) / prof.dz[comp]
            else:
                factor = 1
            Wdry = 1000 * prof.th_dry[comp] * prof.dz[comp]
            W = 1000 * NewCond_th[comp] * prof.dz[comp]
            AvW = (W - Wdry) * factor
            if AvW < 0:
                AvW = 0
            if AvW >= ExtractPotStg1:
                EsAct = EsAct + ExtractPotStg1
                W = W - ExtractPotStg1
                ToExtract = ToExtract - ExtractPotStg1
                ExtractPotStg1 = 0
            else:
                EsAct = EsAct + AvW
                ExtractPotStg1 = ExtractPotStg1 - AvW
                ToExtract = ToExtract - AvW
                W = W - AvW
            NewCond_th[comp] = W / (1000 * prof.dz[comp])
        NewCond_Wsurf = NewCond_Wsurf - EsAct
        if NewCond_Wsurf < 0 or ExtractPotStg1 > 0.0001:
            NewCond_Wsurf = 0
        if NewCond_Wsurf < 0.0001:
            Wevap_Sat, Wevap_Fc, Wevap_Wp, Wevap_Dry, Wevap_Act = evap_layer_water_content(NewCond_th, NewCond_EvapZ, prof)
            NewCond_Wstage2 = round((Wevap_Act - (Wevap_Fc - Soil_REW)) / (Wevap_Sat - (Wevap_Fc - Soil_REW)), 2)
            if NewCond_Wstage2 < 0:
                NewCond_Wstage2 = 0
    if ToExtract > 0:
        NewCond_Stage2 = True
        Edt = ToExtract / ClockStruct_EvapTimeSteps
        for jj in range(int(ClockStruct_EvapTimeSteps)):
            Wevap_Sat, Wevap_Fc, Wevap_Wp, Wevap_Dry, Wevap_Act = evap_layer_water_content(NewCond_th, NewCond_EvapZ, prof)
            Wupper = NewCond_Wstage2 * (Wevap_Sat - (Wevap_Fc - Soil_REW)) + (Wevap_Fc - Soil_REW)
            Wlower = Wevap_Dry
            Wrel = (Wevap_Act - Wlower) / (Wupper - Wlower)
            if Soil_EvapZmax > Soil_EvapZmin:
                Wcheck = Soil_fWrelExp * ((Soil_EvapZmax - NewCond_EvapZ) / (Soil_EvapZmax - Soil_EvapZmin))
                while Wrel < Wcheck and NewCond_EvapZ < Soil_EvapZmax:
                    NewCond_EvapZ = NewCond_EvapZ + 0.001
                    Wevap_Sat, Wevap_Fc, Wevap_Wp, Wevap_Dry, Wevap_Act = evap_layer_water_content(NewCond_th, NewCond_EvapZ, prof)
                    Wupper = NewCond_Wstage2 * (Wevap_Sat - (Wevap_Fc - Soil_REW)) + (Wevap_Fc - Soil_REW)
                    Wlower = Wevap_Dry
                    Wrel = (Wevap_Act - Wlower) / (Wupper - Wlower)
                    Wcheck = Soil_fWrelExp * ((Soil_EvapZmax - NewCond_EvapZ) / (Soil_EvapZmax - Soil_EvapZmin))
            Kr = (np.exp(Soil_fevap * Wrel) - 1) / (np.exp(Soil_fevap) - 1)
            if Kr > 1:
                Kr = 1
            ToExtractStg2 = Kr * Edt
            comp_sto = np.sum(prof.dzsum < NewCond_EvapZ) + 1
            comp = -1
            while ToExtractStg2 > 0 and comp < comp_sto:
                comp = comp + 1
                if prof.dzsum[comp] > NewCond_EvapZ:
                    factor = 1 - (prof.dzsum[comp] - NewCond_EvapZ) / prof.dz[comp]
                else:
                    factor = 1
                Wdry = 1000 * prof.th_dry[comp] * prof.dz[comp]
                W = 1000 * NewCond_th[comp] * prof.dz[comp]
                AvW = (W - Wdry) * factor
                if AvW >= ToExtractStg2:
                    EsAct = EsAct + ToExtractStg2
                    W = W - ToExtractStg2
                    ToExtract = ToExtract - ToExtractStg2
                    ToExtractStg2 = 0
                else:
                    EsAct = EsAct + AvW
                    W = W - AvW
                    ToExtractStg2 = ToExtractStg2 - AvW
                    ToExtract = ToExtract - AvW
                NewCond_th[comp] = W / (1000 * prof.dz[comp])
    NewCond_Epot = EsPot
    return (NewCond_Epot, NewCond_th, NewCond_Stage2, NewCond_Wstage2, NewCond_Wsurf, NewCond_SurfaceStorage, NewCond_EvapZ, EsAct, EsPot)

@njit(cache=True,fastmath=False)

def water_stress(Crop_p_up, Crop_p_lo, Crop_ETadj, Crop_beta, Crop_fshape_w, InitCond_tEarlySen, Dr, taw, et0, beta):
    """
    Function to calculate water stress coefficients

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=18" target="_blank">Reference Manual: water stress equations</a> (pg. 9-13)


    Arguments:


        Crop_p_up (ndarray): water stress thresholds for start of water stress

        Crop_p_lo (ndarray): water stress thresholds for maximum water stress

        Crop_ETadj (float): 

        Crop_beta (float): 

        Crop_fshape_w (ndarray): shape factors for water stress

        InitCond_tEarlySen (float): days in early senesence

        Dr (Dr): rootzone depletion

        taw (TAW): root zone total available water

        et0 (float): Reference Evapotranspiration

        beta (float): Adjust senescence threshold if early sensescence is triggered


    Returns:

        Ksw (Ksw): Ksw object containint water stress coefficients


    """
    nstress = len(Crop_p_up)
    p_up = np.ones(nstress) * Crop_p_up
    p_lo = np.ones(nstress) * Crop_p_lo
    if Crop_ETadj == 1:
        for ii in range(3):
            p_up[ii] = p_up[ii] + 0.04 * (5 - et0) * np.log10(10 - 9 * p_up[ii])
            p_lo[ii] = p_lo[ii] + 0.04 * (5 - et0) * np.log10(10 - 9 * p_lo[ii])
    if beta == True and InitCond_tEarlySen > 0:
        p_up[2] = p_up[2] * (1 - Crop_beta / 100)
    p_up = np.maximum(p_up, np.zeros(4))
    p_lo = np.maximum(p_lo, np.zeros(4))
    p_up = np.minimum(p_up, np.ones(4))
    p_lo = np.minimum(p_lo, np.ones(4))
    Drel = np.zeros(nstress)
    for ii in range(nstress):
        if Dr <= p_up[ii] * taw:
            Drel[ii] = 0
        elif Dr > p_up[ii] * taw and Dr < p_lo[ii] * taw:
            Drel[ii] = 1 - (p_lo[ii] - Dr / taw) / (p_lo[ii] - p_up[ii])
        elif Dr >= p_lo[ii] * taw:
            Drel[ii] = 1
    Ks = np.ones(3)
    for ii in range(3):
        Ks[ii] = 1 - (np.exp(Drel[ii] * Crop_fshape_w[ii]) - 1) / (np.exp(Crop_fshape_w[ii]) - 1)
    Ksw_Exp = Ks[0]
    Ksw_Sto = Ks[1]
    Ksw_Sen = Ks[2]
    Ksw_Pol = 1 - Drel[3]
    Ksw_StoLin = 1 - Drel[1]
    return (Ksw_Exp, Ksw_Sto, Ksw_Sen, Ksw_Pol, Ksw_StoLin)

@njit(cache=True,fastmath=False)

def root_development(Crop, prof, NewCond_DAP, NewCond_Zroot, NewCond_DelayedCDs, NewCond_GDDcum, NewCond_DelayedGDDs, NewCond_TrRatio, NewCond_th, NewCond_CC, NewCond_CC_NS, NewCond_Germination, NewCond_rCor, NewCond_Tpot, NewCond_zGW, gdd, growing_season, water_table_presence):
    """
    Function to calculate root zone expansion

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=46" target="_blank">Reference Manual: root developement equations</a> (pg. 37-41)


    Arguments:

        Crop (Crop): crop params

        prof (SoilProfile): soilv profile paramaters

        NewCond_DAP (float): days after planting

        NewCond_Zroot (float): root depth

        NewCond_DelayedCDs (float): delayed calendar days

        NewCond_GDDcum (float): cumulative growing degree days

        NewCond_TrRatio (float): transpiration ratio

        NewCond_CC (float): canopy cover

        NewCond_CC_NS (float): canopy cover no-stress

        NewCond_Germination (float): germination flag

        NewCond_rCor (float): 

        NewCond_DAP (float): days after planting

        NewCond_Tpot (float): potential transpiration

        NewCond_zGW (float): groundwater depth

        gdd (float): Growing degree days on current day

        growing_season (bool): is growing season (True or Flase)

        water_table_presence (int): water table present (True=1 or Flase=0)


    Returns:

        NewCond_Zroot (float): updated rooting depth


    """
    Zroot_init = float(NewCond_Zroot) * 1.0
    Soil_nLayer = np.unique(prof.Layer).shape[0]
    if growing_season == True:
        if NewCond_DAP == 1:
            NewCond_Zroot = float(Crop.Zmin) * 1.0
            Zroot_init = float(Crop.Zmin) * 1.0
        if Crop.CalendarType == 1:
            tAdj = NewCond_DAP - NewCond_DelayedCDs
        elif Crop.CalendarType == 2:
            tAdj = NewCond_GDDcum - NewCond_DelayedGDDs
        Zini = Crop.Zmin * (Crop.PctZmin / 100)
        t0 = round(Crop.Emergence / 2)
        tmax = Crop.MaxRooting
        if Crop.CalendarType == 1:
            tOld = tAdj - 1
        elif Crop.CalendarType == 2:
            tOld = tAdj - gdd
        if tOld >= tmax:
            ZrOld = Crop.Zmax
        elif tOld <= t0:
            ZrOld = Zini
        else:
            X = (tOld - t0) / (tmax - t0)
            ZrOld = Zini + (Crop.Zmax - Zini) * np.power(X, 1 / Crop.fshape_r)
        if ZrOld < Crop.Zmin:
            ZrOld = Crop.Zmin
        if tAdj >= tmax:
            Zr = Crop.Zmax
        elif tAdj <= t0:
            Zr = Zini
        else:
            X = (tAdj - t0) / (tmax - t0)
            Zr = Zini + (Crop.Zmax - Zini) * np.power(X, 1 / Crop.fshape_r)
        if Zr < Crop.Zmin:
            Zr = Crop.Zmin
        ZrPot = Zr
        dZr = Zr - ZrOld
        if Zr > Crop.Zmin:
            layeri = 1
            l_idx = np.argwhere(prof.Layer == layeri).flatten()
            Zsoil = prof.dz[l_idx].sum()
            while round(Zsoil, 2) <= Crop.Zmin and layeri < Soil_nLayer:
                layeri = layeri + 1
                l_idx = np.argwhere(prof.Layer == layeri).flatten()
                Zsoil = Zsoil + prof.dz[l_idx].sum()
            soil_layer_dz = prof.dz[l_idx].sum()
            layer_comp = l_idx[0]
            ZrAdj = Crop.Zmin
            ZrRemain = Zr - Crop.Zmin
            deltaZ = Zsoil - Crop.Zmin
            EndProf = False
            while EndProf == False:
                ZrTest = ZrAdj + ZrRemain * (prof.Penetrability[layer_comp] / 100)
                if layeri == Soil_nLayer or prof.Penetrability[layer_comp] == 0 or ZrTest <= Zsoil:
                    ZrOUT = ZrTest
                    EndProf = True
                else:
                    ZrAdj = Zsoil
                    ZrRemain = ZrRemain - deltaZ / (prof.Penetrability[layer_comp] / 100)
                    layeri = layeri + 1
                    l_idx = np.argwhere(prof.Layer == layeri).flatten()
                    layer_comp = l_idx[0]
                    soil_layer_dz = prof.dz[l_idx].sum()
                    Zsoil = Zsoil + soil_layer_dz
                    deltaZ = soil_layer_dz
            Zr = max(ZrOUT, ZrOld)
            dZr = Zr - ZrOld
        if NewCond_TrRatio < 0.9999:
            if Crop.fshape_ex >= 0:
                dZr = dZr * NewCond_TrRatio
            else:
                fAdj = (np.exp(NewCond_TrRatio * Crop.fshape_ex) - 1) / (np.exp(Crop.fshape_ex) - 1)
                dZr = dZr * fAdj
        if dZr > 0.001:
            pZexp = Crop.p_up[1] + (1 - Crop.p_up[1]) / 2
            ZiTmp = float(Zroot_init + dZr)
            idx = np.argwhere(prof.dzsum >= ZiTmp).flatten()[0]
            prof = prof
            layeri = prof.Layer[idx]
            TAWprof = prof.th_fc[idx] - prof.th_wp[idx]
            thThr = prof.th_fc[idx] - pZexp * TAWprof
            if NewCond_th[idx] < thThr:
                if NewCond_th[idx] <= prof.th_wp[idx]:
                    dZr = 0
                else:
                    Wrel = (prof.th_fc[idx] - NewCond_th[idx]) / TAWprof
                    Drel = 1 - (1 - Wrel) / (1 - pZexp)
                    Ks = 1 - (np.exp(Drel * Crop.fshape_w[1]) - 1) / (np.exp(Crop.fshape_w[1]) - 1)
                    dZr = dZr * Ks
        if NewCond_CC <= 0 and NewCond_CC_NS > 0.5:
            dZr = 0
        if NewCond_Germination == False:
            dZr = 0
        NewCond_Zroot = float(Zroot_init + dZr)
        if NewCond_Zroot < ZrPot:
            NewCond_rCor = (2 * (ZrPot / NewCond_Zroot) * ((Crop.SxTop + Crop.SxBot) / 2) - Crop.SxTop) / Crop.SxBot
            if NewCond_Tpot > 0:
                NewCond_rCor = NewCond_rCor * NewCond_TrRatio
                if NewCond_rCor < 1:
                    NewCond_rCor = 1
        else:
            NewCond_rCor = 1
        if water_table_presence == 1 and NewCond_zGW > 0:
            if NewCond_Zroot > NewCond_zGW:
                NewCond_Zroot = float(NewCond_zGW)
                if NewCond_Zroot < Crop.Zmin:
                    NewCond_Zroot = float(Crop.Zmin)
    else:
        NewCond_Zroot = 0
    return (NewCond_Zroot, NewCond_rCor)

@njit(cache=True,fastmath=False)

def drainage(prof, th_init, th_fc_Adj_init):
    """
    Function to redistribute stored soil water


    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=51" target="_blank">Reference Manual: drainage calculations</a> (pg. 42-65)


    Arguments:

        prof (SoilProfile): jit class object object containing soil paramaters

        th_init (numpy.array): initial water content

        th_fc_Adj_init (numpy.array): adjusted water content at field capacity


    Returns:

        thnew (numpy.array): updated water content in each compartment

        DeepPerc (float): Total Deep Percolation

        FluxOut (numpy.array): flux of water out of each compartment




    """
    thnew = np.zeros(th_init.shape[0])
    FluxOut = np.zeros(th_init.shape[0])
    drainsum = 0
    for ii in range(th_init.shape[0]):
        cth_fc = prof.th_fc[ii]
        cth_s = prof.th_s[ii]
        ctau = prof.tau[ii]
        cdz = prof.dz[ii]
        cdzsum = prof.dzsum[ii]
        cKsat = prof.Ksat[ii]
        if th_init[ii] <= th_fc_Adj_init[ii]:
            dthdt = 0
        elif th_init[ii] >= cth_s:
            dthdt = ctau * (cth_s - cth_fc)
            if th_init[ii] - dthdt < th_fc_Adj_init[ii]:
                dthdt = th_init[ii] - th_fc_Adj_init[ii]
        else:
            dthdt = ctau * (cth_s - cth_fc) * ((np.exp(th_init[ii] - cth_fc) - 1) / (np.exp(cth_s - cth_fc) - 1))
            if th_init[ii] - dthdt < th_fc_Adj_init[ii]:
                dthdt = th_init[ii] - th_fc_Adj_init[ii]
        draincomp = dthdt * cdz * 1000
        excess = 0
        prethick = cdzsum - cdz
        drainmax = dthdt * 1000 * prethick
        if drainsum <= drainmax:
            drainability = True
        else:
            drainability = False
        if drainability == True:
            thnew[ii] = th_init[ii] - dthdt
            drainsum = drainsum + draincomp
            if drainsum > cKsat:
                excess = excess + drainsum - cKsat
                drainsum = cKsat
        elif drainability == False:
            dthdt = drainsum / (1000 * prethick)
            if dthdt <= 0:
                thX = th_fc_Adj_init[ii]
            elif ctau > 0:
                A = 1 + dthdt * (np.exp(cth_s - cth_fc) - 1) / (ctau * (cth_s - cth_fc))
                thX = cth_fc + np.log(A)
                if thX < th_fc_Adj_init[ii]:
                    thX = th_fc_Adj_init[ii]
            else:
                thX = cth_s + 0.01
            if thX <= cth_s:
                thnew[ii] = th_init[ii] + drainsum / (1000 * cdz)
                if thnew[ii] > thX:
                    drainsum = (thnew[ii] - thX) * 1000 * cdz
                    if thX <= th_fc_Adj_init[ii]:
                        dthdt = 0
                    elif thX >= cth_s:
                        dthdt = ctau * (cth_s - cth_fc)
                        if thX - dthdt < th_fc_Adj_init[ii]:
                            dthdt = thX - th_fc_Adj_init[ii]
                    else:
                        dthdt = ctau * (cth_s - cth_fc) * ((np.exp(thX - cth_fc) - 1) / (np.exp(cth_s - cth_fc) - 1))
                        if thX - dthdt < th_fc_Adj_init[ii]:
                            dthdt = thX - th_fc_Adj_init[ii]
                    drainsum = drainsum + dthdt * 1000 * cdz
                    if drainsum > cKsat:
                        excess = excess + drainsum - cKsat
                        drainsum = cKsat
                    thnew[ii] = thX - dthdt
                elif thnew[ii] > th_fc_Adj_init[ii]:
                    if thnew[ii] <= th_fc_Adj_init[ii]:
                        dthdt = 0
                    elif thnew[ii] >= cth_s:
                        dthdt = ctau * (cth_s - cth_fc)
                        if thnew[ii] - dthdt < th_fc_Adj_init[ii]:
                            dthdt = thnew[ii] - th_fc_Adj_init[ii]
                    else:
                        dthdt = ctau * (cth_s - cth_fc) * ((np.exp(thnew[ii] - cth_fc) - 1) / (np.exp(cth_s - cth_fc) - 1))
                        if thnew[ii] - dthdt < th_fc_Adj_init[ii]:
                            dthdt = thnew[ii] - th_fc_Adj_init[ii]
                    thnew[ii] = thnew[ii] - dthdt
                    drainsum = dthdt * 1000 * cdz
                    if drainsum > cKsat:
                        excess = excess + drainsum - cKsat
                        drainsum = cKsat
                else:
                    drainsum = 0
            elif thX > cth_s:
                thnew[ii] = th_init[ii] + drainsum / (1000 * cdz)
                if thnew[ii] <= cth_s:
                    if thnew[ii] > th_fc_Adj_init[ii]:
                        if thnew[ii] <= th_fc_Adj_init[ii]:
                            dthdt = 0
                        elif thnew[ii] >= cth_s:
                            dthdt = ctau * (cth_s - cth_fc)
                            if thnew[ii] - dthdt < th_fc_Adj_init[ii]:
                                dthdt = thnew[ii] - th_fc_Adj_init[ii]
                        else:
                            dthdt = ctau * (cth_s - cth_fc) * ((np.exp(thnew[ii] - cth_fc) - 1) / (np.exp(cth_s - cth_fc) - 1))
                            if thnew[ii] - dthdt < th_fc_Adj_init[ii]:
                                dthdt = thnew[ii] - th_fc_Adj_init[ii]
                        thnew[ii] = thnew[ii] - dthdt
                        drainsum = dthdt * 1000 * cdz
                        if drainsum > cKsat:
                            excess = excess + drainsum - cKsat
                            drainsum = cKsat
                    else:
                        drainsum = 0
                elif thnew[ii] > cth_s:
                    excess = (thnew[ii] - cth_s) * 1000 * cdz
                    if thnew[ii] <= th_fc_Adj_init[ii]:
                        dthdt = 0
                    elif thnew[ii] >= cth_s:
                        dthdt = ctau * (cth_s - cth_fc)
                        if thnew[ii] - dthdt < th_fc_Adj_init[ii]:
                            dthdt = thnew[ii] - th_fc_Adj_init[ii]
                    else:
                        dthdt = ctau * (cth_s - cth_fc) * ((np.exp(thnew[ii] - cth_fc) - 1) / (np.exp(cth_s - cth_fc) - 1))
                        if thnew[ii] - dthdt < th_fc_Adj_init[ii]:
                            dthdt = thnew[ii] - th_fc_Adj_init[ii]
                    thnew[ii] = cth_s - dthdt
                    draincomp = dthdt * 1000 * cdz
                    drainmax = dthdt * 1000 * prethick
                    if drainmax > excess:
                        drainmax = excess
                    excess = excess - drainmax
                    drainsum = draincomp + drainmax
                    if drainsum > cKsat:
                        excess = excess + drainsum - cKsat
                        drainsum = cKsat
        FluxOut[ii] = drainsum
        if excess > 0:
            precomp = ii + 1
            while excess > 0 and precomp != 0:
                precomp = precomp - 1
                if precomp < ii:
                    FluxOut[precomp] = FluxOut[precomp] - excess
                thnew[precomp] = thnew[precomp] + excess / (1000 * prof.dz[precomp])
                if thnew[precomp] > prof.th_s[precomp]:
                    excess = (thnew[precomp] - prof.th_s[precomp]) * 1000 * prof.dz[precomp]
                    thnew[precomp] = prof.th_s[precomp]
                else:
                    excess = 0
    DeepPerc = drainsum
    return (thnew, DeepPerc, FluxOut)

@njit(cache=True,fastmath=False)

def rainfall_partition(precipitation, InitCond_th, NewCond_DaySubmerged, FieldMngt_SRinhb, FieldMngt_Bunds, FieldMngt_zBund, FieldMngt_CNadjPct, Soil_CN, Soil_AdjCN, Soil_zCN, Soil_nComp, prof):
    """
    Function to partition rainfall into surface runoff and infiltration using the curve number approach


    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=57" target="_blank">Reference Manual: rainfall partition calculations</a> (pg. 48-51)


    Arguments:

        precipitation (float): Percipitation on current day

        InitCond_th (numpy.array): InitCond object containing model paramaters

        NewCond_DaySubmerged (int): number of days submerged

        FieldMngt_SRinhb (float): field management params

        FieldMngt_Bunds (bool): field management params

        FieldMngt_zBund (float): bund height

        FieldMngt_CNadjPct (float): curve number adjustment percent

        Soil_CN (float): curve number

        Soil_AdjCN (float): adjusted curve number

        Soil_zCN (float` :

        Soil_nComp (float): number of compartments

        prof (SoilProfile): Soil object

    Returns:

        Runoff (float): Total Suface Runoff

        Infl (float): Total Infiltration

        NewCond_DaySubmerged (float): number of days submerged


    """
    if FieldMngt_SRinhb == False and (FieldMngt_Bunds == False or FieldMngt_zBund < 0.001):
        NewCond_DaySubmerged = 0
        cn = Soil_CN * (1 + FieldMngt_CNadjPct / 100)
        if Soil_AdjCN == 1:
            CNbot = round(1.4 * np.exp(-14 * np.log(10)) + 0.507 * cn - 0.00374 * cn ** 2 + 8.67e-05 * cn ** 3)
            CNtop = round(5.6 * np.exp(-14 * np.log(10)) + 2.33 * cn - 0.0209 * cn ** 2 + 7.6e-05 * cn ** 3)
            comp_sto_array = prof.dzsum[prof.dzsum >= Soil_zCN]
            if comp_sto_array.shape[0] == 0:
                comp_sto = int(Soil_nComp)
            else:
                comp_sto = int(Soil_nComp - comp_sto_array.shape[0])
            comp_sto += 1
            xx = 0
            wrel = np.zeros(comp_sto)
            for ii in range(comp_sto):
                if prof.dzsum[ii] > Soil_zCN:
                    prof.dzsum[ii] = Soil_zCN
                wx = 1.016 * (1 - np.exp(-4.16 * (prof.dzsum[ii] / Soil_zCN)))
                wrel[ii] = wx - xx
                if wrel[ii] < 0:
                    wrel[ii] = 0
                elif wrel[ii] > 1:
                    wrel[ii] = 1
                xx = wx
            wet_top = 0
            for ii in range(comp_sto):
                th = max(prof.th_wp[ii], InitCond_th[ii])
                wet_top = wet_top + wrel[ii] * ((th - prof.th_wp[ii]) / (prof.th_fc[ii] - prof.th_wp[ii]))
            if wet_top > 1:
                wet_top = 1
            elif wet_top < 0:
                wet_top = 0
            cn = round(CNbot + (CNtop - CNbot) * wet_top)
        S = 25400 / cn - 254
        term = precipitation - 5 / 100 * S
        if term <= 0:
            Runoff = 0
            Infl = precipitation
        else:
            Runoff = term ** 2 / (precipitation + (1 - 5 / 100) * S)
            Infl = precipitation - Runoff
    else:
        Runoff = 0
        Infl = precipitation
    return (Runoff, Infl, NewCond_DaySubmerged)

@njit(cache=True,fastmath=False)

def growing_degree_day(GDDmethod, Tupp, Tbase, temp_max, temp_min):
    """
    Function to calculate number of growing degree days on current day

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=28" target="_blank">Reference manual: growing degree day calculations</a> (pg. 19-20)


    Arguments:

        GDDmethod (int): gdd calculation method

        Tupp (float): Upper temperature (degC) above which crop development no longer increases

        Tbase (float): Base temperature (degC) below which growth does not progress

        temp_max (float): Maximum tempature on current day (celcius)

        temp_min (float): Minimum tempature on current day (celcius)


    Returns:

        gdd (float): Growing degree days for current day



    """
    if GDDmethod == 1:
        Tmean = (temp_max + temp_min) / 2
        Tmean = min(Tmean, Tupp)
        Tmean = max(Tmean, Tbase)
        gdd = Tmean - Tbase
    elif GDDmethod == 2:
        temp_max = min(temp_max, Tupp)
        temp_max = max(temp_max, Tbase)
        temp_min = min(temp_min, Tupp)
        temp_min = max(temp_min, Tbase)
        Tmean = (temp_max + temp_min) / 2
        gdd = Tmean - Tbase
    elif GDDmethod == 3:
        temp_max = min(temp_max, Tupp)
        temp_max = max(temp_max, Tbase)
        temp_min = min(temp_min, Tupp)
        Tmean = (temp_max + temp_min) / 2
        Tmean = max(Tmean, Tbase)
        gdd = Tmean - Tbase
    return gdd

@njit(cache=True,fastmath=False)

def aeration_stress(NewCond_AerDays, Crop_LagAer, thRZ):
    """
    Function to calculate aeration stress coefficient

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=90" target="_blank">Reference Manual: aeration stress</a> (pg. 89-90)


    Arguments:

        NewCond_AerDays (int): number aeration stress days

        Crop_LagAer (int): lag days before aeration stress

        thRZ (NamedTuple): object that contains information on the total water in the root zone


    Returns:

        Ksa_Aer (float): aeration stress coefficient

        NewCond_AerDays (float): updated aer days



    """
    if thRZ.Act > thRZ.Aer:
        if NewCond_AerDays < Crop_LagAer:
            stress = 1 - (thRZ.S - thRZ.Act) / (thRZ.S - thRZ.Aer)
            Ksa_Aer = 1 - NewCond_AerDays / 3 * stress
        elif NewCond_AerDays >= Crop_LagAer:
            Ksa_Aer = (thRZ.S - thRZ.Act) / (thRZ.S - thRZ.Aer)
        NewCond_AerDays = NewCond_AerDays + 1
        if NewCond_AerDays > Crop_LagAer:
            NewCond_AerDays = Crop_LagAer
    else:
        Ksa_Aer = 1
        NewCond_AerDays = 0
    return (Ksa_Aer, NewCond_AerDays)

@njit(cache=True,fastmath=False)

def temperature_stress(Crop, temp_max, temp_min):
    """
    Function to get irrigation depth for current day

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=23" target="_blank">Reference Manual: temperature stress</a> (pg. 14)



    Arguments:

        Crop (Crop): Crop object containing Crop paramaters

        temp_max (float): max tempatature on current day (celcius)

        temp_min (float): min tempature on current day (celcius)


    Returns:

        Kst_PolH (float): heat stress coefficient for current day

        Kst_PolC (float): cold stress coefficient for current day







    """
    KsPol_up = 1
    KsPol_lo = 0.001
    if Crop.PolHeatStress == 0:
        Kst_PolH = 1
    elif Crop.PolHeatStress == 1:
        if temp_max <= Crop.Tmax_lo:
            Kst_PolH = 1
        elif temp_max >= Crop.Tmax_up:
            Kst_PolH = 0
        else:
            Trel = (temp_max - Crop.Tmax_lo) / (Crop.Tmax_up - Crop.Tmax_lo)
            Kst_PolH = KsPol_up * KsPol_lo / (KsPol_lo + (KsPol_up - KsPol_lo) * np.exp(-Crop.fshape_b * (1 - Trel)))
    if Crop.PolColdStress == 0:
        Kst_PolC = 1
    elif Crop.PolColdStress == 1:
        if temp_min >= Crop.Tmin_up:
            Kst_PolC = 1
        elif temp_min <= Crop.Tmin_lo:
            Kst_PolC = 0
        else:
            Trel = (Crop.Tmin_up - temp_min) / (Crop.Tmin_up - Crop.Tmin_lo)
            Kst_PolC = KsPol_up * KsPol_lo / (KsPol_lo + (KsPol_up - KsPol_lo) * np.exp(-Crop.fshape_b * (1 - Trel)))
    return (Kst_PolH, Kst_PolC)

@njit(cache=True,fastmath=False)

def cc_development(CCo, CCx, CGC, CDC, dt, Mode, CCx0):
    """
    Function to calculate canopy cover development by end of the current simulation day

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=30" target="_blank">Reference Manual: canopy_cover devlopment</a> (pg. 21-24)


    Arguments:


        CCo (float): Fractional canopy cover size at emergence

        CCx (float): Maximum canopy cover (fraction of soil cover)

        CGC (float): Canopy growth coefficient (fraction per gdd)

        CDC (float): Canopy decline coefficient (fraction per gdd/calendar day)

        dt (float): Time delta of canopy growth (1 calander day or ... gdd)

        Mode (str): stage of Canopy developement (Growth or Decline)

        CCx0 (float): Maximum canopy cover (fraction of soil cover)

    Returns:

        canopy_cover (float): Canopy Cover



    """
    if Mode == 'Growth':
        canopy_cover = CCo * np.exp(CGC * dt)
        if canopy_cover > CCx / 2:
            canopy_cover = CCx - 0.25 * (CCx / CCo) * CCx * np.exp(-CGC * dt)
        if canopy_cover > CCx:
            canopy_cover = CCx
    elif Mode == 'Decline':
        if CCx < 0.001:
            canopy_cover = 0
        else:
            canopy_cover = CCx * (1 - 0.05 * (np.exp(dt * CDC * 3.33 * ((CCx + 2.29) / (CCx0 + 2.29)) / (CCx + 2.29)) - 1))
    if canopy_cover > 1:
        canopy_cover = 1
    elif canopy_cover < 0:
        canopy_cover = 0
    return canopy_cover

@njit(cache=True,fastmath=False)

def cc_required_time(cc_prev, CCo, CCx, CGC, CDC, Mode):
    """
    Function to find time required to reach canopy_cover at end of previous day, given current CGC or CDC

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=30" target="_blank">Reference Manual: canopy_cover devlopment</a> (pg. 21-24)


    Arguments:

        cc_prev (float): Canopy Cover at previous timestep.

        CCo (float): Fractional canopy cover size at emergence

        CCx (float): Maximum canopy cover (fraction of soil cover)

        CGC (float): Canopy growth coefficient (fraction per gdd)

        CDC (float): Canopy decline coefficient (fraction per gdd/calendar day)

        Mode (str): Canopy growth/decline coefficient (fraction per gdd/calendar day)


    Returns:

        tReq (float): time required to reach canopy_cover at end of previous day





    """
    if Mode == 'CGC':
        if cc_prev <= CCx / 2:
            CGCx = np.log(cc_prev / CCo)
        else:
            CGCx = np.log(0.25 * CCx * CCx / CCo / (CCx - cc_prev))
        tReq = CGCx / CGC
    elif Mode == 'CDC':
        tReq = np.log(1 + (1 - cc_prev / CCx) / 0.05) / (CDC / CCx)
    return tReq

@njit(cache=True,fastmath=False)

def adjust_CCx(cc_prev, CCo, CCx, CGC, CDC, dt, tSum, Crop_CanopyDevEnd, Crop_CCx):
    """
    Function to adjust CCx value for changes in CGC due to water stress during the growing season

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=36" target="_blank">Reference Manual: canopy_cover stress response</a> (pg. 27-33)


    Arguments:

        cc_prev (float): Canopy Cover at previous timestep.

        CCo (float): Fractional canopy cover size at emergence

        CCx (float): Maximum canopy cover (fraction of soil cover)

        CGC (float): Canopy growth coefficient (fraction per gdd)

        CDC (float): Canopy decline coefficient (fraction per gdd/calendar day)

        dt (float): Time delta of canopy growth (1 calander day or ... gdd)

        tSum (float): time since germination (CD or gdd)

        Crop_CanopyDevEnd (float): time that Canopy developement ends

        Crop_CCx (float): Maximum canopy cover (fraction of soil cover)

    Returns:

        CCxAdj (float): Adjusted CCx



    """
    tCCtmp = cc_required_time(cc_prev, CCo, CCx, CGC, CDC, 'CGC')
    if tCCtmp > 0:
        tCCtmp = tCCtmp + (Crop_CanopyDevEnd - tSum) + dt
        CCxAdj = cc_development(CCo, CCx, CGC, CDC, tCCtmp, 'Growth', Crop_CCx)
    else:
        CCxAdj = 0
    return CCxAdj

@njit(cache=True,fastmath=False)

def update_CCx_CDC(cc_prev, CDC, CCx, dt):
    """
    Function to update CCx and CDC parameter valyes for rewatering in late season of an early declining canopy

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=36" target="_blank">Reference Manual: canopy_cover stress response</a> (pg. 27-33)


    Arguments:


        cc_prev (float): Canopy Cover at previous timestep.

        CDC (float): Canopy decline coefficient (fraction per gdd/calendar day)

        CCx (float): Maximum canopy cover (fraction of soil cover)

        dt (float): Time delta of canopy growth (1 calander day or ... gdd)


    Returns:

        CCxAdj (float): updated CCxAdj

        CDCadj (float): updated CDCadj





    """
    CCXadj = cc_prev / (1 - 0.05 * (np.exp(dt * (CDC * 3.33 / (CCx + 2.29))) - 1))
    CDCadj = CDC * ((CCXadj + 2.29) / (CCx + 2.29))
    return (CCXadj, CDCadj)

@njit(cache=True,fastmath=False)

def HIadj_pre_anthesis(NewCond_B, NewCond_B_NS, NewCond_CC, Crop_dHI_pre):
    """
    Function to calculate adjustment to harvest index for pre-anthesis water
    stress

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=119" target="_blank">Reference Manual: harvest index calculations</a> (pg. 110-126)


    Arguments:

        NewCond_B (float): biomass growth

        NewCond_B_NS (float): biomass growth (no stress)

        NewCond_CC (float): canopy cover

        Crop_dHI_pre (float): Crop_dHI_pre


    Returns:


        NewCond_Fpre (float): adjustment to harvest index for pre-anthesis water stress


    """
    if Crop_dHI_pre > 0:
        Br = NewCond_B / NewCond_B_NS
        Br_range = np.log(Crop_dHI_pre) / 5.62
        Br_upp = 1
        Br_low = 1 - Br_range
        Br_top = Br_upp - Br_range / 3
        ratio_low = (Br - Br_low) / (Br_top - Br_low)
        ratio_upp = (Br - Br_top) / (Br_upp - Br_top)
        if Br >= Br_low and Br < Br_top:
            NewCond_Fpre = 1 + (1 + np.sin((1.5 - ratio_low) * np.pi)) / 2 * (Crop_dHI_pre / 100)
        elif Br > Br_top and Br <= Br_upp:
            NewCond_Fpre = 1 + (1 + np.sin((0.5 + ratio_upp) * np.pi)) / 2 * (Crop_dHI_pre / 100)
        else:
            NewCond_Fpre = 1
    else:
        NewCond_Fpre = 1
    if NewCond_CC <= 0.01:
        NewCond_Fpre = 0
    return NewCond_Fpre

@njit(cache=True,fastmath=False)

def HIadj_post_anthesis(NewCond_DelayedCDs, NewCond_sCor1, NewCond_sCor2, NewCond_DAP, NewCond_Fpre, NewCond_CC, NewCond_fpost_upp, NewCond_fpost_dwn, Crop, Ksw):
    """
    Function to calculate adjustment to harvest index for post-anthesis water
    stress

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=119" target="_blank">Reference Manual: harvest index calculations</a> (pg. 110-126)


    Arguments:


        NewCond_DelayedCDs (int): delayed calendar days

        NewCond_sCor1 (float): canopy exapnsion

        NewCond_sCor2 (float): stomatal closure

        NewCond_DAP (int): days since planting

        NewCond_Fpre (float): delayed calendar days

        NewCond_CC (float): current canopy cover

        NewCond_fpost_upp (float): delayed calendar days

        NewCond_fpost_dwn (float): delayed calendar days

        Crop (CropStructNT): Crop paramaters

        Ksw (KswNT): water stress paramaters

    Returns:


        NewCond (InitialCondition): InitCond object containing updated model paramaters


    """
    InitCond_DelayedCDs = NewCond_DelayedCDs * 1
    InitCond_sCor1 = NewCond_sCor1 * 1
    InitCond_sCor2 = NewCond_sCor2 * 1
    tmax1 = Crop.CanopyDevEndCD - Crop.HIstartCD
    dap = NewCond_DAP - InitCond_DelayedCDs
    if dap <= Crop.CanopyDevEndCD + 1 and tmax1 > 0 and (NewCond_Fpre > 0.99) and (NewCond_CC > 0.001) and (Crop.a_HI > 0):
        dCor = 1 + (1 - Ksw.exp) / Crop.a_HI
        NewCond_sCor1 = InitCond_sCor1 + dCor / tmax1
        DayCor = dap - 1 - Crop.HIstartCD
        NewCond_fpost_upp = tmax1 / DayCor * NewCond_sCor1
    tmax2 = Crop.YldFormCD
    dap = NewCond_DAP - InitCond_DelayedCDs
    if dap <= Crop.HIendCD + 1 and tmax2 > 0 and (NewCond_Fpre > 0.99) and (NewCond_CC > 0.001) and (Crop.b_HI > 0):
        dCor = np.power(Ksw.sto, 0.1) * (1 - (1 - Ksw.sto) / Crop.b_HI)
        NewCond_sCor2 = InitCond_sCor2 + dCor / tmax2
        DayCor = dap - 1 - Crop.HIstartCD
        NewCond_fpost_dwn = tmax2 / DayCor * NewCond_sCor2
    if tmax1 == 0 and tmax2 == 0:
        NewCond_Fpost = 1
    elif tmax2 == 0:
        NewCond_Fpost = NewCond_fpost_upp
    elif tmax1 == 0:
        NewCond_Fpost = NewCond_fpost_dwn
    elif tmax1 <= tmax2:
        NewCond_Fpost = NewCond_fpost_dwn * ((tmax1 * NewCond_fpost_upp + (tmax2 - tmax1)) / tmax2)
    else:
        NewCond_Fpost = NewCond_fpost_upp * ((tmax2 * NewCond_fpost_dwn + (tmax1 - tmax2)) / tmax1)
    return (NewCond_sCor1, NewCond_sCor2, NewCond_fpost_upp, NewCond_fpost_dwn, NewCond_Fpost)

@njit(cache=True,fastmath=False)

def HIadj_pollination(NewCond_CC, NewCond_Fpol, Crop_FloweringCD, Crop_CCmin, Crop_exc, Ksw, Kst, HIt):
    """
    Function to calculate adjustment to harvest index for failure of
    pollination due to water or temperature stress

    <a href="https://www.fao.org/3/BR248E/br248e.pdf#page=119" target="_blank">Reference Manual: harvest index calculations</a> (pg. 110-126)


    Arguments:


        NewCond_CC (float): InitCond object containing model paramaters

        NewCond_Fpol (float): InitCond object containing model paramaters

        Crop_FloweringCD (float): Length of flowering stage

        Crop_CCmin (float): minimum canopy cover

        Crop_exc (float): 

        Ksw (KswNT): Ksw object containing water stress paramaters

        Kst (KstNT): Kst object containing tempature stress paramaters

        HIt (float): time for harvest index build-up (calander days)


    Returns:


        NewCond (InitialCondition): InitCond object containing updated model paramaters



    """
    if HIt == 0:
        FracFlow = 0
    elif HIt > 0:
        t1 = HIt - 1
        if t1 == 0:
            F1 = 0
        else:
            t1Pct = 100 * (t1 / Crop_FloweringCD)
            if t1Pct > 100:
                t1Pct = 100
            F1 = 0.00558 * np.exp(0.63 * np.log(t1Pct)) - 0.000969 * t1Pct - 0.00383
        if F1 < 0:
            F1 = 0
        t2 = HIt
        if t2 == 0:
            F2 = 0
        else:
            t2Pct = 100 * (t2 / Crop_FloweringCD)
            if t2Pct > 100:
                t2Pct = 100
            F2 = 0.00558 * np.exp(0.63 * np.log(t2Pct)) - 0.000969 * t2Pct - 0.00383
        if F2 < 0:
            F2 = 0
        if abs(F1 - F2) < 1e-07:
            F = 0
        else:
            F = 100 * ((F1 + F2) / 2) / Crop_FloweringCD
        FracFlow = F
    if NewCond_CC < Crop_CCmin:
        dFpol = 0
    else:
        Ks = min([Ksw.pol, Kst.PolC, Kst.PolH])
        dFpol = Ks * FracFlow * (1 + Crop_exc / 100)
    NewCond_Fpol = NewCond_Fpol + dFpol
    if NewCond_Fpol > 1:
        NewCond_Fpol = 1
    return NewCond_Fpol
