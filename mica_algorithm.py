import json
import pandas as pd
import numpy as np

with open('./expert_rules.json') as f:
    rf=json.load(f)
with open('./colors_rules.json') as f:
    colors_dic=json.load(f)
splib=pd.read_json('./splib.json')
splib['wave'] = splib['wave'].apply(lambda x:np.array(x))
splib['rel'] = splib['rel'].apply(lambda x:np.array(x))

class InvalidRangeError(BaseException):
    def __init__(self):
        pass
    def __str__(self):
        return "the spectrum range of this feature contains no channels"

class InvalidLeftEndPointError(BaseException):
    def __init__(self):
        pass
    def __str__(self):
        return "this left end point range covers no channels"

class InvalidRightEndPointError(BaseException):
    def __init__(self):
        pass
    def __str__(self):
        return "this right end point range covers no channels"

def get_quadratic_center(spectrum, wl, CONTINUUM_ENDPTS, mask_const):
    mask = (wl <= CONTINUUM_ENDPTS[3]) & (wl >= CONTINUUM_ENDPTS[0])
    mask_left_end = (wl <= CONTINUUM_ENDPTS[1]) & (wl >= CONTINUUM_ENDPTS[0])
    mask_right_end = (wl <= CONTINUUM_ENDPTS[3]) & (wl >= CONTINUUM_ENDPTS[2])
    x_av = np.array([wl[mask_left_end].mean(), wl[mask_right_end].mean()], dtype='float64')
    y_av = np.array([spectrum[mask_const][:, mask_left_end].mean(1), spectrum[mask_const][:, mask_right_end].mean(1)], dtype='float64').T
    con = y_av[:, [0]]+(y_av[:, [1]]-y_av[:, [0]])/(x_av[1]-x_av[0])*(wl[mask].reshape([1,-1])-x_av[0])
    con = spectrum[mask_const][:, mask]/con
    index = con.argmin(1)
    mas=((index-1)>=0)&(index+1<mask.sum())
    con=con[mas]
    x2=wl[mask][index[mas]]
    x1=wl[mask][index[mas]-1]
    x3=wl[mask][index[mas]+1]
    r,c=con.shape
    y2=con.ravel()[index[mas]+c*np.arange(r)]
    y1=con.ravel()[index[mas]-1+c*np.arange(r)]
    y3=con.ravel()[index[mas]+1+c*np.arange(r)]
    temp=((y2-y1)*(x3**2-x2**2)-(y3-y2)*(x2**2-x1**2))/((y3-y2)*(x2-x1)-(y2-y1)*(x3-x2))/2
    cen=np.zeros(len(index))*np.nan
    cen[mas]=-1*temp
    center= np.zeros(len(spectrum))*np.nan
    center[mask_const] = cen
    return center
    
def diagnostic_feature(spectrum, reference, wl, CONTINUUM_ENDPTS, FEATURE_WEIGHT,
            CONTINUUM_CONSTRAINTS = [None]*8, FIT_CONSTRAINTS = None,
            DEPTH_CONSTRAINTS = [None,None]):
    # wl is a 1-d array containing p wavelengths
    # spectrum is an array of nxp, n is the number of pixels
    # reference is a 1-d array,containing p elements
    # CONTINUUM_ENDPTS is a list containing four elements, first two elements define the boundary of the left continuum point range,
    # and the last two define the right continuum point range
    # FEATURE_WEIGHT is a scalar,
    # CONTINUUM_CONSTRAINTS is 8-elements list
    # FIT_CONSTRAINTS is a scalar
    # DEPTH_CONSTRAINTS is a 2-elements list, defining the range of absorption depth
    mask = (wl <= CONTINUUM_ENDPTS[3]) & (wl >= CONTINUUM_ENDPTS[0])
    if not mask.any():
        raise InvalidRangeError()
    mask_left_end = (wl <= CONTINUUM_ENDPTS[1]) & (wl >= CONTINUUM_ENDPTS[0])
    if not mask_left_end.any():
        raise InvalidLeftEndPointError()
    mask_right_end = (wl <= CONTINUUM_ENDPTS[3]) & (wl >= CONTINUUM_ENDPTS[2])
    if not mask_right_end.any():
        raise InvalidRightEndPointError()
    x_av = np.array([wl[mask_left_end].mean(), wl[mask_right_end].mean()], dtype='float64')
    y_av = np.array([spectrum[:, mask_left_end].mean(1), spectrum[:, mask_right_end].mean(1)], dtype='float64').T
    r_l=reference[mask_left_end]
    r_r=reference[mask_right_end]
    y_r_av = np.array([r_l[~np.isnan(r_l)].mean(), r_r[~np.isnan(r_r)].mean()], dtype='float64')
    mask_const = np.ones(len(spectrum), dtype='bool')
    if CONTINUUM_CONSTRAINTS[0] is not None:
        mask_const = mask_const & (y_av[:, 0] >= CONTINUUM_CONSTRAINTS[0])
    if CONTINUUM_CONSTRAINTS[1] is not None:
        mask_const = mask_const & (y_av[:, 0] <= CONTINUUM_CONSTRAINTS[1])
    if CONTINUUM_CONSTRAINTS[2] is not None:
        mask_const = mask_const & ((y_av.mean(1)) >= CONTINUUM_CONSTRAINTS[2])
    if CONTINUUM_CONSTRAINTS[3] is not None:
        mask_const = mask_const & ((y_av.mean(1)) <= CONTINUUM_CONSTRAINTS[3])
    if CONTINUUM_CONSTRAINTS[4] is not None:
        mask_const = mask_const & (y_av[:,1] >= CONTINUUM_CONSTRAINTS[4])
    if CONTINUUM_CONSTRAINTS[5] is not None:
        mask_const = mask_const & (y_av[:,1] <= CONTINUUM_CONSTRAINTS[5])
    if CONTINUUM_CONSTRAINTS[6] is not None:
        mask_const = mask_const & ((y_av[:, 1]/y_av[:, 0]) >= CONTINUUM_CONSTRAINTS[6])
    if CONTINUUM_CONSTRAINTS[7] is not None:
        mask_const = mask_const & ((y_av[:, 1]/y_av[:, 0]) <= CONTINUUM_CONSTRAINTS[7])
    con = y_av[mask_const][:, [0]]+(y_av[mask_const][:, [1]]-y_av[mask_const][:, [0]])/(x_av[1]-x_av[0])*(wl[mask].reshape([1,-1])-x_av[0])
    con = spectrum[mask_const][:, mask]/con
    con_ = y_r_av[0]+(y_r_av[1]-y_r_av[0])/(x_av[1]-x_av[0])*(wl[mask]-x_av[0])
    con_ = reference[mask]/con_
    A = np.array([con_, np.ones(len(con_))],dtype='float64').T
    k = np.linalg.inv(A.T.dot(A)).dot(A.T).dot(con.T)
    mask_fit = k[0] > 0   # check signs of depths
    y_fit = k[0][mask_fit].reshape([-1, 1])*(con_.reshape([1,-1]))+k[1][mask_fit].reshape([-1, 1])
    ss_reg = ((y_fit-con[mask_fit].mean(1).reshape([-1, 1]))**2).sum(1)
    ss_tot = ((con[mask_fit]-con[mask_fit].mean(1).reshape([-1, 1]))**2).sum(1)
    r2 = np.zeros(len(con))*np.nan
    r2[mask_fit] = ss_reg/ss_tot
    depth = np.zeros(len(con))*np.nan
    if con_.mean()<1:
        depth[mask_fit] = (1-con_.min())*k[0][mask_fit]
    else:
        depth[mask_fit] = (con_.max()-1)*k[0][mask_fit]
    mask_c = np.ones(len(con),dtype='bool')
    if FIT_CONSTRAINTS is not None:
        mask_c=mask_c &(r2 >= FIT_CONSTRAINTS)
    if DEPTH_CONSTRAINTS[0] is not None:
        mask_c=mask_c & (depth >= DEPTH_CONSTRAINTS[0])
    if DEPTH_CONSTRAINTS[1] is not None:
        mask_c=mask_c&(depth <= DEPTH_CONSTRAINTS[1])   
    r2[~mask_c] = np.nan
    depth[~mask_c] = np.nan
    r2_ = np.zeros(len(spectrum))*np.nan
    r2_[mask_const] = r2
    depth_ = np.zeros(len(spectrum))*np.nan
    depth_[mask_const] = depth
    return r2_*FEATURE_WEIGHT,depth_*FEATURE_WEIGHT,r2_*FEATURE_WEIGHT*depth_

def get_fit(spectrum, reference, wl, CONTINUUM_ENDPTS):
    mask = (wl <= CONTINUUM_ENDPTS[3]) & (wl >= CONTINUUM_ENDPTS[0])
    if not mask.any():
        raise InvalidRangeError()
    mask_left_end = (wl <= CONTINUUM_ENDPTS[1]) & (wl >= CONTINUUM_ENDPTS[0])
    if not mask_left_end.any():
        raise InvalidLeftEndPointError()
    mask_right_end = (wl <= CONTINUUM_ENDPTS[3]) & (wl >= CONTINUUM_ENDPTS[2])
    if not mask_right_end.any():
        raise InvalidRightEndPointError()
    x_av = np.array([wl[mask_left_end].mean(),wl[mask_right_end].mean()],dtype='float64')
    y_av = np.array([spectrum[:,mask_left_end].mean(1),spectrum[:,mask_right_end].mean(1)],dtype='float64').T
    r_l=reference[mask_left_end]
    r_r=reference[mask_right_end]
    y_r_av = np.array([r_l[~np.isnan(r_l)].mean(), r_r[~np.isnan(r_r)].mean()], dtype='float64')
    con = y_av[:,[0]]+(y_av[:,[1]]-y_av[:,[0]])/(x_av[1]-x_av[0])*(wl[mask].reshape([1,-1])-x_av[0])
    con = spectrum[:,mask]/con
    con_ = y_r_av[0]+(y_r_av[1]-y_r_av[0])/(x_av[1]-x_av[0])*(wl[mask]-x_av[0])
    con_ = reference[mask]/con_
    A = np.array([con_,np.ones(len(con_))],dtype='float64').T
    k = np.linalg.inv(A.T.dot(A)).dot(A.T).dot(con.T)
    mask_fit = k[0]>0 # check signs of depths
    y_fit = k[0][mask_fit].reshape([-1,1])*(con_.reshape([1,-1]))+k[1][mask_fit].reshape([-1,1])
    ss_reg = ((y_fit-con[mask_fit].mean(1).reshape([-1,1]))**2).sum(1)
    ss_tot=((con[mask_fit]-con[mask_fit].mean(1).reshape([-1,1]))**2).sum(1)
    r2=np.zeros(len(con))*np.nan
    r2[mask_fit]=ss_reg/ss_tot
    depth=np.zeros(len(con))*np.nan
    if con_.mean()<1:
        #depth[mask_fit]=(1-con_.min())*k[0][mask_fit]
        depth[mask_fit]=1-(con_.min()*k[0]+k[1])[mask_fit]
    else:
        #depth[mask_fit]=(con_.max()-1)*k[0][mask_fit]
        depth[mask_fit]=(con_.max()*k[0]+k[1])[mask_fit]-1
    return r2, depth

def not_absolute_feature(spectrum, reference, wl, CONTINUUM_ENDPTS, NOT_FEATURE_FIT_CONSTRAINTS,
            NOT_FEATURE_ABSOLUTE_DEPTH_CONSTRAINTS):
    r2, depth = get_fit(spectrum, reference, wl, CONTINUUM_ENDPTS)
    mask_c= (r2>=NOT_FEATURE_FIT_CONSTRAINTS)
    mask_c=mask_c & (depth>=NOT_FEATURE_ABSOLUTE_DEPTH_CONSTRAINTS)
    return mask_c

def not_relative_feature(spectrum, reference, wl, CONTINUUM_ENDPTS, NOT_FEATURE_FIT_CONSTRAINTS,
            RELATIVE_FEATURE_DEPTH, NOT_FEATURE_RELATIVE_DEPTH_CONSTRAINTS):
    r2, depth = get_fit(spectrum, reference, wl, CONTINUUM_ENDPTS)
    mask_c= (r2>=NOT_FEATURE_FIT_CONSTRAINTS)
    mask_c=mask_c & (depth>=(RELATIVE_FEATURE_DEPTH*NOT_FEATURE_RELATIVE_DEPTH_CONSTRAINTS))
    return mask_c

def judge_reference_entry(spectrum, wl, key, resampled1, chanels):
    reference = resampled1[key][chanels]
    fit = np.zeros(len(spectrum))
    depth = np.zeros(len(spectrum))
    fd = np.zeros(len(spectrum))
    i=rf[key]['diagnostic'][0]
    FEATURE_WEIGHT=i[0]
    CONTINUUM_ENDPTS=i[1]
    CONTINUUM_CONSTRAINTS=[j if j!=-99.99 else None for j in i[2]]
    FIT_CONSTRAINTS=(lambda x:x if x!=-99.99 else None)(i[3])
    DEPTH_CONSTRAINTS=[j if j!=-99.99 else None for j in i[4]]
    r1,d1,fd1=diagnostic_feature(spectrum,reference,wl,CONTINUUM_ENDPTS,FEATURE_WEIGHT,
        CONTINUUM_CONSTRAINTS,FIT_CONSTRAINTS,
        DEPTH_CONSTRAINTS)
    fit=fit+r1
    depth=depth+d1
    fd=fd+fd1
    for i in rf[key]['diagnostic'][1:]:
        FEATURE_WEIGHT=i[0]
        CONTINUUM_ENDPTS=i[1]
        CONTINUUM_CONSTRAINTS=[j if j!=-99.99 else None for j in i[2]]
        FIT_CONSTRAINTS=(lambda x:x if x!=-99.99 else None)(i[3])
        DEPTH_CONSTRAINTS=[j if j!=-99.99 else None for j in i[4]]
        r,d,fdd=diagnostic_feature(spectrum,reference,wl,CONTINUUM_ENDPTS,FEATURE_WEIGHT,
            CONTINUUM_CONSTRAINTS,FIT_CONSTRAINTS,
            DEPTH_CONSTRAINTS)
        fit=fit+r
        depth=depth+d
        fd=fd+fdd
    for i in rf[key]['not_abs']:
        reference = resampled1[i[0]][chanels]
        CONTINUUM_ENDPTS = i[1]
        NOT_FEATURE_FIT_CONSTRAINTS=i[2]
        NOT_FEATURE_ABSOLUTE_DEPTH_CONSTRAINTS=i[3]
        mask_c=not_absolute_feature(spectrum, reference, wl, CONTINUUM_ENDPTS, NOT_FEATURE_FIT_CONSTRAINTS,
            NOT_FEATURE_ABSOLUTE_DEPTH_CONSTRAINTS)
        fit[mask_c]=np.nan
        depth[mask_c]=np.nan
        fd[mask_c]=np.nan
    for i in rf[key]['not_rel']:
        reference = resampled1[i[0]][chanels]
        CONTINUUM_ENDPTS=i[1]
        NOT_FEATURE_FIT_CONSTRAINTS=i[2]
        RELATIVE_FEATURE_DEPTH=d1
        NOT_FEATURE_RELATIVE_DEPTH_CONSTRAINTS=i[4]
        mask_c=not_relative_feature(spectrum, reference, wl, CONTINUUM_ENDPTS, NOT_FEATURE_FIT_CONSTRAINTS,
                         RELATIVE_FEATURE_DEPTH, NOT_FEATURE_RELATIVE_DEPTH_CONSTRAINTS)
        fit[mask_c]=np.nan
        depth[mask_c]=np.nan
        fd[mask_c]=np.nan
    minimum_weighted_fit,minimum_weighted_depth,maximum_weighted_depth,minimum_fit_depth=[i if i !=-99.99 else None for i in rf[key]['WEIGHTED_FIT_DEPTH_CONSTRAINTS']]
    mask_c = np.ones(len(spectrum), dtype='bool')
    if minimum_weighted_fit is not None:
        mask_c = fit >= minimum_weighted_fit
    if minimum_weighted_depth is not None:
        mask_c= mask_c&(depth>=minimum_weighted_depth)
    if maximum_weighted_depth is not None:
        mask_c=mask_c&(depth<=maximum_weighted_depth)
    if minimum_fit_depth is not None:
        mask_c=mask_c&(fd>minimum_fit_depth)
    fit[~mask_c]=np.nan
    depth[~mask_c]=np.nan
    fd[~mask_c]=np.nan
    return fit, fd
