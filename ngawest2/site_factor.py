# -*- coding: utf-8 -*-
"""
Created on Thu Dec 20 23:48:00 2018

@author: Jian
"""

import numpy as np

from . import BSSA14
from . import CB14
from . import CY14
from . import ASK14
from . import helper

#%%----------------------------------------------------------------------------
def site_factor(model_name, Vs30, Z10_in_m, PGA, T):
    '''
    Compute NGA-West2 site amplification factors (including both Vs30 scaling
    and basin depth scaling).
    '''

    if T > 10.0 or T < 0.01:
        raise ValueError('`T` value should be within [0.01, 10].')

    model_name = helper.check_model_name(model_name)

    Ts = {
        'BSSA': [0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25,
              0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0],
        'CB': [0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.30,
               0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0],
        'CY': [0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.10, 0.12, 0.15, 0.17,
               0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0,
               7.5, 10.0],
        'ASK': [0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.30,
                0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0],
        }

    T_array = Ts[model_name]

    if T in T_array:
        result = _site_factor(model_name, Vs30, Z10_in_m, PGA, T)
    else:
        T_low, T_high = _find_T_bounds(T_array, T)
        r1 = _site_factor(model_name, Vs30, Z10_in_m, PGA, T_low)
        r2 = _site_factor(model_name, Vs30, Z10_in_m, PGA, T_high)
        result = np.interp(T, [T_low, T_high], [r1, r2])

    return result

#%%----------------------------------------------------------------------------
def _site_factor(model_name, Vs30, Z10_in_m, PGA, T):
    '''
    Non-interpolation version of site factor calculation.
    '''

    Z10_in_km = Z10_in_m / 1000.0
    fake_M = 3  # place holders
    fake_R = 3
    fake_rake= 0
    fake_azi = 0

    if model_name == 'BSSA':
        gmpe = BSSA14.BSSA14_nga()
        gmpe(fake_M, fake_R, Vs30, T, fake_rake, Z10=Z10_in_km)
        result = np.exp(gmpe.soil_function(PGA_r=PGA))
    elif model_name == 'ASK':
        gmpe = ASK14.ASK14_nga()
        gmpe(fake_M, fake_R, Vs30, T, fake_rake, Z10=Z10_in_km, azimuth=fake_azi)
        result = np.exp(gmpe.soil_function() + gmpe.site_model(PGA))
    elif model_name == 'CB':
        gmpe = CB14.CB14_nga()
        gmpe(fake_M, fake_R, Vs30, T, fake_rake, Z10=None)  # calculate Z25 internally
        result = np.exp(gmpe.site_function(PGA) + gmpe.basin_function())
    elif model_name == 'CY':
        gmpe = CY14.CY14_nga()
        gmpe(fake_M, fake_R, Vs30, T, fake_rake, Z10=Z10_in_km, azimuth=fake_azi)
        result = np.exp(gmpe.site_function(ln_Yref=np.log(PGA)) + gmpe.basin_function())
    else:
        raise ValueError("`model_name` must be one of {'ASK', 'BSSA', 'CB', 'CY'}")

    return result

#%%----------------------------------------------------------------------------
def _find_T_bounds(T_array, T_val, T_min=0.01, T_max=10):
    '''
    Find the low and high T values surrounding the T_val provided from T_array.
    '''

    if T_val < T_min or T_val > T_max:
        raise ValueError('T out of range, should be between %.3g and %.3g sec.'
                         % (T_min, T_max))

    T_array = np.array(T_array)  # convert to numpy array

    if any(T_val == T_array):
        high_index = low_index = np.argwhere(T_val == T_array)[0][0]
    else:
        high_index = np.argwhere(T_val <= T_array)[0][0]
        low_index = max(high_index - 1, 0)  # safeguarding, if high_index is already 0

    T_low = T_array[low_index]
    T_high = T_array[high_index]

    return T_low, T_high



