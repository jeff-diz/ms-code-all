# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 11:53:49 2019

@author: disbr007
"""

import geopandas as gpd
import logging
import matplotlib.pyplot as plt
import itertools
import numpy as np
from scipy import interpolate

from tqdm import tqdm


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


logger.info('Loading points...')
pts_p = r'V:\pgc\data\scratch\jeff\coreg\data\icesat_reg\WV02_20120522-WV02_20170413\WV02_20120522-WV02_20170413.shp'
pts = gpd.read_file(pts_p, driver='ESRI Shapefile')

logger.info('Randomly sampling pts...')
s = pts.sample(n=1000)

## Get bounds of points
minx, miny, maxx, maxy = s.total_bounds
## Get points
coords = np.array(list(zip(s.geometry.x, s.geometry.y)))
values = s['abs_diff'].values


## Create empty grid to interpolate over
# Assumes crs in meters, 2 meter grid in x and y from min to max
# nj term is number of steps, so (max-min / 2m)
step = 2
grid_x = np.arange(minx, maxx, step)
grid_y = np.arange(miny, maxy, step)

gx, gy = np.meshgrid(grid_x, grid_y, sparse=True)

interp = interpolate.griddata(coords, values, (gx, gy))

fig, ax = plt.subplots(1,1)
ax.plot(grid_x)
#ax.scatter(grid_x, grid_y)