# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 17:13:08 2019

@author: Jeff Disbrow
"""


import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd


xs_p = r'C:\Users\Jeff Disbrow\Documents\UMN-Drive\Fall19\ESCI8701\gis\minn_crosssections.gpkg'
sample_pts = 175
sample_cols = ['X{:03d}'.format(n) for n in range(175)]
ten_m_cols = ['X{:03d}'.format(n) for n in range(78,98)]
five_m_cols = ['X{:03d}'.format(n) for n in range(82,93)]

xs = gpd.read_file(xs_p)


plt.style.use('ggplot')
fig, axes = plt.subplots(8,2)
axes = axes.flatten()

titles = ['', 'Above Falls', '', 'Just Below Falls', '', 'Moving Downstream-1', '', 'Moving Downstream-2', '',
          'Moving Downstream-3', '', 'Moving Downstream-4', '', 'Transition Zone', '', 'Near Confluence']

## Iterate rows of sample points and plot on new subplot
ctr = (len(xs)*2)-1
title_ctr = len(titles)-1
for i, row in xs.iterrows():
    ## Subset rows
    xs_pts = row[sample_cols]
    ten_m_pts = row[ten_m_cols]
    five_m_pts = row[five_m_cols]
    
    ## Plot
    ax = axes[ctr]
    ctr -= 1
#    print(ctr)
    ax.plot(ten_m_pts, color='g')
    ax.plot(five_m_pts, color='b')
    ylow, yhigh = ax.get_ylim()
    ax.set_ylim(ylow, ylow+8)
    
    labels = [item.get_text() for item in ax.get_xticklabels()]
    labels = [x.replace('X','') for x in labels]
    ax.set_xticklabels(labels)
    
    ax = axes[ctr]
    ctr -= 1
#    print(ctr)
    ax.plot(xs_pts)
    ax.plot(ten_m_pts, color='g')
    ax.plot(five_m_pts, color='b')
    ax.set_title(titles[title_ctr], fontsize=9)
    print(title_ctr, ctr)
    print(titles[title_ctr])
    title_ctr -= 2
    print(title_ctr)

    xlow, xhigh = ax.get_xlim()
    ax.xaxis.set_ticks(np.arange(xlow, xhigh, 25))
        
    labels = [item.get_text() for item in ax.get_xticklabels()]
    labels = [x.replace('X','') for x in labels]
    ax.set_xticklabels(labels)


    
plt.tight_layout()