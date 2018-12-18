# -*- coding: utf-8 -*-
"""
Created on Mon Dec 17 19:11:22 2018

@author: Jian
"""

import numpy as np

from . import utils

from . import BSSA14
from . import CB14
from . import CY14
from . import ASK14

#%%----------------------------------------------------------------------------
def GMPE(model_name, Mw, Rjb, Vs30, period, epislon=0, NGAs=None,
         rake=None, Mech=3, Ftype=None, Fnm=None, Frv=None,
         dip=None, W=None, Ztor=None, Zhypo=None, Fas=0,
         Rrup=None, Rx=None, Fhw=None, azimuth=None,
         VsFlag=0, Z25=None, Z15=None, Z10=None,
         ArbCB=0, SJ=0,
         country='California', region='CA',
         Dregion='GlobalCATW',
         CRjb=15, Ry0=None,
         D_DPP=0):

    if NGAs == None:
        NGAs={'CB':{'NewCoefs':None,'terms':(1,1,1,1,1,1,1,1,1)},\
              'BSSA':{'NewCoefs':None,'terms':(1,1,1)},\
              'CY':{'NewCoefs':None,'terms':(1,1,1,1,1,1,1)},\
              'ASK':{'NewCoefs':None,'terms':(1,1,1,1,1,1,1)}}
    else:

        if 'BSSA' not in list(NGAs.keys()):
            NGAs['BSSA'] = NGAs['BA']
        if 'ASK' not in list(NGAs.keys()):
            NGAs['ASK'] = NGAs['AS']

    dict1 = NGAs
    itmp = 0

    # check the input period
    # Note: this function is better used at a given period with a set of other parameters (not with a set of periods)
    if period > 10.0 or 0 < period < 0.01:
        raise ValueError('Positive period value should be within [0.01,10] for SA at corresponding periods')
    if period < 0 and period not in [-1,-2]:
        raise ValueError('negative period should be -1,-2 for PGA and PGV')

    if model_name == 'BSSA':
        ngaM = BSSA14.BSSA14_nga()
        kwds = {'Mech':Mech,'Ftype':Ftype,'Z10':Z10,'Dregion':Dregion,'country':country,'CoefTerms':dict1[model_name]}

    if model_name == 'CB':
        ngaM = CB14.CB14_nga()
        kwds = {'Ftype':Ftype,'Rrup':Rrup,'Ztor':Ztor,'dip':dip,'Z25':Z25,'W':W,'Zhypo':Zhypo,'azimuth':azimuth,'Fhw':Fhw,'Z10':Z10,'Z15':Z15,'Arb':ArbCB,'SJ':SJ,'region':region,'CoefTerms':dict1[model_name]}

    if model_name == 'CY':
        ngaM = CY14.CY14_nga()
        kwds = {'Ftype':Ftype,'Rrup':Rrup,'Rx':Rx,'Ztor':Ztor,'dip':dip,'W':W,'Zhypo':Zhypo,'azimuth':azimuth,'Fhw':Fhw,'Z10':Z10,'AS':Fas,'VsFlag':VsFlag,'country':country,'D_DPP':D_DPP,'CoefTerms':dict1[model_name]}
        # the new CY model treat PGA = SA(0.01)
        if period == -1:
            period = 0.01

    if model_name == 'ASK':
        ngaM = ASK14.ASK14_nga()
        kwds = {'Ftype':Ftype,'Rrup':Rrup,'Rx':Rx,'Ztor':Ztor,'dip':dip,'W':W,'Zhypo':Zhypo,'azimuth':azimuth,'Fhw':Fhw,'Z10':Z10,'Fas':Fas,'CRjb':CRjb,'Ry0':Ry0,'region':region,'country':country,'VsFlag':VsFlag, 'CoefTerms':dict1[model_name]}

    # common interpolate for all models
    periods = np.array(ngaM.periods)
    for ip in range( len(periods) ):
        if abs( period-periods[ip] ) < 0.0001:
            # period is within the periods list
            itmp = 1
            break

    if itmp == 1:
        # compute median, std directly for the existing period in the period list of the NGA model
        values = utils.mapfunc( ngaM, Mw, Rjb, Vs30, period, rake, **kwds )
        values = np.array( values )

    if itmp == 0:
        #print 'do the interpolation for periods that is not in the period list of the NGA model'
        ind_low = (periods <= period*1.0).nonzero()[0]
        ind_high = (periods >= period*1.0).nonzero()[0]

        period_low = max( periods[ind_low] )
        period_high = min( periods[ind_high] )
        values_low = np.array( utils.mapfunc( ngaM, Mw, Rjb, Vs30, period_low, rake, **kwds ) )
        values_high = np.array( utils.mapfunc( ngaM, Mw, Rjb, Vs30, period_high, rake, **kwds ) )
        N1,N2 = np.array(values_low).shape
        values = np.zeros( (N1,N2) )
        for icmp in range( N2 ):
            if icmp != 0:
                # stardand values are in ln (g)
                values[:,icmp] = utils.logline( np.log(period_low), np.log(period_high), values_low[:,icmp], values_high[:,icmp], np.log(period) )
            else:
                # median value is in g
                values[:,icmp] = utils.logline( np.log(period_low), np.log(period_high), np.log(values_low[:,icmp]), np.log(values_high[:,icmp]), np.log(period) )
                values[:,icmp] = np.exp( values[:,icmp] )    # change the median into g unit (logline gives the result in ln(g))

    # outputs
    NGAsigmaT = values[:,1]
    NGAtau = values[:,2]
    NGAsigma = values[:,3]

    if epislon:
        NGAmedian = np.exp( np.log(values[:,0]) + epislon * NGAsigmaT )
    else:
        NGAmedian = values[:,0]

    # returned quantities are all in g, not in log(g), event for the standard deviations
    return NGAmedian[0], \
           np.exp(NGAsigmaT)[0], \
           np.exp(NGAtau)[0], \
           np.exp(NGAsigma)[0]      # all in g, include the standard deviation

#%%----------------------------------------------------------------------------
def GMPE_array(model_name, Mw, Rjb, Vs30, period_array, epislon=0, NGAs=None,
         rake=None, Mech=3, Ftype=None, Fnm=None, Frv=None,
         dip=None, W=None, Ztor=None, Zhypo=None, Fas=0,
         Rrup=None, Rx=None, Fhw=None, azimuth=None,
         VsFlag=0, Z25=None, Z15=None, Z10=None,
         ArbCB=0, SJ=0,
         country='California', region='CA',
         Dregion='GlobalCATW',
         CRjb=15, Ry0=None,
         D_DPP=0):

    import collections
    if not isinstance(period_array, collections.Iterable):
        raise TypeError('`period_array` must be a array-like object.')

    TsDict14 = {
        'BSSA': [0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25,
              0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0],
        'CB': [0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25,
              0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0],
        'CY': [0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.10, 0.12, 0.15, 0.17, 0.20, 0.25,
              0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0],
        'ASK': [0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25,
              0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0],
        }

    results = []
    for period in period_array:
        if period < 0:
            raise ValueError('Period value must be positive')
        if period in TsDict14[model_name]:
            result_ = GMPE(model_name, Mw, Rjb, Vs30, period, epislon=epislon,
                           NGAs=NGAs, rake=rake, Mech=Mech, Ftype=Ftype, Fnm=Fnm,
                           Frv=Frv, dip=dip, W=W, Ztor=Ztor, Zhypo=Zhypo, Fas=Fas,
                           Rrup=Rrup, Rx=Rx, Fhw=Fhw, azimuth=azimuth,
                           VsFlag=VsFlag, Z25=Z25, Z15=Z15, Z10=Z10,
                           ArbCB=ArbCB, SJ=SJ,country=country, region=region,
                           Dregion=Dregion, CRjb=CRjb, Ry0=Ry0, D_DPP=D_DPP)
        else:  # needs interpolation
            low_i, high_i, T_low, T_high = _find_T_indices(TsDict14[model_name], period)
            result1 = GMPE(model_name, Mw, Rjb, Vs30, T_low, epislon=epislon,
                           NGAs=NGAs, rake=rake, Mech=Mech, Ftype=Ftype, Fnm=Fnm,
                           Frv=Frv, dip=dip, W=W, Ztor=Ztor, Zhypo=Zhypo, Fas=Fas,
                           Rrup=Rrup, Rx=Rx, Fhw=Fhw, azimuth=azimuth,
                           VsFlag=VsFlag, Z25=Z25, Z15=Z15, Z10=Z10,
                           ArbCB=ArbCB, SJ=SJ,country=country, region=region,
                           Dregion=Dregion, CRjb=CRjb, Ry0=Ry0, D_DPP=D_DPP)

            result2 = GMPE(model_name, Mw, Rjb, Vs30, T_high, epislon=epislon,
                           NGAs=NGAs, rake=rake, Mech=Mech, Ftype=Ftype, Fnm=Fnm,
                           Frv=Frv, dip=dip, W=W, Ztor=Ztor, Zhypo=Zhypo, Fas=Fas,
                           Rrup=Rrup, Rx=Rx, Fhw=Fhw, azimuth=azimuth,
                           VsFlag=VsFlag, Z25=Z25, Z15=Z15, Z10=Z10,
                           ArbCB=ArbCB, SJ=SJ,country=country, region=region,
                           Dregion=Dregion, CRjb=CRjb, Ry0=Ry0, D_DPP=D_DPP)

            result_ = [None] * len(result1)
            for j in range(len(result_)):
                result_[j] = np.interp(period, [T_low, T_high],
                                       [result1[j], result2[j]])

        results.append(result_)

    results_T = list(zip(*results))

    return tuple([np.array(_) for _ in results_T])

#%%----------------------------------------------------------------------------
def _find_T_indices(T_array, T_val, T_min=0.01, T_max=10):
    '''
    Find the low and high indices surrounding the T_val provided from T_array.
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

    return low_index, high_index, T_low, T_high



















