import logging
import numpy as np
import os
from osgeo import gdal, osr
import random

from RasterWrapper import Raster


def raster_bounds(raster_obj):
    '''
    GDAL only version of getting bounds for a single raster.
    '''
#    src = raster_obj.data_src
    gt = raster_obj.geotransform
    ulx = gt[0]
    uly = gt[3]
    lrx = ulx + (gt[1] * raster_obj.x_sz)
    lry = uly + (gt[5] * raster_obj.y_sz)
    
    return ulx, lry, lrx, uly

    
def minimum_bounding_box(raster_objs):
    '''
    Takes a list of DEMs (or rasters) and returns the minimum bounding box of all in
    the order of bounds specified for gdal.Translate.
    dems: list of dems
    '''
    ## Determine minimum bounding box
    ulxs, lrys, lrxs, ulys = list(), list(), list(), list()
    #geoms = list()
    for r in raster_objs:
        ulx, lry, lrx, uly = raster_bounds(r)
        ulxs.append(ulx)
        lrys.append(lry)
        lrxs.append(lrx)
        ulys.append(uly)        
    
    ## Find the smallest extent of all bounding box corners
    ulx = max(ulxs)
    uly = min(ulys)
    lrx = min(lrxs)
    lry = max(lrys)

    projWin = [ulx, uly, lrx, lry]

    return projWin


def calc_rmse(l1, l2):
    '''
    Calculates RMSE of two lists of numbers.
    '''

    diffs = [x - y for x, y in zip(l1, l2)]
    sq_diff = [x**2 for x in diffs]
    mean_sq_diff = sum(sq_diff) / len(sq_diff)
    rmse_val = np.sqrt(mean_sq_diff)
    
    return rmse_val


def sample_random_points(dem1, dem2, n):
    """
    Generates n random points within projWin [ulx, uly, lrx, lry]
    """
    dem1_nodata = dem1.nodata_val
    dem2_nodata = dem2.nodata_val
    
    projWin = minimum_bounding_box([dem1, dem2])
    minx, miny, maxx, maxy = projWin
    
    sample_vals = []
    while len(sample_vals) < n:
        pt = (random.uniform(miny, maxy), random.uniform(minx, maxx))
        val1 = dem1.SamplePoint(pt)
        val2 = dem2.SamplePoint(pt)
        if val1 != dem1_nodata and val2 != dem2_nodata and val1 is not None and val2 is not None:
            sample_vals.append((val1, val2))
        else:
            pass
        
    return sample_vals
    
#dem1_p = r'V:\pgc\data\scratch\jeff\coreg\data\pc_align_reg\WV02_20150718-WV02_20150718\WV02_20150718_10300100464D6D00_1030010046298B00_seg4_2m_dem.tif'
#dem2_p = r'V:\pgc\data\scratch\jeff\coreg\data\pc_align_reg\WV02_20150718-WV02_20150718\WV02_20150718-DEM.tif'
def dem_RMSE(dem1_p, dem2_p, n):
    """
    Calculate RMSE for two DEMs from
    n sample points
    """
    logging.info('Loading DEMs...')
    dem1 = Raster(dem1_p)
    dem2 = Raster(dem2_p)
    logging.info('Sampling points...')
    sample_values = sample_random_points(dem1, dem2, n=n)
    x_vals, y_vals = zip(*sample_values)
    rmse = calc_rmse(x_vals, y_vals)
    print(rmse)
