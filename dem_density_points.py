# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 10:59:40 2019

@author: disbr007
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import os


from archive_analysis_utils import get_count, get_time_range


#### Load data
## Paths
prj_path = r'E:\disbr007\umn\ms_proj_2019jul05\data'
out_name = r'banks_dem_density.shp'
out_p = os.path.join(prj_path, 'scratch', out_name)
pts_p = os.path.join(prj_path, 'scratch', 'lewk_it.shp')
dems_p = os.path.join(prj_path, 'scratch', 'banks_sel_lewk_it.shp')
## Load
pts = gpd.read_file(pts_p)
dems = gpd.read_file(dems_p)

#### Get counts
density = get_count(pts, dems)
#density.to_file(out_p)

#### Get year range
out = get_time_range(density, dems, 'acqdate1')
out.to_file(out_p)


#### Plotting
countries_p = r'E:\disbr007\general\Countries_WGS84\Countries_WGS84.shp'
countries = gpd.read_file(countries_p)

plotting_crs = {'init':'epsg:3995'}
countries = countries.to_crs(plotting_crs)
out = out.to_crs(plotting_crs)

## Zoom to out layer
out_minx, out_miny, out_maxx, out_maxy = out.total_bounds
x_pad = (out_maxx - out_minx) / 10
y_pad = (out_maxy - out_miny) / 10

plt.style.use('ggplot')
cmap = 'YlOrRd'
markersize = 10
fig, (ax1, ax2) = plt.subplots(1, 2)

for ax in (ax1, ax2):
    countries.plot(color='grey', edgecolor='black', linewidth=1, alpha=0.5, ax=ax)
    ax.set_xlim(out_minx-x_pad, out_maxx+x_pad)
    ax.set_ylim(out_miny-y_pad, out_maxy+y_pad)
    
out.plot(column='count', 
         ax=ax1, 
         cmap=cmap,
         markersize=markersize,
         legend=True,
         legend_kwds={'orientation':'horizontal'})
ax1.set_title('Count')

out.plot(column='months_range', 
         ax=ax2, 
         cmap=cmap, 
         markersize=markersize,
         legend=True)
ax2.set_title('Months Range')
