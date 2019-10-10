# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 14:01:15 2019

@author: disbr007
"""

import operator

import glob
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import os
import pandas as pd

from scipy.interpolate import interpn
from scipy import stats
from scipy.stats import gaussian_kde
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import PolynomialFeatures


def density_scatter( x , y, ax = None, sort = True, bins = 20, **kwargs )   :
    """
    Scatter plot colored by 2d histogram
    """
    if ax is None :
        fig , ax = plt.subplots()
    data , x_e, y_e = np.histogram2d( x, y, bins = bins)
    z = interpn( ( 0.5*(x_e[1:] + x_e[:-1]) , 0.5*(y_e[1:]+y_e[:-1]) ) , data , np.vstack([x,y]).T , method = "splinef2d", bounds_error = False )

    # Sort the points by density, so that the densest points are plotted last
    if sort :
        idx = z.argsort()
        x, y, z = x[idx], y[idx], z[idx]

    ax.scatter( x, y, c=z, **kwargs )
    return ax


## Paths
pairs_p = r'V:\pgc\data\scratch\jeff\coreg\data\pairs'
# Iteration info
#it_info_p = r'V:\pgc\data\scratch\jeff\coreg\data\scratch\test_2019sep24_0836\pca-iterationInfo.csv'
#it_info_p = r'V:\pgc\data\scratch\jeff\coreg\data\scratch\test_2019sep24_1500\WV02_20130610-iterationInfo.csv'

## Columns in iteration info files
iteration_cols =['Iteration',
                 ' Max iteration',
                 ' Mean abs differential rot err',
                 ' Min differential rotation err',
                 ' Mean abs differential trans err',
                 ' Min differential translation err',
                 'fname']

## Create empty df
it_info_master = pd.DataFrame(columns=iteration_cols)


## Iterate all iterationInfo files
matches = glob.glob(os.path.join(pairs_p, '*', '*-iterationInfo.csv'))
for csv in matches:
    fname = os.path.basename(csv).split('.')[0].split('-iterationInfo')[0]
#    print(fname)
    results = pd.read_csv(csv)
#    print(len(it_info))
    results['fname'] = fname
    it_info_master = it_info_master.append(results)

## Convert types
int_cols = ['Iteration', ' Max iteration']
conv_float = {col: float for col in iteration_cols if col != 'fname' and col not in int_cols}
conv_int = {col2: 'int64' for col2 in int_cols}
it_info_master = it_info_master.astype(conv_float)
it_info_master = it_info_master.astype(conv_int)


## Rename columns
# Col names
iter_col = 'Iteration'
max_it = 'max_it'
mean_rot = 'mean_rot_err'
min_rot = 'min_rot_err'
mean_trans = 'mean_trans_err'
min_trans = 'min_trans_err'
std1 = 'std1'
std2 = 'std2'


ren = {' Max iteration': max_it,
       ' Mean abs differential rot err': mean_rot,
       ' Min differential rotation err': min_rot,
       ' Mean abs differential trans err': mean_trans,
       ' Min differential translation err': min_trans}

it_info_master.rename(columns=ren, inplace=True)

## Aggregate error by iteration
agg = {
       mean_trans: ['mean', np.std], 
       mean_rot: ['mean', np.std]
       }

agg = it_info_master.groupby('Iteration').agg(agg)

## Add standard deviation columns
agg['trans_std+1'] = agg[(mean_trans, 'mean')] + agg[mean_trans, 'std'] 
agg['trans_std-1'] = agg[(mean_trans, 'mean')] - agg[mean_trans, 'std'] 
agg['trans_std+2'] = agg[(mean_trans, 'mean')] + 2*agg[mean_trans, 'std'] 
agg['trans_std-2'] = agg[(mean_trans, 'mean')] - 2*agg[mean_trans, 'std'] 



#### Plotting
## Plotting Setup
plt.style.use('ggplot')
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
pt_size = 7
linewidth = 2


it_info_dict = {
        1: {'title': 'Translational Error', 'col': ' Mean abs differential trans err', 'ax':ax2},
        2: {'title': 'Rotational Error', 'col': ' Mean abs differential rot err', 'ax':ax1},
        }

#it_info_master.plot.scatter(x='Iteration', y=col1, ax=ax1)
#it_info_master.plot.scatter(x='Iteration', y=col2, ax=ax2)

ax1.scatter(it_info_master[iter_col], it_info_master[mean_rot], s=pt_size)
ax2.scatter(it_info_master[iter_col], it_info_master[mean_trans], s=pt_size)
# Plot line of means of errors
ax1.plot(agg[3:].index, agg[3:][(mean_rot, 'mean')], lw=linewidth, c='b')
ax2.plot(agg[3:].index, agg[3:][(mean_trans, 'mean')], lw=linewidth, c='b')

ax2.plot(agg[3:].index, agg[3:][('trans_std+2', '')], lw=linewidth, c='b', alpha=0.75, ls=':')
ax2.plot(agg[3:].index, agg[3:][('trans_std-2', '')], lw=linewidth, c='b', alpha=0.75, ls=':')

col1_min = it_info_master[mean_rot].min()
col1_max = it_info_master[mean_rot].max()
col1_10p = (col1_max - col1_min)*0.1

col2_min = it_info_master[mean_trans].min()
col2_max = it_info_master[mean_trans].max()
col2_10p = (col2_max - col2_min)*0.1

ax1.set_ylim(col1_min-col1_10p, col1_max+col1_10p)
ax2.set_ylim(col2_min-col2_10p, col2_max+col2_10p)


### Fit line
#for num, subdict in it_info_dict.items():
#    title = subdict['title']
#    col = subdict['col']
#    ax = subdict['ax']
#    
#    x = it_info_master['Iteration'][3:].values
#    y = it_info_master[col][3:].values
#    
#    x = x[:, np.newaxis]
#    y = y[:, np.newaxis]
#    
#    polynomial_features = PolynomialFeatures(degree=4)
#    x_poly = polynomial_features.fit_transform(x)
#    
#    model = LinearRegression()
#    model.fit(x_poly, y)
#    y_poly_pred = model.predict(x_poly)
#    
#    rmse = np.sqrt(mean_squared_error(y, y_poly_pred))
#    r2 = r2_score(y, y_poly_pred)
##    print(rmse)
##    print(r2)
#    
##    ax.scatter(x,y, s=10)
#    sort_axis = operator.itemgetter(0)
#    sorted_zip = sorted(zip(x,y_poly_pred), key=sort_axis)
#    
#    x, y_poly_pred = zip(*sorted_zip)
##    ax.plot(x, y_poly_pred, color='r', lw=1)
#    
#    ax.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
#    ax.set_title(title)
##    ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))
plt.tight_layout()
